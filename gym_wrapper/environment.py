import copy
import time

import numpy as np
import pygame as p
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from controller.chess_controller import ChessController
from model.chess_components.board import Board
from view.chess_components.chess_board import ChessScreen
from view.config.view_config import ViewConfig


class ChessGym:
    def __init__(self):
        self.chess_board = None
        self.chess_screen = None
        self.chess_controller = None
        self.state_space = None
        self.action_space = None

    def make(self, player_side):
        assert player_side == "white" or player_side == "black"
        self.chess_board = Board((ViewConfig.WIDTH, ViewConfig.HEIGHT), player_side)
        self.chess_screen = ChessScreen(self.chess_board)
        self.chess_controller = ChessController(self.chess_board, self.chess_screen)
        self.state_space = StateSpace(self.chess_controller)
        self.action_space = ActionSpace(self.chess_controller)

    def make_optimized(self, player_side):
        assert player_side == "white" or player_side == "black"
        self.chess_board = Board((ViewConfig.WIDTH, ViewConfig.HEIGHT), player_side)
        self.chess_controller = ChessController(self.chess_board, None)
        self.state_space = StateSpace(self.chess_controller)
        self.action_space = ActionSpace(self.chess_controller)

    def copy(self, env):
        self.chess_board = copy.deepcopy(env.chess_board)
        self.chess_screen = ChessScreen(self.chess_board)
        self.chess_controller = ChessController(self.chess_board, self.chess_screen)
        self.state_space = StateSpace(self.chess_controller)
        self.action_space = ActionSpace(self.chess_controller)

    def copy_optimized(self, env):
        self.chess_board = copy.deepcopy(env.chess_board)
        self.chess_controller = ChessController(self.chess_board, None)
        self.state_space = StateSpace(self.chess_controller)
        self.action_space = ActionSpace(self.chess_controller)

    def close(self):
        del self.action_space
        del self.state_space
        del self.chess_controller
        del self.chess_screen
        del self.chess_board
        self.state_space = None
        self.action_space = None
        self.chess_board = None
        self.chess_screen = None
        self.chess_controller = None

    def reset(self):
        return self.chess_controller.reset()
    
    def reset_optimized(self):
        return self.chess_controller.reset_optimized()

    def step(self, model, action):
        return self.chess_controller.step(model, action)
    
    def step_inference(self, model, action):
        return self.chess_controller.step_inference(model, action)

    def simulate(self, model, action):
        child_state = self.chess_controller.simulate(model, action)
        self.chess_controller.undo_move()
        return child_state

    def get_reward_and_terminated(self, model):
        return model.white_reward, model.black_reward, model.checkmate or model.stalemate

    def get_opponent(self, player):
        return "black" if player == "white" else "white"
    

class ActionSpace:
    def __init__(self, chess_controller):
        self.shape = (64, 64)
        self.action_size = 64 * 64
        self.chess_controller = chess_controller

    def sample(self):
        return self.chess_controller.random_action()


class StateSpace:
    def __init__(self, chess_controller):
        self.chess_controller = chess_controller
        self.shape = self.chess_controller.model.STATE_SIZE

    def get_state(self):
        return self.chess_controller.model.get_state()


if __name__ == '__main__':
    p.init()
    env = ChessGym()
    env.make("white")
    state = env.reset()
    white_score = 0
    black_score = 0
    done = False

    while not done:
        from_pos, to_pos = env.action_space.sample()
        white_reward, black_reward, done, _, _ = env.step_inference(state, (from_pos, to_pos))
        white_score += white_reward
        black_score += black_reward
        print(f"White Score: {white_score}, Black Score: {black_score}")
        time.sleep(0.2)

    env.close()
