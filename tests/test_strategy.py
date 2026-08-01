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


class TestStrategyBotIntegration:
    """Integration tests for StrategyBot."""

    def test_bot_can_be_created(self):
        from gehenna_api.engine.ai.strategy_bot import StrategyBot

        bot = StrategyBot(deck_id=275)
        assert bot.deck_id == 275

    def test_bot_has_required_methods(self):
        from gehenna_api.engine.ai.strategy_bot import StrategyBot

        bot = StrategyBot(deck_id=1)
        assert hasattr(bot, "choose_action_type")
        assert hasattr(bot, "choose_block")
        assert hasattr(bot, "choose_strike")
        assert hasattr(bot, "choose_discard")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
