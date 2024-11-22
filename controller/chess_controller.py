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

    def start_game(self):
        p.init()
        while self.model.running:
            for e in p.event.get():
                self.check_quit_game(e)
                self.check_movement(e)
            self.view.clock.tick(ViewConfig.MAX_FPS)
            p.display.flip()

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

    def check_movement(self, event):
        if event.type == p.MOUSEBUTTONDOWN:
            location = p.mouse.get_pos()
            column = location[0] // ViewConfig.SQ_SIZE
            row = location[1] // ViewConfig.SQ_SIZE
            self.model.movement_selected.append((row, column))
            if len(self.movement_selected) == 2:
                self.move_piece()
                self.model.movement_selected.clear()

    
    def move_piece(self, action):
        model = self.model
        from_pos, to_pos = action
        model.check_situation_castling(model.is_white_check, model.is_black_check)
        
        # Check if the selected piece exists
        if model.board[from_pos[0]][from_pos[1]] is None:
            model.movement_selected.clear()
            return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}

        # Generate all valid moves for the selected piece
        moves = model.board[from_pos[0]][from_pos[1]].get_all_valid_moves(
            model.player_side == "white", model.initial_move, model.board[to_pos[0]][to_pos[1]], model)
        
        if to_pos not in moves:
            # If the target position is not a valid move, return without changes
            return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}

        # Process the move and update reward
        piece = model.board[from_pos[0]][from_pos[1]]
        captured_piece = model.board[to_pos[0]][to_pos[1]]
        if model.player_side == "white":
            model.white_reward += model.calculate_move_reward(captured_piece)
        else:
            model.black_reward += model.calculate_move_reward(captured_piece)
        
        # Move the piece
        model.board[to_pos[0]][to_pos[1]], model.board[from_pos[0]][from_pos[1]] = piece, None
        
        # Update king location if moved
        if piece.type == "king":
            if piece.color == "white":
                model.white_king_location = to_pos
            else:
                model.black_king_location = to_pos
        
        # Handle castling
        if piece.type == "king" and abs(from_pos[1] - to_pos[1]) == 2:
            if to_pos[1] == 2:  # Long castling
                model.board[to_pos[0]][3], model.board[to_pos[0]][0] = model.board[to_pos[0]][0], None
                model.board[to_pos[0]][3].move((to_pos[0], 3))
            elif to_pos[1] == 6:  # Short castling
                model.board[to_pos[0]][5], model.board[to_pos[0]][7] = model.board[to_pos[0]][7], None
                model.board[to_pos[0]][5].move((to_pos[0], 5))
            model.castling_done = True
            if model.player_side == "white":
                model.white_reward += model.castling_reward
            else:
                model.black_reward += model.castling_reward
        
        # Move the piece and update check/checkmate/stalemate status
        piece.move(to_pos)

        # Update check, checkmate, and stalemate statuses for both players
        model.is_white_check = model.get_check_situation_white()
        model.is_black_check = model.get_check_situation_black()
        model.is_white_stalemate = model.get_stalemate_situation_white()
        model.is_black_stalemate = model.get_stalemate_situation_black()

        # Calculate reward for check or checkmate
        if model.is_white_check or model.is_black_check:
            if model.player_side == "white":
                model.white_reward += model.calculate_check_reward()
            else:
                model.black_reward += model.calculate_check_reward()

        # Determine if there is checkmate or stalemate
        if (model.is_white_check and not model.white_moves) or (model.is_black_check and model.white_moves):
            if not model.has_legal_moves():
                model.checkmate = True
                if model.player_side == "white":
                    model.white_reward += model.calculate_checkmate_reward()
                else:
                    model.black_reward += model.calculate_checkmate_reward()
                model.running = False
                return model.white_reward, model.black_reward, True, {}  # Checkmate

        elif (model.is_white_stalemate or model.is_black_stalemate) and not model.is_white_check and not model.is_black_check:
            if not model.has_legal_moves():
                model.stalemate = True
                model.running = False
                return model.white_reward, model.black_reward, True, {}  # Stalemate

        self.view.draw_game(model)
        
        # Toggle the active player and update the frame
        model.white_moves = not model.white_moves
        model.initial_move = False
        self.view.clock.tick(ViewConfig.MAX_FPS)
        p.display.flip()

        return model, model.reward, model.checkmate or model.stalemate, {}

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
            return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}, None

        piece = model.board[from_pos[0]][from_pos[1]]
        
        # Generate all valid moves for the selected piece
        moves = piece.get_all_valid_moves(
            model.player_side == "white", model.initial_move, model.board[to_pos[0]][to_pos[1]], model)
        
        if to_pos not in moves:
            return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}, None
        
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
                if model.is_white_check:
                    model.white_reward += model.calculate_checkmate_reward()
                else:
                    model.black_reward += model.calculate_checkmate_reward()
                model.running = False
                return model.white_reward, model.black_reward, True, {"checkmate": True}, None
                
        # Proceed with the actual move
        captured_piece = model.board[to_pos[0]][to_pos[1]]
                
        # Calculate rewards
        if model.white_moves:
            model.white_reward += model.calculate_move_reward(captured_piece)
        else:
            model.black_reward += model.calculate_move_reward(captured_piece)
        
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
                if model.white_moves:
                    model.white_reward += model.castling_reward
                else:
                    model.black_reward += model.castling_reward
            else:
                # Castling not allowed - revert the king move
                return model.white_reward, model.black_reward, False, {"invalid_castling": True}, None
        
        # Update piece position
        # Make the move
        if captured_piece is None or captured_piece.type != "king":
            piece.move(to_pos)
        
        # Update check status
        model.is_white_check = model.get_check_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_check = model.get_check_situation_black(model.player_side == "white", model.initial_move, None, model)
        model.is_white_stalemate = model.get_stalemate_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_stalemate = model.get_stalemate_situation_black(model.player_side == "white", model.initial_move, None, model)
        
        # Handle check rewards
        if model.is_white_check or model.is_black_check:
            if model.white_moves:
                model.white_reward += model.calculate_check_reward()
            else:
                model.black_reward += model.calculate_check_reward()
        
        
        if (model.is_white_stalemate or model.is_black_stalemate) and not model.is_white_check and not model.is_black_check or model.move_count >= model.MAX_MOVES:
            model.stalemate = True
            model.running = False
            return model.white_reward, model.black_reward, True, {"stalemate": True}, result_action
        
        model.check_situation_pawn_promotion()
        # Switch turns
        model.white_moves = not model.white_moves
        model.move_count += 1
        model.initial_move = False
        return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}, result_action

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
            return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}, None

        piece = model.board[from_pos[0]][from_pos[1]]
        
        # Generate all valid moves for the selected piece
        moves = piece.get_all_valid_moves(
            model.player_side == "white", model.initial_move, model.board[to_pos[0]][to_pos[1]], model)
        
        if to_pos not in moves:
            return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}, None

        # Create a temporary board state to test the move
        temp_board = copy.deepcopy(model.board)
        temp_piece = temp_board[from_pos[0]][from_pos[1]]
        
        # Make the move on temporary board
        temp_board[to_pos[0]][to_pos[1]] = temp_piece
        temp_board[from_pos[0]][from_pos[1]] = None
        
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
                model.checkmate = True
                if model.is_white_check:
                    model.white_reward += model.calculate_checkmate_reward()
                else:
                    model.black_reward += model.calculate_checkmate_reward()
                model.running = False
                return model.white_reward, model.black_reward, True, {"checkmate": True}, None
                
        # Proceed with the actual move
        captured_piece = model.board[to_pos[0]][to_pos[1]]
                
        # Calculate rewards
        if model.white_moves:
            model.white_reward += model.calculate_move_reward(captured_piece)
        else:
            model.black_reward += model.calculate_move_reward(captured_piece)
        
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
                if model.white_moves:
                    model.white_reward += model.castling_reward
                else:
                    model.black_reward += model.castling_reward
            else:
                # Castling not allowed - revert the king move
                return model.white_reward, model.black_reward, False, {"invalid_castling": True}, None
        
        # Update piece position
        # Make the move
        if captured_piece is None or captured_piece.type != "king":
            piece.move(to_pos)
        
        # Update check status
        model.is_white_check = model.get_check_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_check = model.get_check_situation_black(model.player_side == "white", model.initial_move, None, model)
        model.is_white_stalemate = model.get_stalemate_situation_white(model.player_side == "white", model.initial_move, None, model)
        model.is_black_stalemate = model.get_stalemate_situation_black(model.player_side == "white", model.initial_move, None, model)
        
        # Handle check rewards
        if model.is_white_check or model.is_black_check:
            if model.white_moves:
                model.white_reward += model.calculate_check_reward()
            else:
                model.black_reward += model.calculate_check_reward()
        
        
        if (model.is_white_stalemate or model.is_black_stalemate) and not model.is_white_check and not model.is_black_check or model.move_count >= model.MAX_MOVES:
            model.stalemate = True
            model.running = False
            return model.white_reward, model.black_reward, True, {"stalemate": True}, result_action
        
        model.check_situation_pawn_promotion()
        self.view.draw_game(model)
        # Switch turns
        model.white_moves = not model.white_moves
        model.move_count += 1
        model.initial_move = False
        self.view.clock.tick(ViewConfig.MAX_FPS)
        p.display.flip()
        return model.white_reward, model.black_reward, model.checkmate or model.stalemate, {}, result_action
    
    def random_action(self):
        return random.choice(self.model.generate_all_valid_moves(self.model)[0])
