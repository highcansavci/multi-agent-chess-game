from collections import deque
import random
import numpy as np
import torch
import torch.nn.functional as F
import torch.multiprocessing as mp
import sys
import math
from typing import List, Tuple

from gym_wrapper.environment import ChessGym

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from alphazero.alpha_mcts.mcts import MCTSParallel

class AlphaZeroParallel:
    def __init__(self, model, optimizer, env, device, num_workers=4):
        self.model = model
        self.model.share_memory()  # Enable model sharing between processes
        self.optimizer = optimizer
        self.base_env = env  # Keep as template
        self.device = device
        self.num_workers = num_workers
        
        # Adjusted parameters for T440p
        self.num_iterations = 20            # Reduced from 100 to allow faster iteration cycles
        self.num_self_play_iterations = 300 # Reduced from 1500 to manage memory and CPU load
        self.num_parallel_games = 4         # Reduced from 20 based on CPU cores (2 cores, 4 threads)
        self.num_epochs = 50               # Reduced from 1000 to prevent overfitting and save time
        self.batch_size = 64               # Reduced from 128 to manage memory usage
        self.temperature = 1.0             # Changed to match AlphaZero paper
        self.dirichlet_alpha = 0.3         # Keep as is (AlphaZero paper value)
        self.exploration_fraction = 0.25    # Keep as is (good exploration/exploitation balance)
        self.replay_buffer_size = 100000   # Reduced from 1000000 to manage memory
        self.replay_buffer = deque(maxlen=self.replay_buffer_size)

        # Add learning parameters
        self.learning_rate = 0.001         # Lower learning rate for stability
        self.weight_decay = 1e-4           # L2 regularization
        
        # Use torch.multiprocessing instead of ProcessPoolExecutor
        mp.set_start_method('spawn', force=True)
        self.pool = mp.Pool(processes=self.num_workers)

    @staticmethod
    def play_game(model, base_env, params) -> List[Tuple]:
        """Static method for playing a single game"""
        env = ChessGym()
        env.copy_optimized(base_env)
        spg = SPG(env)
        game_memory = []
        mcts = MCTSParallel(env, model, params['device'])
        move_count = 0  # Track number of moves
        
        while True:
            state = np.array([spg.model])
            state = env.change_perspective(state)
            mcts.search(state, [spg])
            
            # Calculate action probabilities from visit counts
            action_probs = np.zeros(env.action_space.action_size)
            for child in spg.root.children:
                action_probs[child.action_taken] = child.visit_count
            if np.sum(action_probs) > 0:
                action_probs /= np.sum(action_probs)
            else:
                action_probs = np.ones_like(action_probs) / len(action_probs)  # Assign uniform probability
            
            # Only add Dirichlet noise in the early game (first 30 moves)
            if move_count < 30:
                dirichlet_noise = np.random.dirichlet([params['dirichlet_alpha']] * env.action_space.action_size)
                action_probs = (1 - params['exploration_fraction']) * action_probs + params['exploration_fraction'] * dirichlet_noise
                # Early game: temperature = 1.0 for exploration
                temperature = 1.0
            else:
                # Late game: minimal temperature for exploitation
                temperature = 0.01
            
            # Store state
            game_memory.append((spg.root.state, action_probs, "white" if spg.model.white_moves else "black"))
            
            # Select action based on temperature
            if temperature > 0.01:  # Early game - use temperature
                temperature_action_probs = action_probs ** (1 / temperature)
                temperature_action_probs /= np.sum(temperature_action_probs)
                action = np.random.choice(env.action_space.action_size, p=temperature_action_probs)
            else:  # Late game - select best move
                action = np.argmax(action_probs)
            
            # Make move
            from_pos = ((action // 64) // 8, (action // 64) % 8)
            to_pos = ((action % 64) // 8, (action % 64) % 8)
            value, is_terminal, _, result_action = env.step(spg.model, (from_pos, to_pos))
            
            move_count += 1
            
            if is_terminal:
                return AlphaZeroParallel.process_game_result(game_memory, value, env, result_action)

    @staticmethod
    def process_game_result(game_memory, value, env, result_action):
        """
        Process the result of a completed game for AlphaZero training
        """
        if result_action is None:
            return []
            
        game_result = value
        return_memory = []
        
        for hist_state, hist_action_probs, hist_player in game_memory:
            # Convert state to network input format
            processed_state = env.chess_board.get_state_(hist_state)

            # Calculate outcome from perspective of current player
            hist_outcome = game_result if hist_player == "white" else -game_result
            
            return_memory.append((
                processed_state,
                hist_action_probs,
                hist_outcome
            ))
        
        return return_memory

    def self_play(self):
        """Parallel self-play implementation using multiprocessing"""
        return_memory = []
        env = ChessGym()
        # Prepare parameters for workers
        params = {
            'device': self.device,
            'temperature': self.temperature,
            'dirichlet_alpha': self.dirichlet_alpha,
            'exploration_fraction': self.exploration_fraction
        }
        # Create args for parallel execution
        args = [(self.model, self.base_env, params) 
                for _ in range(self.num_parallel_games)]
        
        # Execute games in parallel
        results = self.pool.starmap(self.play_game, args)
        
        # Collect results
        for result in results:
            return_memory.extend(result)
            
        return return_memory

    def train_batch(self, batch_data):
        """Process a single training batch"""
        state, policy_targets, value_targets = zip(*batch_data)
        
        # Convert to tensors
        state = torch.tensor(np.array(state), dtype=torch.float32, device=self.device).permute(0, 3, 1, 2)
        policy_targets = torch.tensor(np.array(policy_targets), dtype=torch.float32, device=self.device)
        value_targets = torch.tensor(np.array(value_targets).reshape(-1, 1), dtype=torch.float32, device=self.device)
        
        # Forward pass
        out_policy, out_value = self.model(state)
        
        # Compute losses
        policy_loss = F.cross_entropy(out_policy, policy_targets)
        value_loss = F.mse_loss(out_value, value_targets)
        l2_reg = sum(p.pow(2.0).sum() for p in self.model.parameters())
        loss = policy_loss + 0.5 * value_loss + self.weight_decay * l2_reg
        
        return loss, state.shape[0]

    def train(self, memory, epoch):
        """Training implementation with batch processing"""
        if not memory:
            print(f"No data available for model in epoch {epoch}.")
            return
            
        print(f"Training model in epoch {epoch}.")
        
        # Process all data in batches
        memory_list = list(memory)
        random.shuffle(memory_list)
        total_loss = 0
        total_samples = 0
        
        for i in range(0, len(memory_list), self.batch_size):
            batch = memory_list[i:i + self.batch_size]
            loss, batch_size = self.train_batch(batch)
            
            # Backward pass and optimization
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item() * batch_size
            total_samples += batch_size
            
            if i % (self.batch_size * 10) == 0:
                print(f"Batch {i//self.batch_size} average loss: {total_loss/total_samples:.4f}")

    def learn(self):
        """Main learning loop"""
        try:
            for iteration in range(self.num_iterations):
                self.model.eval()
                self.replay_buffer.clear()
                print(f"Iteration {iteration}: Self-play is starting...")
                # Parallel self-play
                for iteration_ in range(self.num_self_play_iterations // self.num_parallel_games):
                    print(f"Parallel self-play iteration {iteration_} is started.")
                    self.base_env.reset_optimized()
                    self.replay_buffer.extend(self.self_play()) 
                print(f"Self-play is finished. Training is starting...")
                
                # Training
                self.model.train()
                for epoch in range(self.num_epochs):
                    self.train(self.replay_buffer, epoch)
                
                # Save checkpoints
                print(f"Iteration {iteration} is finished. Saving the models and optimizers...")
                torch.save(self.model.state_dict(), f"model_{iteration}.pt")
                torch.save(self.optimizer.state_dict(), f"optimizer_{iteration}.pt")
            
            print("Training process is complete.")
            
        finally:
            self.pool.close()
            self.pool.join()

    def inference(self, mcts) -> List[Tuple]:
        spg = SPG(self.base_env)
        move_count = 0  # Track number of moves
        
        state = np.array([spg.model])
        mcts.search(state, [spg])
            
        # Calculate action probabilities from visit counts
        action_probs = np.zeros(self.base_env.action_space.action_size)
        for child in spg.root.children:
            action_probs[child.action_taken] = child.visit_count
        action_probs /= np.sum(action_probs)
            
        # Only add Dirichlet noise in the early game (first 30 moves)
        if move_count < 30:
            dirichlet_noise = np.random.dirichlet([self.dirichlet_alpha] * self.base_env.action_space.action_size)
            action_probs = (1 - self.exploration_fraction) * action_probs + self.exploration_fraction * dirichlet_noise
            # Early game: temperature = 1.0 for exploration
            temperature = 1.0
        else:
            # Late game: minimal temperature for exploitation
            temperature = 0.01
            
            
        # Select action based on temperature
        if temperature > 0.01:  # Early game - use temperature
            temperature_action_probs = action_probs ** (1 / temperature)
            temperature_action_probs /= np.sum(temperature_action_probs)
            action = np.random.choice(self.base_env.action_space.action_size, p=temperature_action_probs)
        else:  # Late game - select best move
            action = np.argmax(action_probs)
            
        # Make move
        from_pos = ((action // 64) // 8, (action // 64) % 8)
        to_pos = ((action % 64) // 8, (action % 64) % 8)
        return (from_pos, to_pos)

class SPG:
    def __init__(self, env):
        self.model = env.chess_board
        self.memory = []
        self.root = None
        self.node = None