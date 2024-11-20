import torch
import pygame as p
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")

from alphazero.alphazero_model.alphazero_parallel import AlphaZeroParallel
from alphazero.alphazero_model.chess_net import ChessNet
from gym_wrapper.environment import ChessGym

if __name__ == "__main__":
    p.init()
    env = ChessGym()
    player = "white"
    env.make_optimized(player)
    state = env.reset_optimized()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ChessNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=0.0001)
    alpha_zero = AlphaZeroParallel(model, optimizer, env, device)
    alpha_zero.learn()
