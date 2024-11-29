import numpy as np
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
import torch
from alphazero.alpha_mcts.node import Node


class MCTSParallel:
    def __init__(self, env, model, device):
        self.env = env
        self.num_searches = 1
        self.device = device
        self.model = model
        self.dirchlet_epsilon = 0.25
        self.dirchlet_alpha = 0.3

    @torch.no_grad
    def search(self, states, sp_games):
        policy, _ = self.model(
            torch.tensor(self.env.chess_board.get_states(states), device=self.device, dtype=torch.float32).permute(0, 3,
                                                                                                                   1, 2)
        )
        policy = torch.softmax(policy, dim=1).cpu().numpy()
        policy = (1 - self.dirchlet_epsilon) * policy + self.dirchlet_epsilon \
                 * np.random.dirichlet([self.dirchlet_alpha] * self.env.action_space.action_size, size=policy.shape[0])

        for i, spg in enumerate(sp_games):
            spg_policy = policy[i]
            _, valid_moves = self.env.chess_board.generate_all_valid_moves(states[i])
            spg_policy *= valid_moves
            if np.sum(spg_policy) > 0:
                spg_policy /= np.sum(spg_policy)
            else:
                spg_policy = np.zeros_like(spg_policy)  # Prevents propagation of NaN

            spg.root = Node(self.env, states[i], visit_count=1)
            spg.root.expand(spg_policy)

        for search in range(self.num_searches):
            for spg in sp_games:
                spg.node = None
                node = spg.root

                while node.is_fully_expanded():
                    node = node.select()

                value, is_terminal = self.env.get_reward_and_terminated(node.state)
                value = -value

                if is_terminal:
                    node.backpropagate(value)

                else:
                    spg.node = node

            expandable_sp_games = [mapping_idx for mapping_idx in range(len(sp_games)) if
                                   sp_games[mapping_idx].node is not None]

            if len(expandable_sp_games) > 0:
                states = np.stack([sp_games[mapping_idx].node.state for mapping_idx in expandable_sp_games])

                policy, value = self.model(
                    torch.tensor(self.env.chess_board.get_states(states), device=self.device,
                                 dtype=torch.float32).permute(0, 3, 1, 2)
                )
                policy = torch.softmax(policy, dim=1).cpu().numpy()
                value = value.cpu().numpy()

            for i, mapping_idx in enumerate(expandable_sp_games):
                node = sp_games[mapping_idx].node
                spg_policy, spg_value = policy[i], value[i][0]

                _, valid_moves = self.env.chess_board.generate_all_valid_moves(states[i])
                spg_policy *= valid_moves
                if np.sum(spg_policy) > 0:
                    spg_policy /= np.sum(spg_policy)
                else:
                    spg_policy = np.zeros_like(spg_policy)  # Prevents propagation of NaN

                node.expand(spg_policy)
                node.backpropagate(spg_value)

    def decode_action(self, action):
        from_encoding, to_encoding = action // 64, action % 64
        from_pos, to_pos = (from_encoding // 8, from_encoding % 8), (to_encoding // 8, to_encoding % 8)
        return from_pos, to_pos
