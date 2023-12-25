import pygame as p

from controller.chess_controller import ChessController
from model.chess_components.board import Board
from view.chess_components.chess_board import ChessScreen
from view.config.view_config import ViewConfig


if __name__ == '__main__':
    p.init()
    chess_board = Board((ViewConfig.WIDTH, ViewConfig.HEIGHT), "white")
    chess_screen = ChessScreen(chess_board)
    chess_controller = ChessController(chess_board, chess_screen)
    chess_controller.start_game()
