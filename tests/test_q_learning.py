"""Tests for Q-Learning agent."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gehenna_api.engine.ai.q_learning import QLearningAgent, QState, ACTIONS


class TestQState:
    """Tests for QState dataclass."""
    
    def test_qstate_creation(self):
        state = QState(
            pool_ratio=0.8,
            prey_pool_ratio=0.6,
            predator_pool_ratio=0.5,
            own_threat=3.0,
            prey_threat=4.0,
            predator_threat=5.0,
            phase=0.5,
            minion_count=2,
            hand_size=5,
            has_bleed_card=1,
            has_defense_card=0,
            has_rush_card=1,
            prey_combat_module=0,
            predator_combat_module=1,
            prey_bounce_prob=0.3,
            predator_bounce_prob=0.2,
            prey_intercept_prob=0.4,
            predator_intercept_prob=0.1,
            prey_combat_ends_prob=0.2,
            predator_combat_ends_prob=0.3,
            prey_aggravated_prob=0.1,
            predator_aggravated_prob=0.2,
        )
        assert state.pool_ratio == 0.8
        assert state.hand_size == 5
        assert state.prey_combat_module == 0
        assert state.predator_bounce_prob == 0.2
    
    def test_qstate_to_tuple(self):
        state = QState(
            pool_ratio=0.8,
            prey_pool_ratio=0.6,
            predator_pool_ratio=0.5,
            own_threat=3.0,
            prey_threat=4.0,
            predator_threat=5.0,
            phase=0.5,
            minion_count=2,
            hand_size=5,
            has_bleed_card=1,
            has_defense_card=0,
            has_rush_card=1,
            prey_combat_module=0,
            predator_combat_module=1,
            prey_bounce_prob=0.3,
            predator_bounce_prob=0.2,
            prey_intercept_prob=0.4,
            predator_intercept_prob=0.1,
            prey_combat_ends_prob=0.2,
            predator_combat_ends_prob=0.3,
            prey_aggravated_prob=0.1,
            predator_aggravated_prob=0.2,
        )
        t = state.to_tuple()
        assert len(t) == 22
        assert isinstance(t, tuple)
    
    def test_qstate_from_tuple(self):
        t = (0.8, 0.6, 0.5, 3.0, 4.0, 5.0, 0.5, 2, 5, 1, 0, 1, 0, 1, 0.3, 0.2, 0.4, 0.1, 0.2, 0.3, 0.1, 0.2)
        state = QState.from_tuple(t)
        assert state.pool_ratio == 0.8
        assert state.hand_size == 5
        assert state.prey_combat_module == 0
        assert state.predator_bounce_prob == 0.2


class TestQLearningAgent:
    """Tests for QLearningAgent."""
    
    def test_agent_creation(self):
        agent = QLearningAgent()
        assert agent.learning_rate == 0.1
        assert agent.discount_factor == 0.9
        assert agent.exploration_rate == 0.3
    
    def test_get_q_values(self):
        agent = QLearningAgent()
        state = QState(
            pool_ratio=0.8,
            prey_pool_ratio=0.6,
            predator_pool_ratio=0.5,
            own_threat=3.0,
            prey_threat=4.0,
            predator_threat=5.0,
            phase=0.5,
            minion_count=2,
            hand_size=5,
            has_bleed_card=1,
            has_defense_card=0,
            has_rush_card=1,
            prey_combat_module=0,
            predator_combat_module=1,
            prey_bounce_prob=0.3,
            predator_bounce_prob=0.2,
            prey_intercept_prob=0.4,
            predator_intercept_prob=0.1,
            prey_combat_ends_prob=0.2,
            predator_combat_ends_prob=0.3,
            prey_aggravated_prob=0.1,
            predator_aggravated_prob=0.2,
        )
        q_values = agent.get_q_values(state)
        assert len(q_values) == len(ACTIONS)
    
    def test_choose_action(self):
        agent = QLearningAgent(exploration_rate=0.0)  # No exploration
        state = QState(
            pool_ratio=0.8,
            prey_pool_ratio=0.6,
            predator_pool_ratio=0.5,
            own_threat=3.0,
            prey_threat=4.0,
            predator_threat=5.0,
            phase=0.5,
            minion_count=2,
            hand_size=5,
            has_bleed_card=1,
            has_defense_card=0,
            has_rush_card=1,
            prey_combat_module=0,
            predator_combat_module=1,
            prey_bounce_prob=0.3,
            predator_bounce_prob=0.2,
            prey_intercept_prob=0.4,
            predator_intercept_prob=0.1,
            prey_combat_ends_prob=0.2,
            predator_combat_ends_prob=0.3,
            prey_aggravated_prob=0.1,
            predator_aggravated_prob=0.2,
        )
        action = agent.choose_action(state)
        assert action in ACTIONS
    
    def test_update_q_values(self):
        agent = QLearningAgent()
        state1 = QState(
            pool_ratio=0.8,
            prey_pool_ratio=0.6,
            predator_pool_ratio=0.5,
            own_threat=3.0,
            prey_threat=4.0,
            predator_threat=5.0,
            phase=0.5,
            minion_count=2,
            hand_size=5,
            has_bleed_card=1,
            has_defense_card=0,
            has_rush_card=1,
            prey_combat_module=0,
            predator_combat_module=1,
            prey_bounce_prob=0.3,
            predator_bounce_prob=0.2,
            prey_intercept_prob=0.4,
            predator_intercept_prob=0.1,
            prey_combat_ends_prob=0.2,
            predator_combat_ends_prob=0.3,
            prey_aggravated_prob=0.1,
            predator_aggravated_prob=0.2,
        )
        state2 = QState(
            pool_ratio=0.7,
            prey_pool_ratio=0.5,
            predator_pool_ratio=0.4,
            own_threat=3.5,
            prey_threat=4.5,
            predator_threat=5.5,
            phase=0.6,
            minion_count=2,
            hand_size=4,
            has_bleed_card=1,
            has_defense_card=0,
            has_rush_card=0,
            prey_combat_module=1,
            predator_combat_module=0,
            prey_bounce_prob=0.4,
            predator_bounce_prob=0.3,
            prey_intercept_prob=0.5,
            predator_intercept_prob=0.2,
            prey_combat_ends_prob=0.3,
            predator_combat_ends_prob=0.4,
            prey_aggravated_prob=0.2,
            predator_aggravated_prob=0.3,
        )
        
        # Get initial Q-value
        initial_q = agent.get_q_values(state1)[0]
        
        # Update
        agent.update(state1, 'bleed', 0.5, state2, done=False)
        
        # Check Q-value changed
        new_q = agent.get_q_values(state1)[0]
        assert new_q != initial_q
    
    def test_save_and_load(self):
        agent = QLearningAgent()
        state = QState(
            pool_ratio=0.8,
            prey_pool_ratio=0.6,
            predator_pool_ratio=0.5,
            own_threat=3.0,
            prey_threat=4.0,
            predator_threat=5.0,
            phase=0.5,
            minion_count=2,
            hand_size=5,
            has_bleed_card=1,
            has_defense_card=0,
            has_rush_card=1,
            prey_combat_module=0,
            predator_combat_module=1,
            prey_bounce_prob=0.3,
            predator_bounce_prob=0.2,
            prey_intercept_prob=0.4,
            predator_intercept_prob=0.1,
            prey_combat_ends_prob=0.2,
            predator_combat_ends_prob=0.3,
            prey_aggravated_prob=0.1,
            predator_aggravated_prob=0.2,
        )
        
        # Train a bit
        for _ in range(10):
            agent.update(state, 'bleed', 0.5, state, done=False)
        
        # Save
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        agent.save(filepath)
        
        # Load into new agent
        new_agent = QLearningAgent()
        new_agent.load(filepath)
        
        # Check Q-values match
        original_q = agent.get_q_values(state)
        loaded_q = new_agent.get_q_values(state)
        assert original_q == loaded_q
        
        # Cleanup
        os.unlink(filepath)
    
    def test_exploration_decay(self):
        agent = QLearningAgent(exploration_rate=0.5, exploration_decay=0.9)
        initial_rate = agent.exploration_rate
        
        agent.decay_exploration()
        
        assert agent.exploration_rate < initial_rate
        assert agent.exploration_rate >= agent.min_exploration
    
    def test_get_stats(self):
        agent = QLearningAgent()
        stats = agent.get_stats()
        
        assert 'q_table_size' in stats
        assert 'replay_buffer_size' in stats
        assert 'exploration_rate' in stats


class TestStateEncoder:
    """Tests for StateEncoder."""
    
    def test_encoder_creation(self):
        from gehenna_api.engine.ai.state_encoder import StateEncoder
        from gehenna_api.engine.state import GameState, PlayerState
        
        state = GameState(game_id="test")
        ps = PlayerState(
            id=1,
            username="Player 1",
            pool=30,
            hand=[],
            crypt=[],
            library=[],
            ash_heap=[],
            has_edge=False,
            transfers=0,
            victory_points=0,
        )
        state.players.append(ps)
        
        encoder = StateEncoder(state, player_id=1)
        assert encoder.player_id == 1


class TestRewardCalculator:
    """Tests for RewardCalculator."""
    
    def test_reward_creation(self):
        from gehenna_api.engine.ai.reward import RewardCalculator
        from gehenna_api.engine.state import GameState, PlayerState
        
        state = GameState(game_id="test")
        ps = PlayerState(
            id=1,
            username="Player 1",
            pool=30,
            hand=[],
            crypt=[],
            library=[],
            ash_heap=[],
            has_edge=False,
            transfers=0,
            victory_points=0,
        )
        state.players.append(ps)
        
        calc = RewardCalculator(state, player_id=1)
        assert calc.player_id == 1
    
    def test_calculate_reward(self):
        from gehenna_api.engine.ai.reward import RewardCalculator
        from gehenna_api.engine.state import GameState, PlayerState
        
        state = GameState(game_id="test")
        ps = PlayerState(
            id=1,
            username="Player 1",
            pool=30,
            hand=[],
            crypt=[],
            library=[],
            ash_heap=[],
            has_edge=False,
            transfers=0,
            victory_points=0,
        )
        state.players.append(ps)
        
        calc = RewardCalculator(state, player_id=1)
        reward = calc.calculate_reward('bleed', 'success', 'mid')
        
        assert isinstance(reward, float)
        assert reward > 0  # Positive reward for successful bleed


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
