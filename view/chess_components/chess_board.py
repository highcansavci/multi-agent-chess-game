import pygame as p
import pygame.display
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from model.chess_components.board import Board
from view.chess_components.pieces import PiecesImagePrototype
from view.config.view_config import ViewConfig


class ChessScreen:
    def __init__(self, board: Board):
        self.colors = [ViewConfig.COLOR_BEIGE, ViewConfig.COLOR_BROWN]
        self.model = board
        self.screen = p.display.set_mode((ViewConfig.WIDTH, ViewConfig.HEIGHT))
        self.clock = p.time.Clock()
        self.screen.fill(ViewConfig.COLOR_BEIGE)
        self.draw_game(self.model)

    def draw_game(self, model):
        self.draw_board()
        self.draw_pieces(model)

    def draw_board(self):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                p.draw.rect(self.screen, self.colors[(i + j) % 2],
                            p.Rect(j * ViewConfig.SQ_SIZE, i * ViewConfig.SQ_SIZE,
                                   ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))

    def draw_pieces(self, model):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = model.board[i][j]
                if piece is not None:
                    image = PiecesImagePrototype.IMAGES[(piece.color, piece.type)]
                    self.screen.blit(image, p.Rect(j * ViewConfig.SQ_SIZE, i * ViewConfig.SQ_SIZE,
                                                   ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
                else:
                    p.draw.rect(self.screen, self.colors[(i + j) % 2],
                                p.Rect(j * ViewConfig.SQ_SIZE, i * ViewConfig.SQ_SIZE,
                                       ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
        pygame.display.update()
