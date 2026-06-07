from __future__ import annotations

import random

from abc import ABC, abstractmethod

from gehenna_api.engine.state import GameState


class Bot(ABC):
    @abstractmethod
    def choose_action(self, state: GameState, player_id: int) -> str:
        ...

    def choose_action_type(
        self, state: GameState, player_id: int, minion_id: str
    ) -> str:
        """Choose which action type a minion should perform.

        Returns one of: 'bleed', 'hunt', or 'action_card'
        Default: prefer bleed, hunt if vampire with no blood, else action card.
        """
        minion = state.card_by_id(minion_id)
        if not minion:
            return 'bleed'

        # Hunt is mandatory for vampires with no blood
        if minion.tipo in ('Vampire', 'vampire', 'Imbued'):
            if minion.blood == 0:
                return 'hunt'
            if minion.blood <= 2 and random.random() < 0.3:
                return 'hunt'

        # Default to bleed (intrinsic action)
        return 'bleed'

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
