from abc import ABC
import sys

from view.config.view_config import ViewConfig
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from model.chess_components.base_piece import BasePiece


class Pawn(BasePiece, ABC):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.type = "pawn"
        self.reward = 1
        self.initial_pawn_move = False
    
    def get_attack_path(self, from_pos, to_pos):
        return []


class BlackPawn(Pawn):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "black"
        self.state = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        """
        Determine if the pawn is controlling the square occupied by the black king.
        Pawns control diagonally, not forward.
        """
        if initial_move:
            return False  # Pawns do not control any squares on their first move

        row, col = self.position_x, self.position_y

        # Diagonal control squares for a black pawn
        diagonal_controls = []
        if row + 1 < ViewConfig.DIMENSION and col - 1 >= 0:
            diagonal_controls.append((row + 1, col - 1))
        if row + 1 < ViewConfig.DIMENSION and col + 1 < ViewConfig.DIMENSION:
            diagonal_controls.append((row + 1, col + 1))

        # Check if white king is in any of the controlled squares
        return model.white_king_location in diagonal_controls

    
    def check_control_target(self, player_is_white, initial_move, target_piece, model, target_position):
        """
        Determine if the pawn is controlling the square occupied by the black king.
        Pawns control diagonally, not forward.
        """
        if initial_move:
            return False  # Pawns do not control any squares on their first move

        row, col = self.position_x, self.position_y

        # Diagonal control squares for a black pawn
        diagonal_controls = []
        if row + 1 < ViewConfig.DIMENSION and col - 1 >= 0:
            diagonal_controls.append((row + 1, col - 1))
        if row + 1 < ViewConfig.DIMENSION and col + 1 < ViewConfig.DIMENSION:
            diagonal_controls.append((row + 1, col + 1))

        # Check if white king is in any of the controlled squares
        return target_position in diagonal_controls

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                           model)

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        moves = []
        row, col = self.position_x, self.position_y

        # One square forward
        if row + 1 < ViewConfig.DIMENSION and model.board[row + 1][col] is None:
            moves.append((row + 1, col))

            # Two squares forward (only if initial move and one square forward is also empty)
            if self.initial_pawn_move and row + 2 < ViewConfig.DIMENSION and model.board[row + 2][col] is None:
                moves.append((row + 2, col))

        # Diagonal captures
        if row + 1 < ViewConfig.DIMENSION and col - 1 >= 0:
            target_piece = model.board[row + 1][col - 1]
            if target_piece is not None and target_piece.color == "white":
                moves.append((row + 1, col - 1))
        if row + 1 < ViewConfig.DIMENSION and col + 1 < ViewConfig.DIMENSION:
            target_piece = model.board[row + 1][col + 1]
            if target_piece is not None and target_piece.color == "white":
                moves.append((row + 1, col + 1))

        return moves


class WhitePawn(Pawn):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "white"
        self.state = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        """
        Determine if the pawn is controlling the square occupied by the black king.
        Pawns control diagonally, not forward.
        """
        if initial_move:
            return False  # Pawns do not control any squares on their first move

        row, col = self.position_x, self.position_y

        # Diagonal control squares for a white pawn
        diagonal_controls = []
        if row - 1 >= 0 and col - 1 >= 0:
            diagonal_controls.append((row - 1, col - 1))
        if row - 1 >= 0 and col + 1 < ViewConfig.DIMENSION:
            diagonal_controls.append((row - 1, col + 1))
        return model.black_king_location in diagonal_controls
    
    def check_control_target(self, player_is_white, initial_move, target_piece, model, target_position):
        """
        Determine if the pawn is controlling the square occupied by the black king.
        Pawns control diagonally, not forward.
        """
        if initial_move:
            return False  # Pawns do not control any squares on their first move

        row, col = self.position_x, self.position_y

        # Diagonal control squares for a white pawn
        diagonal_controls = []
        if row - 1 >= 0 and col - 1 >= 0:
            diagonal_controls.append((row - 1, col - 1))
        if row - 1 >= 0 and col + 1 < ViewConfig.DIMENSION:
            diagonal_controls.append((row - 1, col + 1))
        return target_position in diagonal_controls

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                           model)

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        moves = []
        row, col = self.position_x, self.position_y

        # One square forward
        if row - 1 >= 0 and model.board[row - 1][col] is None:
            moves.append((row - 1, col))

            # Two squares forward (only if initial move and one square forward is also empty)
            if self.initial_pawn_move and row - 2 >= 0 and model.board[row - 2][col] is None:
                moves.append((row - 2, col))

        # Diagonal captures
        if row - 1 >= 0 and col - 1 >= 0:
            target_piece = model.board[row - 1][col - 1]
            if target_piece is not None and target_piece.color == "black":
                moves.append((row - 1, col - 1))
        if row - 1 >= 0 and col + 1 < ViewConfig.DIMENSION:
            target_piece = model.board[row - 1][col + 1]
            if target_piece is not None and target_piece.color == "black":
                moves.append((row - 1, col + 1))

        return moves
