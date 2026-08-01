"""Strategy Bot - Uses StrategyEngine for intelligent decisions."""

from __future__ import annotations

import os
from pathlib import Path

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.ai.strategy import (
    CardKnowledge,
    CardTiming,
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

    def choose_card_to_play(
        self,
        state: GameState,
        player_id: int,
        action_type: str = 'bleed',
    ) -> str | None:
        """Choose which card to play from hand based on timing and knowledge.
        
        Args:
            state: Current game state
            player_id: ID of the player
            action_type: Type of action being attempted ('bleed', 'rush', etc.)
        
        Returns:
            Card ID to play, or None if no card should be played
        """
        player = state.player_by_id(player_id)
        if not player or not player.hand:
            return None
        
        # Use CardKnowledge for intelligent card selection
        knowledge = CardKnowledge(state, player_id)
        timing = CardTiming(state, player_id)
        
        # Get prioritized cards for this situation
        prioritized = knowledge.prioritize_cards_for_situation(action_type)
        
        # Return highest priority card that should be played
        for card, priority in prioritized:
            # Check if we should hold this card
            if knowledge.should_hold_card(card) and priority < 80:
                continue
            
            name = card.name.lower()
            tipo = card.tipo.strip().lower()
            
            # Deflection - only play against big bleeds
            if 'deflection' in name:
                if player.pool <= 10:
                    return card.id
                continue
            
            # Stealth cards - play when needed
            if any(n in name for n in ('cloak', 'seduction', 'where the veil')):
                if timing.should_play_stealth(action_type):
                    return card.id
                continue
            
            # Action modifiers - play after action confirmed
            if tipo == 'action modifier':
                if timing.should_play_modifier():
                    return card.id
                continue
            
            # Action cards - play based on action type
            if tipo == 'action':
                if action_type == 'bleed' and 'bleed' in name:
                    return card.id
                if action_type == 'rush' and 'rush' in name.lower():
                    return card.id
                continue
            
            # Political actions
            if tipo == 'political action':
                return card.id
        
        return None

    def should_play_card(
        self,
        state: GameState,
        player_id: int,
        card_id: str,
        context: dict,
    ) -> bool:
        """Decide whether to play a specific card.
        
        Args:
            state: Current game state
            player_id: ID of the player
            card_id: ID of the card to play
            context: Additional context (e.g., {'bleed_amount': 3})
        
        Returns:
            True if card should be played
        """
        card = state.card_by_id(card_id)
        if not card:
            return False
        
        timing = CardTiming(state, player_id)
        player = state.player_by_id(player_id)
        if not player:
            return False
        
        name = card.name.lower()
        
        # Deflection
        if 'deflection' in name:
            bleed_amount = context.get('bleed_amount', 0)
            return timing.should_play_deflection(bleed_amount)
        
        # Stealth
        if any(n in name for n in ('cloak', 'seduction', 'where the veil')):
            action_type = context.get('action_type', 'bleed')
            return timing.should_play_stealth(action_type)
        
        # Modifiers
        if card.tipo.strip().lower() == 'action modifier':
            return timing.should_play_modifier()
        
        # Default: play the card
        return True


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
