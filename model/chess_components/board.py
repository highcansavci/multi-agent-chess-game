import numpy as np
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
from model.chess_components.bishop import BlackBishop, WhiteBishop
from model.chess_components.king import BlackKing, WhiteKing
from model.chess_components.pawn import BlackPawn, WhitePawn
from model.chess_components.knight import BlackKnight, WhiteKnight
from model.chess_components.queen import BlackQueen, WhiteQueen
from model.chess_components.rook import BlackRook, WhiteRook
from view.config.view_config import ViewConfig


class Board:
    def __init__(self, board_size, player_side="black"):
        self.board_size = board_size
        self.player_side = player_side
        self.board = None
        self.initialize_board()
        self.white_moves = True
        self.white_king_location = (7, 4) if self.player_side == "white" else (0, 4)
        self.black_king_location = (7, 4) if self.player_side == "black" else (0, 4)
        self.in_check = False
        self.white_long_castling = False
        self.white_short_castling = False
        self.black_long_castling = False
        self.black_short_castling = False
        self.initial_move = True
        self.is_white_check = False
        self.is_black_check = False
        self.checkmate = False
        self.is_white_stalemate = False
        self.is_black_stalemate = False
        self.stalemate = False
        self.castling_done = False
        self.reward = 0
        self.checkmate_reward = 1
        self.stalemate_reward = 0.5
        self.castling_reward = 0.05
        self.check_reward = 0.1
        self.STATE_SIZE = (8, 8, 16)

    def initialize_board(self):
        if self.player_side == "white":
            self.board = [
                [BlackRook((0, 0)), BlackKnight((0, 1)), BlackBishop((0, 2)), BlackQueen((0, 3)), BlackKing((0, 4)),
                 BlackBishop((0, 5)), BlackKnight((0, 6)), BlackRook((0, 7))],
                [BlackPawn((1, 0)), BlackPawn((1, 1)), BlackPawn((1, 2)), BlackPawn((1, 3)), BlackPawn((1, 4)),
                 BlackPawn((1, 5)), BlackPawn((1, 6)), BlackPawn((1, 7))],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [WhitePawn((6, 0)), WhitePawn((6, 1)), WhitePawn((6, 2)), WhitePawn((6, 3)), WhitePawn((6, 4)),
                 WhitePawn((6, 5)), WhitePawn((6, 6)), WhitePawn((6, 7))],
                [WhiteRook((7, 0)), WhiteKnight((7, 1)), WhiteBishop((7, 2)), WhiteQueen((7, 3)), WhiteKing((7, 4)),
                 WhiteBishop((7, 5)), WhiteKnight((7, 6)), WhiteRook((7, 7))]]
        else:
            self.board = [
                [WhiteRook((0, 0)), WhiteKnight((0, 1)), WhiteBishop((0, 2)), WhiteQueen((0, 3)), WhiteKing((0, 4)),
                 WhiteBishop((0, 5)), WhiteKnight((0, 6)), WhiteRook((0, 7))],
                [WhitePawn((1, 0)), WhitePawn((1, 1)), WhitePawn((1, 2)), WhitePawn((1, 3)), WhitePawn((1, 4)),
                 WhitePawn((1, 5)), WhitePawn((1, 6)), WhitePawn((1, 7))],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [None, None, None, None, None, None, None, None],
                [BlackPawn((6, 0)), BlackPawn((6, 1)), BlackPawn((6, 2)), BlackPawn((6, 3)), BlackPawn((6, 4)),
                 BlackPawn((6, 5)), BlackPawn((6, 6)), BlackPawn((6, 7))],
                [BlackRook((7, 0)), BlackKnight((7, 1)), BlackBishop((7, 2)), BlackQueen((7, 3)), BlackKing((7, 4)),
                 BlackBishop((7, 5)), BlackKnight((7, 6)), BlackRook((7, 7))]]

    def get_check_situation_white(self, player_is_white, initial_move, target_piece, model):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is None:
                    continue
                if piece.color == "white":
                    if piece.check_control(player_is_white, initial_move, target_piece, model):
                        return True
        return False

    def get_check_situation_black(self, player_is_white, initial_move, target_piece, model):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is None:
                    continue
                if piece.color == "black":
                    if piece.check_control(player_is_white, initial_move, target_piece, model):
                        return True
        return False

    def get_stalemate_situation_white(self, player_is_white, initial_move, target_piece, model):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is None:
                    continue
                if piece.color == "black" and piece.type != "king":
                    if piece.get_all_possible_moves(player_is_white, initial_move, target_piece, model):
                        return False

        if initial_move:
            return False

        pos_x, pos_y = model.black_king_location
        black_king = model.board[pos_x][pos_y]
        black_king_available_moves = black_king.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                                                       model)

        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is None:
                    continue
                elif piece.color == "white":
                    moves = piece.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
                    for k in range(len(black_king_available_moves) - 1, -1, -1):
                        if black_king_available_moves[k] in moves:
                            black_king_available_moves.remove(black_king_available_moves[k])

        return len(black_king_available_moves) == 0

    def get_stalemate_situation_black(self, player_is_white, initial_move, target_piece, model):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is None:
                    continue
                if piece.color == "white" and piece.type != "king":
                    if piece.get_all_possible_moves(player_is_white, initial_move, target_piece, model):
                        return False

        pos_x, pos_y = model.white_king_location
        white_king = model.board[pos_x][pos_y]
        white_king_available_moves = white_king.get_all_possible_moves(player_is_white, initial_move, target_piece,
                                                                       model)
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is None:
                    continue
                elif piece.color == "black":
                    moves = piece.get_all_possible_moves(player_is_white, initial_move, target_piece, model)
                    for k in range(len(white_king_available_moves) - 1, -1, -1):
                        if white_king_available_moves[k] in moves:
                            white_king_available_moves.remove(white_king_available_moves[k])

        return len(white_king_available_moves) == 0

    def check_situation_pawn_promotion(self):
        promote_location = (0, 7)
        for i in promote_location:
            for j in range(ViewConfig.DIMENSION):
                if isinstance(self.board[i][j], WhitePawn):
                    self.board[i][j] = WhiteQueen((i, j))
                elif isinstance(self.board[i][j], BlackPawn):
                    self.board[i][j] = BlackQueen((i, j))

    def check_situation_castling(self, is_white_check, is_black_check):
        if self.player_side == "white":
            self.white_long_castling = isinstance(self.board[7][0], WhiteRook) and not self.board[7][
                0].is_moved and isinstance(self.board[7][4], WhiteKing) and not self.board[7][4].is_moved and \
                                       self.board[7][1] is None and self.board[7][2] is None and self.board[7][
                                           3] is None and not is_black_check
            self.white_short_castling = isinstance(self.board[7][7], WhiteRook) and not self.board[7][
                7].is_moved and isinstance(self.board[7][4], WhiteKing) and not self.board[7][4].is_moved and \
                                        self.board[7][5] is None and self.board[7][6] is None and not is_black_check
            self.black_long_castling = isinstance(self.board[0][0], BlackRook) and not self.board[0][
                0].is_moved and isinstance(self.board[0][4], BlackKing) and not self.board[0][4].is_moved and \
                                       self.board[0][1] is None and self.board[0][2] is None and self.board[0][
                                           3] is None and not is_white_check
            self.black_short_castling = isinstance(self.board[0][7], BlackRook) and not self.board[0][
                7].is_moved and isinstance(self.board[0][4], BlackKing) and not self.board[0][4].is_moved and \
                                        self.board[0][5] is None and self.board[0][6] is None and not is_white_check
        else:
            self.white_long_castling = isinstance(self.board[0][0], WhiteRook) and not self.board[0][
                0].is_moved and isinstance(self.board[0][4], WhiteKing) and not self.board[0][4].is_moved and \
                                       self.board[0][1] is None and self.board[0][2] is None and self.board[0][
                                           3] is None and not is_black_check
            self.white_short_castling = isinstance(self.board[0][7], WhiteRook) and not self.board[0][
                7].is_moved and isinstance(self.board[0][4], WhiteKing) and not self.board[0][4].is_moved and \
                                        self.board[0][5] is None and self.board[0][6] is None and not is_black_check
            self.black_long_castling = isinstance(self.board[7][0], BlackRook) and not self.board[7][
                0].is_moved and isinstance(self.board[7][4], BlackKing) and not self.board[7][4].is_moved and \
                                       self.board[7][1] is None and self.board[7][2] is None and self.board[7][
                                           3] is None and not is_white_check
            self.black_short_castling = isinstance(self.board[7][7], BlackRook) and not self.board[7][
                7].is_moved and isinstance(self.board[7][4], BlackKing) and not self.board[7][4].is_moved and \
                                        self.board[7][5] is None and self.board[7][6] is None and not is_white_check

    def get_state(self):
        state_array = np.zeros(self.STATE_SIZE)
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                each_state = []
                piece = self.board[i][j]
                if piece is None:
                    each_state += [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                else:
                    each_state += piece.get_state()
                each_state += [int(self.black_long_castling or self.black_short_castling),
                               int(self.white_long_castling or self.white_short_castling),
                               int(self.is_black_check),
                               int(self.is_white_check)]
                state_array[i, j, :] = np.array(each_state)
        return state_array

    def get_states(self, states):
        state_array = np.zeros((len(states), self.STATE_SIZE[0], self.STATE_SIZE[1], self.STATE_SIZE[2]))
        for num_state in range(len(states)):
            for i in range(ViewConfig.DIMENSION):
                for j in range(ViewConfig.DIMENSION):
                    each_state = []
                    piece = states[num_state].board[i][j]
                    if piece is None:
                        each_state += [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    else:
                        each_state += piece.get_state()
                    each_state += [int(states[num_state].black_long_castling or states[num_state].black_short_castling),
                                   int(states[num_state].white_long_castling or states[num_state].white_short_castling),
                                   int(states[num_state].is_black_check),
                                   int(states[num_state].is_white_check)]
                    state_array[num_state, i, j, :] = np.array(each_state)
        return state_array

    def get_state_(self, state):
        state_array = np.zeros(self.STATE_SIZE)
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                each_state = []
                piece = state.board[i][j]
                if piece is None:
                    each_state += [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                else:
                    each_state += piece.get_state()
                each_state += [int(state.black_long_castling or state.black_short_castling),
                               int(state.white_long_castling or state.white_short_castling),
                               int(state.is_black_check),
                               int(state.is_white_check)]
                state_array[i, j, :] = np.array(each_state)
        return state_array

    def calculate_move_reward(self, piece):
        return 0 if piece is None else piece.get_reward()

    def calculate_coef(self):
        return 1 if self.white_moves and self.player_side == "white" or not self.white_moves and self.player_side == "black" else -1

    def calculate_coef_check(self):
        return 1 if self.is_white_check and self.player_side == "white" or not self.is_black_check and self.player_side == "black" else -1

    def calculate_check_reward(self):
        return self.check_reward if self.is_white_check or self.is_black_check else 0

    def calculate_checkmate_reward(self):
        return 1 if self.is_white_check and self.player_side == "white" or not self.is_black_check and self.player_side == "black" else -1

    def calculate_stalemate_reward(self):
        return 0.5

    def generate_all_valid_moves(self):
        moves = []
        encoded_moves = np.zeros(64 * 64)
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None:
                    moves.extend([((i, j), move) for move in piece.get_all_valid_moves(self.player_side == "white",
                                                                                       None, None,
                                                                                       self)])

        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                for k in range(ViewConfig.DIMENSION):
                    for t in range(ViewConfig.DIMENSION):
                        if ((i, j), (k, t)) in moves:
                            encoded_moves[(i * 8 + j) * 64 + (k * 8 + t)] = 1

        return moves, encoded_moves

    def generate_all_valid_moves(self, model):
        moves = []
        encoded_moves = np.zeros(64 * 64)
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = model.board[i][j]
                if piece is not None:
                    moves.extend([((i, j), move) for move in piece.get_all_valid_moves(model.player_side == "white",
                                                                                       None, None,
                                                                                       model)])

        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                for k in range(ViewConfig.DIMENSION):
                    for t in range(ViewConfig.DIMENSION):
                        if ((i, j), (k, t)) in moves:
                            encoded_moves[(i * 8 + j) * 64 + (k * 8 + t)] = 1

        return moves, encoded_moves

    def update_positions(self):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None:
                    piece.position_x = i
                    piece.position_y = j

    def update_white_king_location(self):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None and piece.color == "white" and piece.type == "king":
                    return i, j

    def update_black_king_location(self):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None and piece.color == "black" and piece.type == "king":
                    return i, j
