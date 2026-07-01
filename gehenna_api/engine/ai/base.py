from __future__ import annotations

from abc import ABC, abstractmethod

from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.state import GameState


class Bot(ABC):
    @abstractmethod
    def choose_action(self, state: GameState, player_id: int) -> str:
        ...

    def choose_action_type(
        self, state: GameState, player_id: int, minion_id: str
    ) -> str:
        """Choose which action type a minion should perform.

        Returns: 'bleed', 'hunt', 'leave_torpor', 'rescue', 'diablerie',
                 'action_card', 'burn_card'
        """
        minion = state.card_by_id(minion_id)
        if not minion:
            return 'bleed'

        is_vampire = minion.tipo in ('Vampire', 'vampire', 'Imbued')
        player = state.player_by_id(player_id)

        # Leave torpor: mandatory if in torpor and have 2+ blood
        if minion.position == CardPosition.torpor:
            if is_vampire and minion.blood >= 2:
                return 'leave_torpor'
            return 'action_card'

        # Hunt is mandatory for vampires with no blood
        if is_vampire:
            if minion.blood == 0:
                return 'hunt'
            if minion.blood <= 2 and state.random.random() < 0.3:
                return 'hunt'

        # Check for action cards in hand
        has_action_cards = self._has_action_cards(state, player_id)
        if has_action_cards:
            # Check if there's a political action card
            if self._has_political_card(state, player_id) and is_vampire:
                if not player.political_action_used and state.random.random() < 0.15:
                    return 'political'
            return 'action_card'

        # Look for rescue/diablerie opportunities
        has_torpor_target = self._has_torpor_target(state, player_id)
        if has_torpor_target:
            if state.random.random() < 0.2:
                return 'rescue'
            if state.random.random() < 0.1 and is_vampire:
                return 'diablerie'

        # Look for burnable card targets (Pentex Subversion, etc.)
        if self._has_burnable_target(state, minion, player_id):
            if state.random.random() < 0.3:
                return 'burn_card'

        # Default to bleed
        return 'bleed'

    def _has_burnable_target(
        self, state: GameState, minion: CardInstance, player_id: int
    ) -> bool:
        """Check if there's another minion with a burnable effect."""
        for c in state.cards.values():
            if c.id == minion.id:
                continue
            if not c.is_ready:
                continue
            if c.tipo.strip() not in {'Vampire', 'vampire', 'Imbued', 'Ally'}:
                continue
            if getattr(c, 'burnable_effects', None):
                return True
        return False

    def _has_political_card(self, state: GameState, player_id: int) -> bool:
        """Check if player has a political action card in hand."""
        player = state.player_by_id(player_id)
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and card.tipo.strip().lower() == 'political action':
                return True
        return False

    def _has_action_cards(self, state: GameState, player_id: int) -> bool:
        """Check if player has any minion action cards in hand.
        
        Only true action cards (not Action Modifier, Reaction, or Combat).
        """
        player = state.player_by_id(player_id)
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                t = card.tipo.strip().lower()
                if t in (
                    'action', 'equipment', 'retainer', 'ally',
                    'political action',
                ):
                    return True
        return False

    def _has_torpor_target(self, state: GameState, player_id: int) -> bool:
        """Check if there's a vampire in torpor that can be targeted."""
        for c in state.cards.values():
            if c.position == CardPosition.torpor:
                if c.tipo in ('Vampire', 'vampire', 'Imbued'):
                    return True
        return False

    @abstractmethod
    def choose_block(
        self, state: GameState, player_id: int, action_id: str
    ) -> bool:
        ...

    @abstractmethod
    def choose_strike(self, state: GameState, combatant_id: str) -> str:
        ...

    @abstractmethod
    def choose_discard(
        self, state: GameState, player_id: int, hand: list[str]
    ) -> str:
        ...

    def choose_vessel_direction(
        self,
        state: GameState,
        player_id: int,
        vessel_id: str,
        vampire_id: str,
    ) -> str:
        """Choose the direction for Vessel's untap effect.

        Returns:
            'vampire_to_pool': move 1 blood from vampire to pool
            'pool_to_vampire': move 1 blood from pool to vampire
            'skip': skip the effect
        """
        return 'vampire_to_pool'
