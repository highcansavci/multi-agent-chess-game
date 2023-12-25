from abc import ABC


class BasePiece(ABC):
    def __init__(self, initial_position):
        self.position_x, self.position_y = initial_position
        self.color = None
        self.type = None
        self.is_moved = False
        self.reward = 0
        self.state = []

    def get_position(self):
        return self.position_x, self.position_y

    def get_color(self):
        return self.color

    def get_type(self):
        return self.type

    def get_reward(self):
        return self.reward

    def get_state(self):
        return self.state

    def get_all_possible_moves(self, player_is_white, initial_move, target_piece, model):
        pass

    def get_all_valid_moves(self, player_is_white, initial_move, target_piece, model):
        pass

    def check_control(self, player_is_white, initial_move, target_piece, model):
        pass

    def move(self, position):
        self.position_x, self.position_y = position
        self.is_moved = True
