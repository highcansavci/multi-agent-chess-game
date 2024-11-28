import copy
import numpy as np
import sys
from collections import deque

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
    def __init__(self, board_size, player_side="white"):
        self.board_size = board_size
        self.player_side = player_side
        self.from_pos = None
        self.to_pos = None
        self.movement_selected = deque()
        self.board = None
        self.initialize_board()
        self.running = True
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
        self.move_count = 0
        self.STATE_SIZE = (8, 8, 16)
        self.MAX_MOVES = 500

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

        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None and piece.color == "black" and piece.type == "king":
                    pos_x, pos_y = (i, j)
                    
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

        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None and piece.color == "white" and piece.type == "king":
                    pos_x, pos_y = (i, j)
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
        """
        Check if any pawns have reached their promotion rank and promote them to queens.
        White pawns promote on the 0th rank, and black pawns promote on the 7th rank.
        """
        # Check for white pawn promotion on the 0th rank
        for j in range(ViewConfig.DIMENSION):
            if isinstance(self.board[0][j], WhitePawn):
                self.board[0][j] = WhiteQueen((0, j))

        # Check for black pawn promotion on the 7th rank
        for j in range(ViewConfig.DIMENSION):
            if isinstance(self.board[7][j], BlackPawn):
                self.board[7][j] = BlackQueen((7, j))

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

    def change_perspective(self):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None:
                    piece.adjust_piece_state()
                    piece.color = "white" if piece.color == "black" else "black"

    def update_white_king_location(self):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None and piece.color == "white" and piece.type == "king":
                    self.white_king_location = (i, j)

    def update_black_king_location(self):
        for i in range(ViewConfig.DIMENSION):
            for j in range(ViewConfig.DIMENSION):
                piece = self.board[i][j]
                if piece is not None and piece.color == "black" and piece.type == "king":
                    self.black_king_location = (i, j)
    
    def get_white_check_path(self, model):
        """
        Identify pieces putting white king in check and their attack paths
        
        Returns:
        - List of pieces directly causing check
        - Attack paths for blocking or capturing
        """
        checking_pieces = []
        
        # Check all black pieces
        for row in range(ViewConfig.DIMENSION):
            for col in range(ViewConfig.DIMENSION):
                piece = model.board[row][col]
                
                # Skip if no piece or white piece
                if not piece:
                    continue
                
                if piece.color == "black":
                    if piece.check_control(None, None, None, model):
                        checking_pieces.append((piece, (row, col)))
        
        # If no checking pieces, return empty list
        return checking_pieces

    def get_black_check_path(self, model):
        """
        Identify pieces putting black king in check and their attack paths
        
        Returns:
        - List of pieces directly causing check
        - Attack paths for blocking or capturing
        """
        checking_pieces = []
        
        # Check all white pieces
        for row in range(ViewConfig.DIMENSION):
            for col in range(ViewConfig.DIMENSION):
                piece = model.board[row][col]
                
                # Skip if no piece or black piece
                if not piece:
                    continue
                
                # Check if any attack move targets black king
                if piece.color == "white":
                    if piece.check_control(None, None, None, model):                    
                        checking_pieces.append((piece, (row, col)))
        
        # If no checking pieces, return empty list
        return checking_pieces

    def get_white_check_path_target(self, model, target):
        """
        Identify pieces putting white king in check and their attack paths
        
        Returns:
        - List of pieces directly causing check
        - Attack paths for blocking or capturing
        """
        checking_pieces = []
        
        # Check all black pieces
        for row in range(ViewConfig.DIMENSION):
            for col in range(ViewConfig.DIMENSION):
                piece = model.board[row][col]
                
                # Skip if no piece or white piece
                if not piece:
                    continue
                
                if piece.color == "black":
                    if piece.check_control_target(None, None, None, model, target):
                        checking_pieces.append((piece, (row, col)))
        
        # If no checking pieces, return empty list
        return checking_pieces

    def get_black_check_path_target(self, model, target):
        """
        Identify pieces putting black king in check and their attack paths
        
        Returns:
        - List of pieces directly causing check
        - Attack paths for blocking or capturing
        """
        checking_pieces = []
        
        # Check all white pieces
        for row in range(ViewConfig.DIMENSION):
            for col in range(ViewConfig.DIMENSION):
                piece = model.board[row][col]
                
                # Skip if no piece or black piece
                if not piece:
                    continue
                
                # Check if any attack move targets black king
                if piece.color == "white":
                    if piece.check_control_target(None, None, None, model, target):                    
                        checking_pieces.append((piece, (row, col)))
        
        # If no checking pieces, return empty list
        return checking_pieces     

    def explore_attacker_capture(self, model, piece, from_pos):
        """
        Find moves to capture attacking pieces, block check, or move the king to safety.
        """
        alternative_moves = []
        move_scores = []

        # Identify checking pieces and their positions
        checking_pieces = (
            self.get_white_check_path(model) if piece.color == "white" else self.get_black_check_path(model)
        )
        # If there are no checking pieces, there's no check to resolve
        if not checking_pieces:
            return alternative_moves, move_scores

        # King-specific logic
        king_piece = model.board[model.white_king_location[0]][model.white_king_location[1]] if piece.color == "white" else \
                    model.board[model.black_king_location[0]][model.black_king_location[1]]
        
        # Force the king to move to a safe square
        king_safe_moves = king_piece.get_all_valid_moves(
            model.player_side == "white", model.initial_move, None, model
        )

        for move in king_safe_moves:
            is_safe = not (
                self.get_white_check_path_target(model, move) if piece.color == "white" else self.get_black_check_path_target(model, move)
            )
            if is_safe:
                alternative_moves.append((king_piece, (king_piece.position_x, king_piece.position_y), move))
                move_scores.append(0)

        # Check if the king can safely capture the attacker
        for checking_piece, attacker_pos in checking_pieces:
            if attacker_pos in king_safe_moves:
                is_safe = not (
                    self.get_white_check_path_target(model, attacker_pos) if piece.color == "white" else self.get_black_check_path_target(model, attacker_pos)
                )
                if is_safe:
                    alternative_moves.append((king_piece, (king_piece.position_x, king_piece.position_y),attacker_pos))
                    move_scores.append(checking_piece.get_reward())

        # Other pieces capturing the attacker or blocking the check
        for checking_piece, attacker_pos in checking_pieces:
            for row in range(ViewConfig.DIMENSION):
                for col in range(ViewConfig.DIMENSION):
                    current_piece = model.board[row][col]

                    if current_piece and current_piece.color == piece.color and current_piece.type != "king":
                        moves = current_piece.get_all_valid_moves(
                            model.player_side == "white", model.initial_move, checking_piece, model
                        )

                        for move in moves:
                            if move == attacker_pos:  # Capture the attacker
                                alternative_moves.append((current_piece, (row, col), move))
                                move_scores.append(piece.get_reward())
                            elif move in checking_piece.get_attack_path(
                                attacker_pos,
                                model.white_king_location if piece.color == "black" else model.black_king_location
                            ):
                                alternative_moves.append((current_piece, (row, col), move))
                                move_scores.append(0)  # Blocking moves are lower priority

        return alternative_moves, move_scores

        
