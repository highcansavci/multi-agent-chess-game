import random
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
import pygame as p
from collections import deque
from model.chess_components.board import Board
from view.chess_components.chess_board import ChessScreen
from view.config.view_config import ViewConfig
import copy


class ChessController:
    def __init__(self, model: Board, view: ChessScreen):
        self.from_pos = None
        self.to_pos = None
        self.model = model
        self.view = view
        self.running = True
        self.movement_selected = deque()
        self.model_trace = deque(maxlen=1)

    def start_game(self):
        p.init()
        while self.running:
            for e in p.event.get():
                self.check_quit_game(e)
                self.check_movement(e)
            self.view.clock.tick(ViewConfig.MAX_FPS)
            p.display.flip()

    def check_quit_game(self, event):
        if event.type == p.QUIT:
            self.running = False
        elif event.type == p.KEYDOWN:
            if event.key == p.K_ESCAPE:
                self.running = False

    def reset(self):
        self.model.initialize_board()
        self.view.draw_game()
        return self.model.get_state()

    def check_movement(self, event):
        if event.type == p.MOUSEBUTTONDOWN:
            location = p.mouse.get_pos()
            column = location[0] // ViewConfig.SQ_SIZE
            row = location[1] // ViewConfig.SQ_SIZE
            self.movement_selected.append((row, column))
            if len(self.movement_selected) == 2:
                self.move_piece()
                self.movement_selected.clear()

    def move_piece(self):
        from_pos, to_pos = self.movement_selected
        self.model_trace.append(copy.deepcopy(self.model))
        self.model.check_situation_castling(self.model.is_white_check, self.model.is_black_check)
        if self.model.board[from_pos[0]][from_pos[1]] is None:
            self.movement_selected.clear()
            return
        moves = self.model.board[from_pos[0]][from_pos[1]].get_all_valid_moves(
            self.model.player_side == "white",
            self.model.initial_move,
            self.model.board[to_pos[0]][to_pos[1]],
            self.model)
        if to_pos not in moves:
            self.movement_selected.clear()
            return
        piece = self.model.board[from_pos[0]][from_pos[1]]
        if self.model.board[to_pos[0]][to_pos[1]] is None or (
                self.model.board[from_pos[0]][from_pos[1]].color == "white" and self.model.board[to_pos[0]][
            to_pos[1]].color == "black") or (
                self.model.board[from_pos[0]][from_pos[1]] == "black" and self.model.board[to_pos[0]][
            to_pos[1]].color == "white"):
            self.model.board[to_pos[0]][to_pos[1]], self.model.board[from_pos[0]][from_pos[1]] = \
                self.model.board[from_pos[0]][from_pos[1]], None
        if (((self.model.white_long_castling and piece is not None and piece.color == "white") or
             (
                     self.model.black_long_castling and piece is not None and piece.color == "black")) and piece.type == "king" and
                from_pos[1] - to_pos[1] == 2):
            self.model.castling_done = True
            self.model.board[to_pos[0]][3], self.model.board[from_pos[0]][0] = \
                self.model.board[from_pos[0]][0], None
            self.model.board[to_pos[0]][3].move((to_pos[0], 3))
        if (((self.model.white_short_castling and piece is not None and piece.color == "white") or
             (
                     self.model.black_short_castling and piece is not None and piece.color == "black")) and piece.type == "king" and
                to_pos[1] - from_pos[1] == 2):
            self.model.castling_done = True
            self.model.board[to_pos[0]][5], self.model.board[from_pos[0]][7] = \
                self.model.board[from_pos[0]][7], None
            self.model.board[to_pos[0]][5].move((to_pos[0], 5))
        self.model.board[to_pos[0]][to_pos[1]].move(to_pos)
        piece = self.model.board[to_pos[0]][to_pos[1]]
        if piece is not None and piece.color == "white" and piece.type == "king":
            self.model.white_king_location = (to_pos[0], to_pos[1])
        elif piece is not None and piece.color == "black" and piece.type == "king":
            self.model.black_king_location = (to_pos[0], to_pos[1])
        self.model.is_white_check = self.model.get_check_situation_white(self.model.player_side == "white",
                                                                         self.model.initial_move,
                                                                         self.model.board[to_pos[0]][to_pos[1]],
                                                                         self.model)
        self.model.is_black_check = self.model.get_check_situation_black(self.model.player_side == "white",
                                                                         self.model.initial_move,
                                                                         self.model.board[to_pos[0]][to_pos[1]],
                                                                         self.model)
        self.model.is_white_stalemate = self.model.get_stalemate_situation_white(self.model.player_side == "white",
                                                                                 self.model.initial_move,
                                                                                 self.model.board[to_pos[0]][to_pos[1]],
                                                                                 self.model)
        self.model.is_black_stalemate = self.model.get_stalemate_situation_black(self.model.player_side == "white",
                                                                                 self.model.initial_move,
                                                                                 self.model.board[to_pos[0]][to_pos[1]],
                                                                                 self.model)
        if self.model.is_white_check and not self.model.white_moves or self.model.is_black_check and self.model.white_moves:
            self.model.checkmate = True
            print("Checkmate:", self.model.checkmate)
            self.running = False

        elif self.model.is_white_stalemate and not self.model.is_white_check or self.model.is_black_stalemate and not self.model.is_black_check:
            self.model.stalemate = True
            print("Stalemate:", self.model.stalemate)
            self.running = False
        self.model.check_situation_pawn_promotion()
        self.view.draw_game()
        self.model.white_moves = not self.model.white_moves
        self.model.initial_move = False

    def undo_move(self):
        prev_model = self.model_trace.pop()
        self.model.board_size = prev_model.board_size
        self.model.player_side = prev_model.player_side
        self.model.board = prev_model.board
        self.model.white_moves = prev_model.white_moves
        self.model.white_king_location = prev_model.white_king_location
        self.model.black_king_location = prev_model.black_king_location
        self.model.in_check = prev_model.in_check
        self.model.white_long_castling = prev_model.white_long_castling
        self.model.white_short_castling = prev_model.white_short_castling
        self.model.black_long_castling = prev_model.black_long_castling
        self.model.black_short_castling = prev_model.black_short_castling
        self.model.initial_move = prev_model.initial_move
        self.model.is_white_check = prev_model.is_white_check
        self.model.is_black_check = prev_model.is_black_check
        self.model.checkmate = prev_model.checkmate
        self.model.is_white_stalemate = prev_model.is_white_stalemate
        self.model.is_black_stalemate = prev_model.is_black_stalemate
        self.model.stalemate = prev_model.stalemate
        self.model.castling_done = prev_model.castling_done
        self.model.reward = prev_model.reward
        self.view.draw_game()

    def step(self, action):
        from_pos, to_pos = action
        self.model_trace.append(copy.deepcopy(self.model))
        self.model.check_situation_castling(self.model.is_white_check, self.model.is_black_check)
        if self.model.board[from_pos[0]][from_pos[1]] is None:
            self.movement_selected.clear()
            return self.model.get_state(), self.model.reward, self.model.checkmate or self.model.stalemate, {}
        moves = self.model.board[from_pos[0]][from_pos[1]].get_all_valid_moves(
            self.model.player_side == "white",
            self.model.initial_move,
            self.model.board[to_pos[0]][to_pos[1]],
            self.model)
        if to_pos not in moves:
            return self.model.get_state(), self.model.reward, self.model.checkmate or self.model.stalemate, {}
        piece = self.model.board[from_pos[0]][from_pos[1]]
        to_piece = None if self.model.board[to_pos[0]][to_pos[1]] is None else copy.deepcopy(
            self.model.board[to_pos[0]][to_pos[1]])
        self.model.reward += self.model.calculate_move_reward(to_piece) * self.model.calculate_coef()
        if self.model.board[to_pos[0]][to_pos[1]] is None or (
                self.model.board[from_pos[0]][from_pos[1]].color == "white" and self.model.board[to_pos[0]][
            to_pos[1]].color == "black") or (
                self.model.board[from_pos[0]][from_pos[1]] == "black" and self.model.board[to_pos[0]][
            to_pos[1]].color == "white"):
            self.model.board[to_pos[0]][to_pos[1]], self.model.board[from_pos[0]][from_pos[1]] = \
                self.model.board[from_pos[0]][from_pos[1]], None
        if (((self.model.white_long_castling and piece is not None and piece.color == "white") or
             (
                     self.model.black_long_castling and piece is not None and piece.color == "black")) and piece.type == "king" and
                from_pos[1] - to_pos[1] == 2):
            self.model.castling_done = True
            self.model.board[to_pos[0]][3], self.model.board[from_pos[0]][0] = \
                self.model.board[from_pos[0]][0], None
            self.model.board[to_pos[0]][3].move((to_pos[0], 3))
            self.model.reward += self.model.castling_reward * self.model.calculate_coef()
        if (((self.model.white_short_castling and piece is not None and piece.color == "white") or
             (
                     self.model.black_short_castling and piece is not None and piece.color == "black")) and piece.type == "king" and
                to_pos[1] - from_pos[1] == 2):
            self.model.castling_done = True
            self.model.board[to_pos[0]][5], self.model.board[from_pos[0]][7] = \
                self.model.board[from_pos[0]][7], None
            self.model.board[to_pos[0]][5].move((to_pos[0], 5))
            self.model.reward += self.model.castling_reward * self.model.calculate_coef()
        self.model.board[to_pos[0]][to_pos[1]].move(to_pos)
        piece = self.model.board[to_pos[0]][to_pos[1]]
        if piece is not None and piece.color == "white" and piece.type == "king":
            self.model.white_king_location = (to_pos[0], to_pos[1])
        elif piece is not None and piece.color == "black" and piece.type == "king":
            self.model.black_king_location = (to_pos[0], to_pos[1])
        self.model.is_white_check = self.model.get_check_situation_white(self.model.player_side == "white",
                                                                         self.model.initial_move,
                                                                         self.model.board[to_pos[0]][to_pos[1]],
                                                                         self.model)
        self.model.is_black_check = self.model.get_check_situation_black(self.model.player_side == "white",
                                                                         self.model.initial_move,
                                                                         self.model.board[to_pos[0]][to_pos[1]],
                                                                         self.model)
        self.model.is_white_stalemate = self.model.get_stalemate_situation_white(self.model.player_side == "white",
                                                                                 self.model.initial_move,
                                                                                 self.model.board[to_pos[0]][to_pos[1]],
                                                                                 self.model)
        self.model.is_black_stalemate = self.model.get_stalemate_situation_black(self.model.player_side == "white",
                                                                                 self.model.initial_move,
                                                                                 self.model.board[to_pos[0]][to_pos[1]],
                                                                                 self.model)

        self.model.reward += self.model.calculate_check_reward() * self.model.calculate_coef_check()
        if self.model.is_white_check and not self.model.white_moves or self.model.is_black_check and self.model.white_moves:
            self.model.checkmate = True
            print("Checkmate:", self.model.checkmate)
            self.model.reward += self.model.calculate_checkmate_reward()
            self.running = False
            return self.model.get_state(), self.model.reward, self.model.checkmate or self.model.stalemate, {}
        elif self.model.is_white_stalemate and not self.model.is_white_check or self.model.is_black_stalemate and not self.model.is_black_check:
            self.model.stalemate = True
            print("Stalemate:", self.model.stalemate)
            self.running = False
            return self.model.get_state(), self.model.reward, self.model.checkmate or self.model.stalemate, {}

        self.model.check_situation_pawn_promotion()
        self.view.draw_game()
        self.model.white_moves = not self.model.white_moves
        self.model.initial_move = False
        self.view.clock.tick(ViewConfig.MAX_FPS)
        p.display.flip()
        return self.model.get_state(), self.model.reward, self.model.checkmate or self.model.stalemate, {}

    def simulate(self, model, action):
        from_pos, to_pos = action
        self.model_trace.append(copy.deepcopy(self.model))
        self.model = model
        self.model.check_situation_castling(self.model.is_white_check, self.model.is_black_check)
        if self.model.board[from_pos[0]][from_pos[1]] is None:
            self.movement_selected.clear()
            return copy.deepcopy(self.model)
        moves = self.model.board[from_pos[0]][from_pos[1]].get_all_valid_moves(
            self.model.player_side == "white",
            self.model.initial_move,
            self.model.board[to_pos[0]][to_pos[1]],
            self.model)
        if to_pos not in moves:
            return copy.deepcopy(self.model)
        piece = self.model.board[from_pos[0]][from_pos[1]]
        to_piece = None if self.model.board[to_pos[0]][to_pos[1]] is None else copy.deepcopy(
            self.model.board[to_pos[0]][to_pos[1]])
        self.model.reward += self.model.calculate_move_reward(to_piece) * self.model.calculate_coef()
        if self.model.board[to_pos[0]][to_pos[1]] is None or (
                self.model.board[from_pos[0]][from_pos[1]].color == "white" and self.model.board[to_pos[0]][
            to_pos[1]].color == "black") or (
                self.model.board[from_pos[0]][from_pos[1]] == "black" and self.model.board[to_pos[0]][
            to_pos[1]].color == "white"):
            self.model.board[to_pos[0]][to_pos[1]], self.model.board[from_pos[0]][from_pos[1]] = \
                self.model.board[from_pos[0]][from_pos[1]], None
        if (((self.model.white_long_castling and piece is not None and piece.color == "white") or
             (
                     self.model.black_long_castling and piece is not None and piece.color == "black")) and piece.type == "king" and
                from_pos[1] - to_pos[1] == 2):
            self.model.castling_done = True
            self.model.board[to_pos[0]][3], self.model.board[from_pos[0]][0] = \
                self.model.board[from_pos[0]][0], None
            self.model.board[to_pos[0]][3].move((to_pos[0], 3))
            self.model.reward += self.model.castling_reward * self.model.calculate_coef()
        if (((self.model.white_short_castling and piece is not None and piece.color == "white") or
             (
                     self.model.black_short_castling and piece is not None and piece.color == "black")) and piece.type == "king" and
                to_pos[1] - from_pos[1] == 2):
            self.model.castling_done = True
            self.model.board[to_pos[0]][5], self.model.board[from_pos[0]][7] = \
                self.model.board[from_pos[0]][7], None
            self.model.board[to_pos[0]][5].move((to_pos[0], 5))
            self.model.reward += self.model.castling_reward * self.model.calculate_coef()
        self.model.board[to_pos[0]][to_pos[1]].move(to_pos)
        piece = self.model.board[to_pos[0]][to_pos[1]]
        if piece is not None and piece.color == "white" and piece.type == "king":
            self.model.white_king_location = (to_pos[0], to_pos[1])
        elif piece is not None and piece.color == "black" and piece.type == "king":
            self.model.black_king_location = (to_pos[0], to_pos[1])
        self.model.is_white_check = self.model.get_check_situation_white(self.model.player_side == "white",
                                                                         self.model.initial_move,
                                                                         self.model.board[to_pos[0]][to_pos[1]],
                                                                         self.model)
        self.model.is_black_check = self.model.get_check_situation_black(self.model.player_side == "white",
                                                                         self.model.initial_move,
                                                                         self.model.board[to_pos[0]][to_pos[1]],
                                                                         self.model)
        self.model.is_white_stalemate = self.model.get_stalemate_situation_white(self.model.player_side == "white",
                                                                                 self.model.initial_move,
                                                                                 self.model.board[to_pos[0]][to_pos[1]],
                                                                                 self.model)
        self.model.is_black_stalemate = self.model.get_stalemate_situation_black(self.model.player_side == "white",
                                                                                 self.model.initial_move,
                                                                                 self.model.board[to_pos[0]][to_pos[1]],
                                                                                 self.model)
        self.model.reward += self.model.calculate_check_reward() * self.model.calculate_coef_check()
        if self.model.is_white_check and not self.model.white_moves or self.model.is_black_check and self.model.white_moves:
            self.model.checkmate = True
            self.model.reward += self.model.calculate_checkmate_reward()
            self.running = False
            return copy.deepcopy(self.model)
        elif self.model.is_white_stalemate and not self.model.is_white_check or self.model.is_black_stalemate and not self.model.is_black_check:
            self.model.stalemate = True
            self.running = False
            return copy.deepcopy(self.model)

        self.model.check_situation_pawn_promotion()
        self.view.draw_game()
        self.model.white_moves = not self.model.white_moves
        self.model.initial_move = False
        self.view.clock.tick(ViewConfig.MAX_FPS)
        p.display.flip()
        return copy.deepcopy(self.model)

    def random_action(self):
        return random.choice(self.model.generate_all_valid_moves()[0])
