"""Tests for the strategy engine."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gehenna_api.engine.ai.strategy import (
    DeckStrategy,
    GamePhase,
    PhaseAdjustments,
    StrategyEngine,
    ThreatAssessment,
)


class TestGamePhase:
    """Tests for GamePhase enum."""

    def test_game_phase_values(self):
        assert GamePhase.EARLY.value == "early"
        assert GamePhase.MID.value == "mid"
        assert GamePhase.LATE.value == "late"
        assert GamePhase.FINAL.value == "final"


class TestPhaseAdjustments:
    """Tests for PhaseAdjustments dataclass."""

    def test_default_values(self):
        adj = PhaseAdjustments()
        assert adj.bleed_modifier == 0.0
        assert adj.rush_modifier == 0.0
        assert adj.vote_modifier == 0.0

    def test_from_dict(self):
        data = {
            "bleed_modifier": 0.2,
            "rush_modifier": -0.1,
            "vote_modifier": 0.3,
        }
        adj = PhaseAdjustments.from_dict(data)
        assert adj.bleed_modifier == 0.2
        assert adj.rush_modifier == -0.1
        assert adj.vote_modifier == 0.3


class TestDeckStrategy:
    """Tests for DeckStrategy dataclass."""

    def test_default_values(self):
        strategy = DeckStrategy(deck_id=1)
        assert strategy.deck_id == 1
        assert strategy.bleed_priority == 1.0
        assert strategy.rush_priority == 0.0
        assert strategy.vote_priority == 0.0

    def test_from_dict(self):
        data = {
            "deck_id": 275,
            "name": "Test Deck",
            "bleed_priority": 0.6,
            "rush_priority": 0.5,
            "early_phase": {"bleed_modifier": -0.1, "rush_modifier": -0.2},
        }
        strategy = DeckStrategy.from_dict(data)
        assert strategy.deck_id == 275
        assert strategy.name == "Test Deck"
        assert strategy.bleed_priority == 0.6
        assert strategy.rush_priority == 0.5
        assert strategy.early_phase.bleed_modifier == -0.1
        assert strategy.early_phase.rush_modifier == -0.2

    def test_get_phase_adjustments(self):
        strategy = DeckStrategy(deck_id=1)
        strategy.early_phase = PhaseAdjustments(bleed_modifier=-0.2)
        strategy.late_phase = PhaseAdjustments(bleed_modifier=0.2)

        early_adj = strategy.get_phase_adjustments(GamePhase.EARLY)
        late_adj = strategy.get_phase_adjustments(GamePhase.LATE)

        assert early_adj.bleed_modifier == -0.2
        assert late_adj.bleed_modifier == 0.2

    def test_get_adjusted_priority(self):
        strategy = DeckStrategy(deck_id=1)
        # Clamped to 0-1
        assert strategy.get_adjusted_priority(0.5, 0.3) == 0.8
        assert strategy.get_adjusted_priority(0.5, -0.3) == 0.2
        assert strategy.get_adjusted_priority(0.5, 0.6) == 1.0  # Capped
        assert strategy.get_adjusted_priority(0.5, -0.6) == 0.0  # Floored


class TestThreatAssessment:
    """Tests for ThreatAssessment."""

    def test_default_thresholds(self):
        assessor = ThreatAssessment()
        assert assessor.pool_threshold == 20
        assert assessor.minion_threshold == 3
        assert assessor.title_bonus == 2


class TestStrategyEngine:
    """Tests for StrategyEngine."""

    def test_load_strategies_from_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test strategy file
            strategy_data = {
                "deck_id": 999,
                "name": "Test Deck",
                "bleed_priority": 0.7,
            }
            with open(os.path.join(tmpdir, "deck-999.json"), "w") as f:
                json.dump(strategy_data, f)

            engine = StrategyEngine(strategies_dir=tmpdir)
            strategy = engine.get_strategy(999)

            assert strategy.deck_id == 999
            assert strategy.name == "Test Deck"
            assert strategy.bleed_priority == 0.7

    def test_get_default_strategy(self):
        engine = StrategyEngine()
        strategy = engine.get_strategy(9999)  # Non-existent

        assert strategy.deck_id == 9999
        assert strategy.bleed_priority == 1.0  # Default

    def test_adjusted_strategy(self):
        strategy = DeckStrategy(
            deck_id=1,
            bleed_priority=0.6,
            rush_priority=0.5,
            early_phase=PhaseAdjustments(bleed_modifier=-0.1, rush_modifier=-0.2),
            late_phase=PhaseAdjustments(bleed_modifier=0.2, rush_modifier=0.2),
        )

        engine = StrategyEngine()

        early = engine.get_adjusted_strategy(strategy, GamePhase.EARLY)
        late = engine.get_adjusted_strategy(strategy, GamePhase.LATE)

        assert early["bleed_priority"] == 0.5  # 0.6 - 0.1
        assert early["rush_priority"] == 0.3  # 0.5 - 0.2
        assert late["bleed_priority"] == 0.8  # 0.6 + 0.2
        assert late["rush_priority"] == 0.7  # 0.5 + 0.2


class TestCardKnowledge:
    """Tests for CardKnowledge."""

    def test_get_card_category(self):
        from gehenna_api.engine.ai.strategy import CardKnowledge
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

        knowledge = CardKnowledge(state, player_id=1)

        # Test with mock cards
        class MockCard:
            def __init__(self, name, tipo):
                self.name = name
                self.tipo = tipo
                self.is_superior = False
                self.bleed = 0
                self.stealth = 0

        deflection = MockCard("Deflection", "reaction")
        govern = MockCard("Govern the Unaligned", "action")
        stealth = MockCard("Shadow Cloak", "action modifier")

        assert knowledge.get_card_category(deflection) == "defense"
        assert knowledge.get_card_category(govern) == "bleed"
        assert knowledge.get_card_category(stealth) == "stealth"

    def test_get_useful_cards_for_situation(self):
        from gehenna_api.engine.ai.strategy import CardKnowledge
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

        knowledge = CardKnowledge(state, player_id=1)

        defense_cards = knowledge.get_useful_cards_for_situation("defense")
        bleed_cards = knowledge.get_useful_cards_for_situation("bleed")

        assert "deflection" in defense_cards
        assert "govern" in bleed_cards

    def test_should_hold_card(self):
        from gehenna_api.engine.ai.strategy import CardKnowledge
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

        knowledge = CardKnowledge(state, player_id=1)

        # Test with mock cards
        class MockCard:
            def __init__(self, name, bleed=0, stealth=0):
                self.name = name
                self.bleed = bleed
                self.stealth = stealth
                self.tipo = "action"
                self.is_superior = False

        deflection = MockCard("Deflection")
        high_bleed = MockCard("Govern", bleed=3)
        low_bleed = MockCard("Shroud", bleed=1)

        assert knowledge.should_hold_card(deflection) is True
        assert knowledge.should_hold_card(high_bleed) is True
        assert knowledge.should_hold_card(low_bleed) is False


class TestCardTiming:
    """Tests for CardTiming."""

    def test_should_play_redirect(self):
        from gehenna_api.engine.ai.strategy import CardTiming
        from gehenna_api.engine.state import GameState, PlayerState

        state = GameState(game_id="test")
        for i in range(1, 3):
            ps = PlayerState(
                id=i,
                username=f"Player {i}",
                pool=10 if i == 1 else 15,  # Player 1 has low pool
                hand=[],
                crypt=[],
                library=[],
                ash_heap=[],
                has_edge=False,
                transfers=0,
                victory_points=0,
            )
            state.players.append(ps)

        timing = CardTiming(state, player_id=1)

        # Should redirect big bleeds
        assert timing.should_play_redirect(3) is True
        assert timing.should_play_redirect(2) is True  # Pool <= 15
        assert timing.should_play_redirect(1) is False

    def test_should_play_stealth(self):
        from gehenna_api.engine.ai.strategy import CardTiming
        from gehenna_api.engine.state import GameState, PlayerState

        state = GameState(game_id="test")
        for i in range(1, 3):
            ps = PlayerState(
                id=i,
                username=f"Player {i}",
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

        timing = CardTiming(state, player_id=1)

        # Should play stealth when predator has blockers
        # (needs actual minions to test properly)
        result = timing.should_play_stealth('bleed')
        assert isinstance(result, bool)

    def test_get_card_priority(self):
        from gehenna_api.engine.ai.strategy import CardTiming
        from gehenna_api.engine.state import GameState, PlayerState
        from gehenna_api.engine.card_instance import CardInstance

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

        timing = CardTiming(state, player_id=1)

        # Test card priority with mock cards
        class MockCard:
            def __init__(self, name, tipo):
                self.name = name
                self.tipo = tipo

        deflection = MockCard("Deflection", "reaction")
        stealth = MockCard("Shadow Cloak", "action modifier")
        bleed = MockCard("Govern the Unaligned", "action")

        assert timing.get_card_priority(deflection) == 100
        assert timing.get_card_priority(stealth) == 80
        assert timing.get_card_priority(bleed) == 40


class TestComboSystem:
    """Tests for ComboSystem."""

    def test_detect_available_combos(self):
        from gehenna_api.engine.ai.strategy import ComboSystem
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

        combo = ComboSystem(state, player_id=1)
        available = combo.detect_available_combos()
        
        # Should return a list (may be empty)
        assert isinstance(available, list)

    def test_get_combo_priority(self):
        from gehenna_api.engine.ai.strategy import ComboSystem
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

        combo = ComboSystem(state, player_id=1)
        priority = combo.get_combo_priority()
        
        # Should return an integer
        assert isinstance(priority, int)
        assert priority >= 0


class TestLearningSystem:
    """Tests for LearningSystem."""

    def test_record_action(self):
        from gehenna_api.engine.ai.strategy import LearningSystem

        learning = LearningSystem()
        learning.record_action(
            action_type='bleed',
            card_name='Govern',
            situation='aggressive',
            outcome='success',
        )
        
        assert len(learning.action_history) == 1
        assert learning.action_history[0]['action_type'] == 'bleed'

    def test_get_card_effectiveness(self):
        from gehenna_api.engine.ai.strategy import LearningSystem

        learning = LearningSystem()
        
        # Record some actions
        for _ in range(7):
            learning.record_action('bleed', 'Govern', 'aggressive', 'success')
        for _ in range(3):
            learning.record_action('bleed', 'Govern', 'aggressive', 'fail')
        
        effectiveness = learning.get_card_effectiveness('Govern')
        assert effectiveness == 0.7  # 7/10 success

    def test_get_situation_adjustment(self):
        from gehenna_api.engine.ai.strategy import LearningSystem

        learning = LearningSystem()
        
        # Record successful situation
        for _ in range(8):
            learning.record_action('bleed', None, 'aggressive', 'success')
        for _ in range(2):
            learning.record_action('bleed', None, 'aggressive', 'fail')
        
        adjustment = learning.get_situation_adjustment('aggressive')
        assert adjustment == 0.1  # High win rate

    def test_reset(self):
        from gehenna_api.engine.ai.strategy import LearningSystem

        learning = LearningSystem()
        learning.record_action('bleed', 'Govern', 'aggressive', 'success')
        
        learning.reset()
        
        assert len(learning.action_history) == 0
        assert len(learning.card_effectiveness) == 0


class TestGameStateAnalyzer:
    """Tests for GameStateAnalyzer."""

    def test_analyzer_calculates_prey_predator(self):
        from gehenna_api.engine.ai.strategy import GameStateAnalyzer
        from gehenna_api.engine.state import GameState, PlayerState

        state = GameState(game_id="test")
        # Create 4 players
        for i in range(1, 5):
            ps = PlayerState(
                id=i,
                username=f"Player {i}",
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

        analyzer = GameStateAnalyzer(state, player_id=1)

        assert analyzer.prey is not None
        assert analyzer.prey.id == 4  # Player 4 is prey of Player 1 (counter-clockwise)
        assert analyzer.predator is not None
        assert analyzer.predator.id == 2  # Player 2 is predator of Player 1 (clockwise)
        assert len(analyzer.cross_players) == 1  # Player 3 is cross

    def test_analyzer_strategic_position(self):
        from gehenna_api.engine.ai.strategy import GameStateAnalyzer, ThreatAssessment
        from gehenna_api.engine.state import GameState, PlayerState

        state = GameState(game_id="test")
        # Create 4 players with different pools
        for i in range(1, 5):
            ps = PlayerState(
                id=i,
                username=f"Player {i}",
                pool=30 if i == 1 else 10,  # Player 1 is strong
                hand=[],
                crypt=[],
                library=[],
                ash_heap=[],
                has_edge=False,
                transfers=0,
                victory_points=1 if i == 1 else 0,  # Player 1 has VP
            )
            state.players.append(ps)

        analyzer = GameStateAnalyzer(state, player_id=1)
        assessor = ThreatAssessment()

        position = analyzer.get_strategic_position(assessor)
        # Just check it returns a valid position
        assert position in ['aggressive', 'defensive', 'diplomatic', 'balanced']

    def test_analyzer_should_help_cross(self):
        from gehenna_api.engine.ai.strategy import GameStateAnalyzer, ThreatAssessment
        from gehenna_api.engine.state import GameState, PlayerState

        state = GameState(game_id="test")
        # Create 4 players
        for i in range(1, 5):
            ps = PlayerState(
                id=i,
                username=f"Player {i}",
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

        analyzer = GameStateAnalyzer(state, player_id=1)
        assessor = ThreatAssessment()

        # Cross player is Player 3
        cross_player = analyzer.cross_players[0] if analyzer.cross_players else None
        if cross_player:
            # Should help if cross predator is threatening
            result = analyzer.should_help_cross(cross_player, assessor)
            assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
