"""Reward system for V:TES Q-Learning.

Calculates rewards based on game events and outcomes.
"""

from __future__ import annotations

from gehenna_api.engine.state import GameState


class RewardCalculator:
    """Calculates rewards for Q-Learning based on game events."""
    
    # Base rewards for different events
    REWARDS = {
        'bleed_success': 0.3,      # Successful bleed
        'bleed_blocked': -0.1,     # Bleed was blocked
        'rush_success': 0.2,       # Successful rush
        'rush_blocked': -0.1,      # Rush was blocked
        'control_success': 0.2,    # Successful control action
        'bloat_success': 0.2,      # Gained pool
        'oust': 1.0,               # Ousted prey
        'pool_lost': -0.1,         # Lost pool
        'pool_gained': 0.2,        # Gained pool
        'action_failed': -0.05,    # Action failed
        'no_action': -0.05,        # Turn with no action
    }
    
    # Phase multipliers
    PHASE_MULTIPLIERS = {
        'early': 0.8,   # Focus on setup
        'mid': 1.0,     # Neutral
        'late': 1.2,    # More aggressive
        'final': 1.5,   # Maximum urgency
    }
    
    def __init__(self, state: GameState, player_id: int):
        self.state = state
        self.player_id = player_id
        self.player = state.player_by_id(player_id)
        
        # Track previous state for delta calculations
        self.prev_pool = self.player.pool if self.player else 30
        self.prev_prey_pool = self._get_prey_pool()
    
    def _get_prey_pool(self) -> int:
        """Get prey's current pool."""
        prey = self.state.prey_of(self.player_id)
        return prey.pool if prey else 30
    
    def calculate_reward(
        self,
        action_type: str,
        outcome: str,
        phase: str = 'mid',
    ) -> float:
        """Calculate reward for an action.
        
        Args:
            action_type: Type of action taken (bleed, rush, etc.)
            outcome: Outcome of action (success, blocked, failed)
            phase: Current game phase (early, mid, late, final)
        
        Returns:
            Reward value
        """
        # Get base reward
        reward_key = f'{action_type}_{outcome}'
        base_reward = self.REWARDS.get(reward_key, 0.0)
        
        # Apply phase multiplier
        phase_mult = self.PHASE_MULTIPLIERS.get(phase, 1.0)
        reward = base_reward * phase_mult
        
        # Add pool delta reward
        if self.player:
            pool_delta = self.player.pool - self.prev_pool
            if pool_delta > 0:
                reward += self.REWARDS['pool_gained'] * pool_delta
            elif pool_delta < 0:
                reward += self.REWARDS['pool_lost'] * abs(pool_delta)
            
            # Track for next calculation
            self.prev_pool = self.player.pool
        
        # Add prey pool delta reward
        prey_pool = self._get_prey_pool()
        prey_pool_delta = self.prev_prey_pool - prey_pool
        if prey_pool_delta > 0:
            reward += prey_pool_delta * 0.1  # Reward for damaging prey
        self.prev_prey_pool = prey_pool
        
        return reward
    
    def calculate_oust_reward(self) -> float:
        """Calculate reward for ousting a player."""
        return self.REWARDS['oust']
    
    def calculate_turn_reward(self, action_taken: bool) -> float:
        """Calculate reward for completing a turn."""
        if not action_taken:
            return self.REWARDS['no_action']
        return 0.0
    
    def reset(self) -> None:
        """Reset tracking variables."""
        if self.player:
            self.prev_pool = self.player.pool
        self.prev_prey_pool = self._get_prey_pool()
