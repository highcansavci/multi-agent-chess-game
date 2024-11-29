from abc import ABC
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from model.chess_components.base_piece import BasePiece
from view.config.view_config import ViewConfig


class Queen(BasePiece, ABC):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.type = "queen"
        self.reward = 25

    def get_attack_path(self, from_pos, to_pos):
        """
        Get attack path for a Queen (combination of Rook and Bishop logic).
        """
        path = []
        row_diff = to_pos[0] - from_pos[0]
        col_diff = to_pos[1] - from_pos[1]

        if abs(row_diff) == abs(col_diff):  # Diagonal
            step_row = row_diff // abs(row_diff)
            step_col = col_diff // abs(col_diff)
        elif row_diff == 0:  # Horizontal
            step_row, step_col = 0, col_diff // abs(col_diff)
        elif col_diff == 0:  # Vertical
            step_row, step_col = row_diff // abs(row_diff), 0
        else:
            return path  # Invalid path for a Queen

        current_row, current_col = from_pos[0] + step_row, from_pos[1] + step_col
        while (current_row, current_col) != to_pos:
            path.append((current_row, current_col))
            current_row += step_row
            current_col += step_col

        return path


class BlackQueen(Queen):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "black"
        self.state = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return model.white_king_location in moves
    
    def check_control_target(self, player_is_white, initial_move, target_piece, model, target_position):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return target_position in moves

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                           model) if not model.white_moves else []

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        moves = []
        directions = [(-1, 1), (1, 1), (-1, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (0, -1)]
        for dir_ in directions:
            for i in range(1, ViewConfig.DIMENSION):
                target_row = self.position_x + dir_[0] * i
                target_column = self.position_y + dir_[1] * i
                if 0 <= target_row < ViewConfig.DIMENSION and 0 <= target_column < ViewConfig.DIMENSION:
                    end_piece = model.board[target_row][target_column]
                    if end_piece is None:
                        moves.append((target_row, target_column))
                    elif end_piece.color != self.color:
                        moves.append((target_row, target_column))
                        break
                    else:
                        break
                else:
                    break
        return moves


class WhiteQueen(Queen):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "white"
        self.state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return model.black_king_location in moves
    
    def check_control_target(self, player_is_white, initial_move, target_piece, model, target_position):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return target_position in moves

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                           model) if model.white_moves else []

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        moves = []
        directions = [(-1, 1), (1, 1), (-1, -1), (1, -1), (-1, 0), (1, 0), (0, 1), (0, -1)]
        for dir_ in directions:
            for i in range(1, ViewConfig.DIMENSION):
                target_row = self.position_x + dir_[0] * i
                target_column = self.position_y + dir_[1] * i
                if 0 <= target_row < ViewConfig.DIMENSION and 0 <= target_column < ViewConfig.DIMENSION:
                    end_piece = model.board[target_row][target_column]
                    if end_piece is None:
                        moves.append((target_row, target_column))
                    elif end_piece.color != self.color:
                        moves.append((target_row, target_column))
                        break
                    else:
                        break
                else:
                    break
        return moves
