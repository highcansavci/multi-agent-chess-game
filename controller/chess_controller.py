import random
import sys

sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")
import pygame as p
from model.chess_components.board import Board
from view.chess_components.chess_board import ChessScreen
from view.config.view_config import ViewConfig
import copy


class ChessController:
    def __init__(self, model: Board, view: ChessScreen):
        self.model = model
        self.view = view

    def check_quit_game(self, event):
        if event.type == p.QUIT:
            self.model.running = False
        elif event.type == p.KEYDOWN:
            if event.key == p.K_ESCAPE:
                self.model.running = False

    def reset(self):
        self.model.initialize_board()
        self.model.move_count = 0
        self.view.draw_game(self.model)
        return self.model
    
    def reset_optimized(self):
        self.model.initialize_board()
        self.model.move_count = 0
        return self.model

    def step(self, model, action, sophisticated_sampling=True):
        """
        Executes a move in the chess game, checking for checkmate/stalemate before performing the action.
        """
        from_pos, to_pos = action
        model.check_situation_castling(model.is_white_check, model.is_black_check)

        # Update king location    
        model.update_white_king_location()
        model.update_black_king_location()
        
        # Check if the selected piece exists
        if model.board[from_pos[0]][from_pos[1]] is None:
            model.movement_selected.clear()
            return model.reward, model.checkmate or model.stalemate, {}, None

        piece = model.board[from_pos[0]][from_pos[1]]
        
        # Generate all valid moves for the selected piece
        moves = piece.get_all_valid_moves(
            model.player_side == "white", model.initial_move, model.board[to_pos[0]][to_pos[1]], model)
        
        if to_pos not in moves:
            return model.reward, model.checkmate or model.stalemate, {}, None
        
        # Check if this move would result in checkmate
        would_be_in_check = (
            model.get_check_situation_black(model.player_side == "white", model.initial_move, None, model)
            if piece.color == "white"
            else model.get_check_situation_white(model.player_side == "white", model.initial_move, None, model)
        )

        result_action = (from_pos, to_pos)  # Store original action

        if would_be_in_check:
            # Explore moves to capture attacking pieces, block check, or move the king to safety
            alternative_moves, move_scores = model.explore_attacker_capture(model, piece, from_pos)

            if alternative_moves:
                # Use learning-driven selection for the best move
                if sophisticated_sampling and move_scores:
                    total_score = sum(move_scores)
                    if total_score > 0:
                        probabilities = [score / total_score for score in move_scores]
                        chosen_idx = random.choices(range(len(alternative_moves)), weights=probabilities)[0]
                    else:
                        chosen_idx = random.randint(0, len(alternative_moves) - 1)
                else:
                    chosen_idx = random.randint(0, len(alternative_moves) - 1)

                piece = alternative_moves[chosen_idx][0]
                from_pos = alternative_moves[chosen_idx][1]
                to_pos = alternative_moves[chosen_idx][2]
                result_action = (from_pos, to_pos)  # Update result action
            else:
                # No safe moves available, declare checkmate
                model.checkmate = True
                if model.is_white_check and model.player_side == "white" or model.is_black_check and model.player_side == "black":
                    model.reward = 1
                else:
                    model.reward = -1
                model.running = False
                return model.reward, True, {"checkmate": True}, result_action
                
        # Proceed with the actual move
        captured_piece = model.board[to_pos[0]][to_pos[1]]
        
        # Make the move
        if captured_piece is None or captured_piece.type != "king":
            model.board[to_pos[0]][to_pos[1]] = piece
            model.board[from_pos[0]][from_pos[1]] = None
        
        # Handle castling
        if piece.type == "king" and abs(from_pos[1] - to_pos[1]) == 2:
            # Check if castling is actually allowed based on check_situation_castling results
            is_allowed = False
            is_long_castling = to_pos[1] == 2
            king_row = to_pos[0]
            
            if piece.color == "white":
                if is_long_castling and model.white_long_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [2, 3]:  # Check squares the king moves through
                        # Create a temporary board state
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None  # Remove king from original position
                        temp_board[king_row][col] = piece  # Place king on passing square
                        
                        # Check if this position would put king in check
                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)
                    
                    if not threatened:
                        is_allowed = True
                        model.board[king_row][3], model.board[king_row][0] = model.board[king_row][0], None
                        model.board[king_row][3].move((king_row, 3))
                        
                elif not is_long_castling and model.white_short_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [5, 6]:  # Check squares the king moves through
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None
                        temp_board[king_row][col] = piece
                        
                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)
                    
                    if not threatened:
                        is_allowed = True
                        model.board[king_row][5], model.board[king_row][7] = model.board[king_row][7], None
                        model.board[king_row][5].move((king_row, 5))
            else:  # Black king
                if is_long_castling and model.black_long_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [2, 3]:
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None
                        temp_board[king_row][col] = piece
                        
                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)
                    
                    if not threatened:
                        is_allowed = True
                        model.board[king_row][3], model.board[king_row][0] = model.board[king_row][0], None
                        model.board[king_row][3].move((king_row, 3))
                        
                elif not is_long_castling and model.black_short_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [5, 6]:
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None
                        temp_board[king_row][col] = piece
                        
                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)
                    
                    if not threatened:
                        is_allowed = True
                        model.board[king_row][5], model.board[king_row][7] = model.board[king_row][7], None
                        model.board[king_row][5].move((king_row, 5))
            
            if is_allowed:
                model.castling_done = True
            else:
                # Castling not allowed - revert the king move
                return model.reward, False, {"invalid_castling": True}, None
        
        # Update piece position
        # Make the move
        if captured_piece is None or captured_piece.type != "king":
            piece.move(to_pos)
        
        # Update check status
        model.is_white_check = model.get_check_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_check = model.get_check_situation_black(model.player_side == "white", model.initial_move, None, model)
        model.is_white_stalemate = model.get_stalemate_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_stalemate = model.get_stalemate_situation_black(model.player_side == "white", model.initial_move, None, model)
        
        if (model.is_white_stalemate or model.is_black_stalemate) and not model.is_white_check and not model.is_black_check or model.move_count >= model.MAX_MOVES:
            model.stalemate = True
            model.running = False
            return model.reward, True, {"stalemate": True}, result_action
        
        model.check_situation_pawn_promotion()
        # Switch turns
        model.white_moves = not model.white_moves
        model.move_count += 1
        model.initial_move = False
        return model.reward, model.checkmate or model.stalemate, {}, result_action

    def step_inference(self, model, action, sophisticated_sampling=True):
        """
        Executes a move in the chess game, checking for checkmate/stalemate before performing the action.
        """
        from_pos, to_pos = action
        model.check_situation_castling(model.is_white_check, model.is_black_check)

        # Update king location    
        model.update_white_king_location()
        model.update_black_king_location()
        
        # Check if the selected piece exists
        if model.board[from_pos[0]][from_pos[1]] is None:
            model.movement_selected.clear()
            return model.reward, model.checkmate or model.stalemate, {}, None

        piece = model.board[from_pos[0]][from_pos[1]]
        
        # Generate all valid moves for the selected piece
        moves = piece.get_all_valid_moves(
            model.player_side == "white", model.initial_move, model.board[to_pos[0]][to_pos[1]], model)
        
        if to_pos not in moves:
            return model.reward, model.checkmate or model.stalemate, {}, None

        # Check if this move would result in checkmate
        would_be_in_check = (
            model.get_check_situation_black(model.player_side == "white", model.initial_move, None, model)
            if piece.color == "white"
            else model.get_check_situation_white(model.player_side == "white", model.initial_move, None, model)
        )

        result_action = (from_pos, to_pos)  # Store original action

        if would_be_in_check:
            # Explore moves to capture attacking pieces, block check, or move the king to safety
            alternative_moves, move_scores = model.explore_attacker_capture(model, piece, from_pos)

            if alternative_moves:
                # Use learning-driven selection for the best move
                if sophisticated_sampling and move_scores:
                    total_score = sum(move_scores)
                    if total_score > 0:
                        probabilities = [score / total_score for score in move_scores]
                        chosen_idx = random.choices(range(len(alternative_moves)), weights=probabilities)[0]
                    else:
                        chosen_idx = random.randint(0, len(alternative_moves) - 1)
                else:
                    chosen_idx = random.randint(0, len(alternative_moves) - 1)

                piece = alternative_moves[chosen_idx][0]
                from_pos = alternative_moves[chosen_idx][1]
                to_pos = alternative_moves[chosen_idx][2]
                result_action = (from_pos, to_pos)  # Update result action
            else:
                # No safe moves available, declare checkmate
                model.checkmate = True
                if model.is_white_check and model.player_side == "white" or model.is_black_check and model.player_side == "black":
                    model.reward = 1
                else:
                    model.reward = -1
                model.running = False
                return model.reward, True, {"checkmate": True}, result_action

        # Proceed with the actual move
        captured_piece = model.board[to_pos[0]][to_pos[1]]

        # Make the move
        if captured_piece is None or captured_piece.type != "king":
            model.board[to_pos[0]][to_pos[1]] = piece
            model.board[from_pos[0]][from_pos[1]] = None

        # Handle castling
        if piece.type == "king" and abs(from_pos[1] - to_pos[1]) == 2:
            # Check if castling is actually allowed based on check_situation_castling results
            is_allowed = False
            is_long_castling = to_pos[1] == 2
            king_row = to_pos[0]

            if piece.color == "white":
                if is_long_castling and model.white_long_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [2, 3]:  # Check squares the king moves through
                        # Create a temporary board state
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None  # Remove king from original position
                        temp_board[king_row][col] = piece  # Place king on passing square

                        # Check if this position would put king in check
                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)

                    if not threatened:
                        is_allowed = True
                        model.board[king_row][3], model.board[king_row][0] = model.board[king_row][0], None
                        model.board[king_row][3].move((king_row, 3))

                elif not is_long_castling and model.white_short_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [5, 6]:  # Check squares the king moves through
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None
                        temp_board[king_row][col] = piece

                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)

                    if not threatened:
                        is_allowed = True
                        model.board[king_row][5], model.board[king_row][7] = model.board[king_row][7], None
                        model.board[king_row][5].move((king_row, 5))
            else:  # Black king
                if is_long_castling and model.black_long_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [2, 3]:
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None
                        temp_board[king_row][col] = piece

                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)

                    if not threatened:
                        is_allowed = True
                        model.board[king_row][3], model.board[king_row][0] = model.board[king_row][0], None
                        model.board[king_row][3].move((king_row, 3))

                elif not is_long_castling and model.black_short_castling:
                    # Check if squares between king and rook are threatened
                    threatened = False
                    for col in [5, 6]:
                        temp_board = copy.deepcopy(model.board)
                        temp_board[king_row][4] = None
                        temp_board[king_row][col] = piece

                        if piece.color == "white":
                            threatened |= model.get_check_situation_black(model.player_side == "white", False, temp_board, model)
                        else:
                            threatened |= model.get_check_situation_white(model.player_side == "white", False, temp_board, model)

                    if not threatened:
                        is_allowed = True
                        model.board[king_row][5], model.board[king_row][7] = model.board[king_row][7], None
                        model.board[king_row][5].move((king_row, 5))

            if is_allowed:
                model.castling_done = True
            else:
                # Castling not allowed - revert the king move
                return model.reward, False, {"invalid_castling": True}, None

        # Update piece position
        # Make the move
        if captured_piece is None or captured_piece.type != "king":
            piece.move(to_pos)

        # Update check status
        model.is_white_check = model.get_check_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_check = model.get_check_situation_black(model.player_side == "white", model.initial_move, None, model)
        model.is_white_stalemate = model.get_stalemate_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_stalemate = model.get_stalemate_situation_black(model.player_side == "white", model.initial_move, None, model)

        if (model.is_white_stalemate or model.is_black_stalemate) and not model.is_white_check and not model.is_black_check or model.move_count >= model.MAX_MOVES:
            model.stalemate = True
            model.running = False
            return model.reward, True, {"stalemate": True}, result_action

        model.check_situation_pawn_promotion()
        self.view.draw_game(model)
        # Switch turns
        model.white_moves = not model.white_moves
        model.move_count += 1
        model.initial_move = False
        self.view.clock.tick(ViewConfig.MAX_FPS)
        p.display.flip()
        return model.reward, model.checkmate or model.stalemate, {}, result_action
    
    def random_action(self):
        return random.choice(self.model.generate_all_valid_moves(self.model)[0])
