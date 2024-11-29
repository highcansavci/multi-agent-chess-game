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
        self.reward = 5

    def get_attack_path(self, from_pos, to_pos):
        return []


class BlackKing(King):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "black"
        self.state = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]

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
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)

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
                if end_piece is not None and end_piece.color == self.color:
                    continue

                # Check if the target square is threatened by white pieces
                if not is_square_threatened((target_row, target_column), "black" if self.color == "white" else "white", model):
                    moves.append((target_row, target_column))
        print("Black King moves: ", moves)
        return moves


class WhiteKing(King):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "white"
        self.state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

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
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)

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
                if end_piece is not None and end_piece.color == self.color:
                    continue

                # Check if the target square is threatened by black pieces
                if not is_square_threatened((target_row, target_column), "black" if self.color == "white" else "white", model):
                    moves.append((target_row, target_column))
        print("White King moves: ", moves)
        return moves


def is_square_threatened(square, opponent_color, model):
    """
    Check if a specific square is threatened by any opponent's pieces.

    Args:
        square (tuple): The target square (row, col).
        opponent_color (str): The color of the opponent ("white" or "black").
        model: The chess model containing the board state.

    Returns:
        bool: True if the square is threatened, False otherwise.
    """
    for row in range(ViewConfig.DIMENSION):
        for col in range(ViewConfig.DIMENSION):
            piece = model.board[row][col]

            if piece is not None and piece.type != "king" and piece.color == opponent_color:
                # Check if the piece can control the target square
                if piece.type == "pawn" and piece.check_control_target(player_is_white=(opponent_color == "white"),
                    initial_move=False,
                    target_piece=None,
                    model=model,
                    target_position=square):
                    return True
                possible_moves = piece.get_all_possible_moves(
                    player_is_white=(opponent_color == "white"),
                    initial_move=False,
                    target_piece=None,
                    model=model
                )
                if square in possible_moves:
                    return True

    return False
