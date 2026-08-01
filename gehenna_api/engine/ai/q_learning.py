"""Q-Learning Agent for V:TES bots.

This module implements a Q-Learning agent that learns to play V:TES
through self-play and experience replay.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QState:
    """Represents a game state as a tuple of features."""
    
    # Basic state
    pool_ratio: float  # Our pool / 30
    prey_pool_ratio: float  # Prey pool / 30
    predator_pool_ratio: float  # Predator pool / 30
    own_threat: float  # Our threat level (0-10)
    prey_threat: float  # Prey threat level (0-10)
    predator_threat: float  # Predator threat level (0-10)
    phase: float  # Game phase (0=early, 1=final)
    minion_count: int  # Number of ready minions
    hand_size: int  # Cards in hand
    has_bleed_card: int  # Has bleed card (0/1)
    has_defense_card: int  # Has defense card (0/1)
    has_rush_card: int  # Has rush card (0/1)
    
    # New features: Combat module
    prey_combat_module: int  # 0=balanced, 1=defensive, 2=aggressive
    predator_combat_module: int  # 0=balanced, 1=defensive, 2=aggressive
    
    # New features: Reaction capabilities
    prey_bounce_prob: float  # Probability prey has bounce (0-1)
    predator_bounce_prob: float  # Probability predator has bounce (0-1)
    prey_intercept_prob: float  # Probability prey has intercept (0-1)
    predator_intercept_prob: float  # Probability predator has intercept (0-1)
    
    # New features: Card probabilities
    prey_combat_ends_prob: float  # Probability prey has combat ends (0-1)
    predator_combat_ends_prob: float  # Probability predator has combat ends (0-1)
    prey_aggravated_prob: float  # Probability prey has aggravated (0-1)
    predator_aggravated_prob: float  # Probability predator has aggravated (0-1)
    
    def to_tuple(self) -> tuple:
        """Convert to hashable tuple for Q-table."""
        return (
            round(self.pool_ratio, 2),
            round(self.prey_pool_ratio, 2),
            round(self.predator_pool_ratio, 2),
            round(self.own_threat, 1),
            round(self.prey_threat, 1),
            round(self.predator_threat, 1),
            round(self.phase, 2),
            min(self.minion_count, 6),
            min(self.hand_size, 7),
            self.has_bleed_card,
            self.has_defense_card,
            self.has_rush_card,
            self.prey_combat_module,
            self.predator_combat_module,
            round(self.prey_bounce_prob, 2),
            round(self.predator_bounce_prob, 2),
            round(self.prey_intercept_prob, 2),
            round(self.predator_intercept_prob, 2),
            round(self.prey_combat_ends_prob, 2),
            round(self.predator_combat_ends_prob, 2),
            round(self.prey_aggravated_prob, 2),
            round(self.predator_aggravated_prob, 2),
        )
    
    @classmethod
    def from_tuple(cls, data: tuple) -> 'QState':
        """Create QState from tuple."""
        return cls(
            pool_ratio=data[0],
            prey_pool_ratio=data[1],
            predator_pool_ratio=data[2],
            own_threat=data[3],
            prey_threat=data[4],
            predator_threat=data[5],
            phase=data[6],
            minion_count=data[7],
            hand_size=data[8],
            has_bleed_card=data[9],
            has_defense_card=data[10],
            has_rush_card=data[11],
            prey_combat_module=data[12],
            predator_combat_module=data[13],
            prey_bounce_prob=data[14],
            predator_bounce_prob=data[15],
            prey_intercept_prob=data[16],
            predator_intercept_prob=data[17],
            prey_combat_ends_prob=data[18],
            predator_combat_ends_prob=data[19],
            prey_aggravated_prob=data[20],
            predator_aggravated_prob=data[21],
        )


# Actions available to the bot
ACTIONS = [
    'bleed',      # 0: Bleed prey
    'rush',       # 1: Rush with ally
    'control',    # 2: Control action
    'bloat',      # 3: Gain pool
    'stealth',    # 4: Play stealth
    'recruit',    # 5: Recruit ally
    'pass',       # 6: Do nothing
]

NUM_ACTIONS = len(ACTIONS)


class QLearningAgent:
    """Q-Learning agent for V:TES.
    
    Uses Q-Learning to learn optimal actions based on game state.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        exploration_rate: float = 0.3,
        exploration_decay: float = 0.995,
        min_exploration: float = 0.01,
    ):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.min_exploration = min_exploration
        
        # Q-table: state -> [q_value for each action]
        self.q_table: dict[tuple, list[float]] = {}
        
        # Replay buffer for training
        self.replay_buffer: list[dict] = []
        self.max_buffer_size = 10000
        
        # Statistics
        self.games_played = 0
        self.total_rewards = 0.0
    
    def get_q_values(self, state: QState) -> list[float]:
        """Get Q-values for a state."""
        key = state.to_tuple()
        if key not in self.q_table:
            # Initialize with small random values
            self.q_table[key] = [random.uniform(-0.1, 0.1) for _ in range(NUM_ACTIONS)]
        return self.q_table[key]
    
    def choose_action(self, state: QState) -> str:
        """Choose action using ε-greedy policy."""
        # Explore with probability ε
        if random.random() < self.exploration_rate:
            return random.choice(ACTIONS)
        
        # Exploit: choose best action
        q_values = self.get_q_values(state)
        best_idx = max(range(NUM_ACTIONS), key=lambda i: q_values[i])
        return ACTIONS[best_idx]
    
    def update(
        self,
        state: QState,
        action: str,
        reward: float,
        next_state: QState,
        done: bool = False,
    ) -> None:
        """Update Q-value using Q-Learning formula."""
        key = state.to_tuple()
        next_key = next_state.to_tuple()
        
        # Get current Q-value
        q_values = self.get_q_values(state)
        action_idx = ACTIONS.index(action)
        current_q = q_values[action_idx]
        
        # Calculate target Q-value
        if done:
            target_q = reward
        else:
            next_q_values = self.get_q_values(next_state)
            max_next_q = max(next_q_values)
            target_q = reward + self.discount_factor * max_next_q
        
        # Update Q-value
        new_q = current_q + self.learning_rate * (target_q - current_q)
        self.q_table[key][action_idx] = new_q
        
        # Store in replay buffer
        self._store_experience(state, action, reward, next_state, done)
    
    def _store_experience(
        self,
        state: QState,
        action: str,
        reward: float,
        next_state: QState,
        done: bool,
    ) -> None:
        """Store experience in replay buffer."""
        experience = {
            'state': state.to_tuple(),
            'action': action,
            'reward': reward,
            'next_state': next_state.to_tuple(),
            'done': done,
        }
        self.replay_buffer.append(experience)
        
        # Trim buffer if needed
        if len(self.replay_buffer) > self.max_buffer_size:
            self.replay_buffer.pop(0)
    
    def decay_exploration(self) -> None:
        """Decay exploration rate."""
        self.exploration_rate = max(
            self.min_exploration,
            self.exploration_rate * self.exploration_decay
        )
    
    def train_on_buffer(self, batch_size: int = 32) -> float:
        """Train on random batch from replay buffer."""
        if len(self.replay_buffer) < batch_size:
            return 0.0
        
        batch = random.sample(self.replay_buffer, batch_size)
        total_loss = 0.0
        
        for experience in batch:
            state = QState.from_tuple(experience['state'])
            action = experience['action']
            reward = experience['reward']
            next_state = QState.from_tuple(experience['next_state'])
            done = experience['done']
            
            # Calculate loss
            q_values = self.get_q_values(state)
            action_idx = ACTIONS.index(action)
            current_q = q_values[action_idx]
            
            if done:
                target_q = reward
            else:
                next_q_values = self.get_q_values(next_state)
                max_next_q = max(next_q_values)
                target_q = reward + self.discount_factor * max_next_q
            
            loss = (target_q - current_q) ** 2
            total_loss += loss
            
            # Update
            self.update(state, action, reward, next_state, done)
        
        return total_loss / batch_size
    
    def save(self, filepath: str) -> None:
        """Save Q-table to file."""
        data = {
            'q_table': {str(k): v for k, v in self.q_table.items()},
            'exploration_rate': self.exploration_rate,
            'games_played': self.games_played,
            'total_rewards': self.total_rewards,
            'hyperparams': {
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor,
                'exploration_decay': self.exploration_decay,
                'min_exploration': self.min_exploration,
            },
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str) -> None:
        """Load Q-table from file."""
        path = Path(filepath)
        if not path.exists():
            return
        
        with open(path) as f:
            data = json.load(f)
        
        # Restore Q-table
        self.q_table = {
            eval(k): v for k, v in data.get('q_table', {}).items()
        }
        
        # Restore hyperparameters
        self.exploration_rate = data.get('exploration_rate', self.exploration_rate)
        self.games_played = data.get('games_played', 0)
        self.total_rewards = data.get('total_rewards', 0.0)
        
        hyperparams = data.get('hyperparams', {})
        self.learning_rate = hyperparams.get('learning_rate', self.learning_rate)
        self.discount_factor = hyperparams.get('discount_factor', self.discount_factor)
        self.exploration_decay = hyperparams.get('exploration_decay', self.exploration_decay)
        self.min_exploration = hyperparams.get('min_exploration', self.min_exploration)
    
    def get_stats(self) -> dict:
        """Get agent statistics."""
        return {
            'q_table_size': len(self.q_table),
            'replay_buffer_size': len(self.replay_buffer),
            'exploration_rate': self.exploration_rate,
            'games_played': self.games_played,
            'total_rewards': self.total_rewards,
        }
