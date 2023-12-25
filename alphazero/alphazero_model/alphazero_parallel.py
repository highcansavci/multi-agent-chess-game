import random
import numpy as np
import torch
import torch.nn.functional as F
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from alphazero.alpha_mcts.mcts import MCTSParallel


class AlphaZeroParallel:
    def __init__(self, model, optimizer, env, device):
        self.model = model
        self.optimizer = optimizer
        self.env = env
        self.device = device
        self.mcts = MCTSParallel(env, model, self.device)
        self.num_iterations = 10
        self.num_self_play_iterations = 500
        self.num_parallel_games = 100
        self.num_epochs = 10
        self.batch_size = 128 * 256
        self.temperature = 1.25

    def self_play(self):
        return_memory = []
        player = "white"
        sp_games = [SPG(self.env) for spg in range(self.num_parallel_games)]

        while len(sp_games) > 0:
            states = np.stack([spg.model for spg in sp_games])
            neutral_states = self.env.change_perspective(states, player)

            self.mcts.search(neutral_states, sp_games)

            for i in range(len(sp_games))[::-1]:
                print(f"{i}th game has started.")
                spg = sp_games[i]

                action_probs = np.zeros(self.env.action_space.action_size)
                for child in spg.root.children:
                    action_probs[child.action_taken] = child.visit_count
                action_probs /= np.sum(action_probs)

                spg.memory.append((spg.root.state, action_probs, player))

                temperature_action_probs = action_probs ** (1 / self.temperature)
                action = np.random.choice(self.env.action_space.action_size,
                                          p=temperature_action_probs)  # Divide temperature_action_probs with its sum in case of an error

                spg.model = self.env.simulate(spg.model, ((action // 64 // 8, action // 64 % 8), ((action % 64) // 8, (action % 64) % 8)))

                value, is_terminal = self.env.get_reward_and_terminated(spg.model)
                if is_terminal:
                    for hist_neutral_state, hist_action_probs, hist_player in spg.memory:
                        hist_outcome = value if hist_player == player else -value
                        return_memory.append((
                            self.env.chess_board.get_state_(hist_neutral_state),
                            hist_action_probs,
                            hist_outcome
                        ))
                    del sp_games[i]

            player = self.env.get_opponent(player)

        return return_memory

    def train(self, memory, epoch):
        random.shuffle(memory)
        for batch_idx in range(0, len(memory), self.batch_size):
            print(f"{epoch}th epoch and {batch_idx}th batch..")
            sample = memory[batch_idx:min(len(memory) - 1, batch_idx + self.batch_size)]  # Change to memory[batch_idx:batch_idx+self.args['batch_size']] in case of an error
            state, policy_targets, value_targets = zip(*sample)

            state, policy_targets, value_targets = np.array(state), np.array(policy_targets), np.array(
                value_targets).reshape(-1, 1)

            state = torch.tensor(state, dtype=torch.float32, device=self.device).permute(0, 3, 1, 2)
            policy_targets = torch.tensor(policy_targets, dtype=torch.float32, device=self.device)
            value_targets = torch.tensor(value_targets, dtype=torch.float32, device=self.device)

            out_policy, out_value = self.model(state)

            policy_loss = F.cross_entropy(out_policy, policy_targets)
            value_loss = F.mse_loss(out_value, value_targets)
            loss = policy_loss + value_loss

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def learn(self):
        for iteration in range(self.num_iterations):
            memory = []
            self.env.reset()

            self.model.eval()
            print(f"Self play is started....")
            for self_play_iteration in range(self.num_self_play_iterations // self.num_parallel_games):
                memory += self.self_play()
            print(f"Self play is finished. Training is started...")
            self.model.train()
            for epoch in range(self.num_epochs):
                self.train(memory, epoch)

            print(f"Iteration {iteration} is finished. Saving the model...")
            torch.save(self.model.state_dict(), f"model_{iteration}.pt")
            torch.save(self.optimizer.state_dict(), f"optimizer_{iteration}.pt")


class SPG:
    def __init__(self, env):
        self.model = env.chess_board
        self.memory = []
        self.root = None
        self.node = None