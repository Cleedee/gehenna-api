from __future__ import annotations

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.state import GameState


class RandomBot(Bot):
    def choose_action(self, state: GameState, player_id: int) -> str:
        player = state.player_by_id(player_id)
        if not player or not player.hand:
            return 'pass'
        return state.random.choice(player.hand)

    def choose_block(
        self, state: GameState, player_id: int, action_id: str
    ) -> bool:
        ready = state.ready_minions(player_id)
        if not ready:
            return False
        # Always try to block if possible (aggressive defense)
        # Can be made more sophisticated later
        return True

    def choose_strike(self, state: GameState, combatant_id: str) -> str:
        return 'hand_strike'

    def choose_discard(
        self, state: GameState, player_id: int, hand: list[str]
    ) -> str:
        if not hand:
            return ''
        return hand[0]

    def choose_vessel_direction(
        self,
        state: GameState,
        player_id: int,
        vessel_id: str,
        vampire_id: str,
    ) -> str:
        """Decide Vessel direction: pool-to-vampire if vampire needs
        blood, otherwise vampire-to-pool for pool gain."""
        player = state.player_by_id(player_id)
        vampire = state.card_by_id(vampire_id)
        if not player or not vampire:
            return 'skip'
        # Vampire low on blood → pool to vampire
        if vampire.blood <= 2:
            return 'pool_to_vampire'
        # Default: vampire to pool (gain pool)
        return 'vampire_to_pool'
