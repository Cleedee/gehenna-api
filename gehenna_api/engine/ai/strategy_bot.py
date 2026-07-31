"""Strategy Bot - Uses StrategyEngine for intelligent decisions."""

from __future__ import annotations

import os
from pathlib import Path

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.ai.strategy import (
    DeckStrategy,
    StrategyEngine,
    DEFAULT_STRATEGIES,
)
from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.state import GameState


class StrategyBot(Bot):
    """Bot that uses strategy configurations for decision making."""

    def __init__(self, deck_id: int = 0, strategies_dir: str | None = None):
        self.deck_id = deck_id
        self.engine = StrategyEngine(strategies_dir)
        self.strategy = self.engine.get_strategy(deck_id)

        # Track game state for adaptation
        self.cards_played: list[str] = []
        self.cards_seen: dict[int, list[str]] = {}  # player_id -> cards
        self.turns_played: int = 0

    def choose_action(
        self, state: GameState, player_id: int
    ) -> str:
        """Choose action for the player."""
        return ""  # Not used directly

    def choose_action_type(
        self,
        state: GameState,
        player_id: int,
        minion_id: str,
    ) -> str:
        """Choose action type based on strategy."""
        self.turns_played = state.turn_number

        # Use strategy engine
        action = self.engine.choose_action_type(
            state=state,
            player_id=player_id,
            minion_id=minion_id,
            deck_id=self.deck_id,
        )

        # Track for adaptation
        self.cards_played.append(action)

        return action

    def choose_block(
        self,
        state: GameState,
        player_id: int,
        action_id: str,
    ) -> bool:
        """Choose whether to block."""
        player = state.player_by_id(player_id)
        if not player:
            return False

        # Get the action card
        action_card = state.card_by_id(action_id)
        if not action_card:
            return False

        # Check if action is bleed
        text = (getattr(action_card, "text", "") or "").lower()
        is_bleed = "bleed" in text or action_card.bleed > 0
        is_high_bleed = action_card.bleed > 2

        # Block high-threat bleeds against us
        if is_bleed and is_high_bleed:
            return True

        # Don't waste resources on small actions
        return False

    def choose_strike(
        self,
        state: GameState,
        combatant_id: str,
    ) -> str:
        """Choose strike type."""
        combatant = state.card_by_id(combatant_id)
        if not combatant:
            return "handstrike"

        # Use best available strike
        # Prioritize: Steal Blood > Aggravated > Hand Strike
        if combatant.has_steal_blood:
            return "steal_blood"

        # Check for aggravated damage cards
        for cid in combatant.hand:
            card = state.card_by_id(cid)
            if card and getattr(card, "is_aggravated", False):
                return card.id

        # Default to hand strike
        return "handstrike"

    def choose_discard(
        self,
        state: GameState,
        player_id: int,
        hand: list[str],
    ) -> str:
        """Choose which card to discard."""
        player = state.player_by_id(player_id)
        if not player or not hand:
            return ""

        # Strategy-based discard
        strategy = self.strategy

        # Keep preferred cards
        for cid in hand:
            card = state.card_by_id(cid)
            if card and card.name in strategy.preferred_cards:
                continue  # Don't discard preferred

        # Discard avoided cards first
        for cid in hand:
            card = state.card_by_id(cid)
            if card and card.name in strategy.avoided_cards:
                return cid

        # Discard lowest priority card
        # Simple: discard last card
        return hand[-1] if hand else ""

    def choose_vampire_to_burn_blood(
        self,
        state: GameState,
        player_id: int,
        amount: int,
    ) -> str | None:
        """Choose vampire to burn blood from (e.g., for Villein)."""
        player = state.player_by_id(player_id)
        if not player:
            return None

        # Find vampire with most blood
        best = None
        best_blood = 0

        for cid in player.ready:
            card = state.card_by_id(cid)
            if (
                card
                and card.tipo.strip().lower() == "vampire"
                and card.blood > best_blood
            ):
                best = card
                best_blood = card.blood

        return best.id if best else None


def create_strategy_bot(
    deck_id: int,
    strategies_dir: str | None = None,
) -> StrategyBot:
    """Create a strategy bot for a specific deck."""
    if strategies_dir is None:
        strategies_dir = str(
            Path(__file__).parent / "strategies"
        )
    return StrategyBot(deck_id=deck_id, strategies_dir=strategies_dir)
