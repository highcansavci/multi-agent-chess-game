import time
import torch
import pygame as p
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")

from alphazero.alpha_mcts.mcts import MCTSParallel
from gym_wrapper.record import VideoRecorder

from alphazero.alphazero_model.alphazero_parallel import AlphaZeroParallel
from alphazero.alphazero_model.chess_net import ChessNet
from gym_wrapper.environment import ChessGym

if __name__ == "__main__":

    p.init()
    env_ = ChessGym()
    record_env = VideoRecorder(env_, "alphazero.mp4")
    env_.make("white")
    state = env_.reset()
    score = 0
    done = False
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ChessNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=0.0001)
    model.load_state_dict(torch.load("model_0.pt", map_location=device, weights_only=True))
    optimizer.load_state_dict(torch.load("optimizer_0.pt", map_location=device, weights_only=True))
    mcts = MCTSParallel(env_, model, device)
    alpha_zero = AlphaZeroParallel(model, optimizer, env_, device)
    move_count = 0

    while not done:
        from_pos, to_pos = alpha_zero.inference(mcts, move_count)
        reward, done, _, _ = env_.step_inference(state, (from_pos, to_pos))
        score += reward
        print(f"Score: {score}")
        record_env.record()
        time.sleep(1)
        move_count += 1

    record_env.export()
    env_.close()
