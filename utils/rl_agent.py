import numpy as np
from dotenv import load_dotenv
import os
load_dotenv()

class QLearningAgent:
    def __init__(self, actions=3, learning_rate=0.1, discount_factor=0.9, exploration_rate=0.1):
        self.q_table = {}
        self.actions = actions
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate

    def get_action(self, state):
        state_key = str(state)
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.actions)
        if np.random.rand() < self.exploration_rate:
            return np.random.randint(self.actions)
        return np.argmax(self.q_table[state_key])

    def update_q_table(self, state, action, reward, next_state):
        state_key = str(state)
        next_state_key = str(next_state)
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.actions)
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = np.zeros(self.actions)
        current_q = self.q_table[state_key][action]
        next_max_q = np.max(self.q_table[next_state_key])
        self.q_table[state_key][action] = current_q + self.learning_rate * (reward + self.discount_factor * next_max_q - current_q)
