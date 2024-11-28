import copy
import math
import random

import numpy as np
import sys
from model.chess_components.board import Board
sys.path.append("../..")
sys.path.append("../../..")
sys.path.append("../../../..")
from gym_wrapper.environment import ChessGym


class Node:
    def __init__(self, env: ChessGym, state: Board, parent=None, action_taken=None, prior=1, visit_count=0):
        self.env = env
        self.state = state
        self.parent = parent
        self.action_taken = action_taken
        self.prior = prior
        self.children = []

        self.visit_count = visit_count
        self.value_sum = 0
        self.eps = 1
        self.C = 2

    def is_fully_expanded(self):
        return len(self.children) > 0

    def select(self):
        ucbs = np.array([self.get_ucb(child) for child in self.children], dtype=np.float32)
        ucbs /= np.sum(ucbs)
        return np.random.choice(self.children, 1, p=ucbs)[0]

    def get_ucb(self, child):
        q_value = 1 - (child.value_sum / (child.visit_count + self.eps) + 1) / 2
        return q_value + self.C * math.sqrt(math.log(self.visit_count) / (child.visit_count + self.eps)) * self.prior

    def expand(self, policy):
        for action, prob in enumerate(policy):
            if prob > 0:
                state = copy.deepcopy(self.state)
                self.env.step(state, ((action // 64 // 8, action // 64 % 8), ((action % 64) // 8, (action % 64) % 8)))
                next_state = self.env.change_perspective([state])[0]
                child = Node(self.env, next_state, self, action, prob)
                self.children.append(child)

    def backpropagate(self, value):
        self.value_sum += value
        self.visit_count += 1

        value = -value
        if self.parent is not None:
            self.parent.backpropagate(value)


