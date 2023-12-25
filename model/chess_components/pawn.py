from abc import ABC
import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from model.chess_components.base_piece import BasePiece


class Pawn(BasePiece, ABC):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.type = "pawn"
        self.reward = 0.01
        self.initial_pawn_move = False


class BlackPawn(Pawn):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "black"
        self.state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return model.white_king_location in moves

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                           model) if not model.white_moves else []

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        if initial_move:
            return []
        possible_moves = [(self.position_x + 1, self.position_y - 1),
                          (self.position_x + 1, self.position_y + 1),
                          (self.position_x + 1, self.position_y),
                          (self.position_x + 2, self.position_y)] if player_is_white else [
            (self.position_x - 1, self.position_y - 1),
            (self.position_x - 1, self.position_y + 1),
            (self.position_x - 1, self.position_y),
            (self.position_x - 2, self.position_y)]

        if not self.initial_pawn_move:
            possible_moves.remove((self.position_x + 2 if player_is_white else self.position_x - 2, self.position_y))
        if target_piece is not None:
            possible_moves.remove((self.position_x + 1 if player_is_white else self.position_x - 1, self.position_y))
        elif target_piece is None or target_piece.color == "black":
            possible_moves.remove(
                (self.position_x + 1 if player_is_white else self.position_x - 1, self.position_y - 1))
            possible_moves.remove(
                (self.position_x + 1 if player_is_white else self.position_x - 1, self.position_y + 1))

        for i in range(len(possible_moves) - 1, -1, -1):
            move = possible_moves[i]
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                continue
            else:
                possible_moves.remove(move)
        self.initial_pawn_move = False
        return possible_moves


class WhitePawn(Pawn):
    def __init__(self, initial_position):
        super().__init__(initial_position)
        self.color = "white"
        self.state = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    def check_control(self, player_is_white, initial_move, target_piece, model):
        if initial_move:
            return []
        moves = self.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
        return model.black_king_location in moves

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        return self.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                           model) if model.white_moves else []

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        possible_moves = [(self.position_x - 1, self.position_y - 1),
                          (self.position_x - 1, self.position_y + 1),
                          (self.position_x - 1, self.position_y),
                          (self.position_x - 2, self.position_y)] if player_is_white else [
            (self.position_x + 1, self.position_y - 1),
            (self.position_x + 1, self.position_y + 1),
            (self.position_x + 1, self.position_y),
            (self.position_x + 2, self.position_y)]
        if not self.initial_pawn_move:
            possible_moves.remove((self.position_x - 2 if player_is_white else self.position_x + 2, self.position_y))
        if target_piece is not None:
            possible_moves.remove((self.position_x - 1 if player_is_white else self.position_x + 1, self.position_y))
        elif target_piece is None or target_piece.color == "white":
            possible_moves.remove(
                (self.position_x - 1 if player_is_white else self.position_x + 1, self.position_y - 1))
            possible_moves.remove(
                (self.position_x - 1 if player_is_white else self.position_x + 1, self.position_y + 1))

        for i in range(len(possible_moves) - 1, -1, -1):
            move = possible_moves[i]
            if 0 <= move[0] < 8 and 0 <= move[1] < 8:
                continue
            else:
                possible_moves.remove(move)
        self.initial_pawn_move = False
        return possible_moves
