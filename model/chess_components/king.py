from abc import ABC
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from model.chess_components.base_piece import BasePiece
from view.config.view_config import ViewConfig


class King(BasePiece, ABC):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.type = "king"
        self.castling = False
        self.reward = 0.5


class BlackKing(King):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "black"
        self.state = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return model.white_king_location in moves

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece, model) if not model.white_moves else []

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        moves = []
        directions = [(-1, 1), (1, 1), (-1, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (0, -1)]
        if model.black_long_castling:
            directions += [(0, -2)]
        if model.black_short_castling:
            directions += [(0, 2)]
        for dir_ in directions:
            target_row = self.position_x + dir_[0]
            target_column = self.position_y + dir_[1]
            if 0 <= target_row < ViewConfig.DIMENSION and 0 <= target_column < ViewConfig.DIMENSION:
                end_piece = model.board[target_row][target_column]
                if end_piece is not None and end_piece.color == "black":
                    continue
                moves.append((target_row, target_column))
            else:
                continue
        return moves


class WhiteKing(King):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "white"
        self.state = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return model.black_king_location in moves

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece, model) if model.white_moves else []

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        moves = []
        directions = [(-1, 1), (1, 1), (-1, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (0, -1)]
        if model.white_long_castling:
            directions += [(0, -2)]
        if model.white_short_castling:
            directions += [(0, 2)]
        for dir_ in directions:
            target_row = self.position_x + dir_[0]
            target_column = self.position_y + dir_[1]
            if 0 <= target_row < ViewConfig.DIMENSION and 0 <= target_column < ViewConfig.DIMENSION:
                end_piece = model.board[target_row][target_column]
                if end_piece is not None and end_piece.color == "white":
                    continue
                moves.append((target_row, target_column))
            else:
                continue
        return moves
