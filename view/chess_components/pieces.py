import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from model.chess_components.base_piece import BasePiece
import pygame as p
from view.config.view_config import ViewConfig


class PiecesImagePrototype:
    IMAGES = dict()
    IMAGES[("black", "pawn")] = p.transform.scale(p.image.load("../assets/images/bp.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("black", "bishop")] = p.transform.scale(p.image.load("../assets/images/bB.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("black", "rook")] = p.transform.scale(p.image.load("../assets/images/bR.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("black", "knight")] = p.transform.scale(p.image.load("../assets/images/bN.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("black", "queen")] = p.transform.scale(p.image.load("../assets/images/bQ.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("black", "king")] = p.transform.scale(p.image.load("../assets/images/bK.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("white", "pawn")] = p.transform.scale(p.image.load("../assets/images/wp.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("white", "bishop")] = p.transform.scale(p.image.load("../assets/images/wB.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("white", "rook")] = p.transform.scale(p.image.load("../assets/images/wR.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("white", "knight")] = p.transform.scale(p.image.load("../assets/images/wN.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("white", "queen")] = p.transform.scale(p.image.load("../assets/images/wQ.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))
    IMAGES[("white", "king")] = p.transform.scale(p.image.load("../assets/images/wK.png"), (ViewConfig.SQ_SIZE, ViewConfig.SQ_SIZE))


class Pieces:
    def __init__(self, piece: BasePiece, image_path):
        self.piece = piece
        self.image_path = image_path

    def get_piece(self):
        return self.piece

    def get_image(self):
        return PiecesImagePrototype.IMAGES[(self.piece.color, self.piece.type)]
