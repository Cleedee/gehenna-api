from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from gehenna_api.engine.card_instance import CardInstance, CardPosition


class Phase(str, Enum):
    unlock = 'unlock'
    master = 'master'
    minion = 'minion'
    influence = 'influence'
    discard = 'discard'


class PlayerState(BaseModel):
    id: int
    username: str
    pool: int = 30
    hand: list[str] = Field(default_factory=list)
    crypt: list[str] = Field(default_factory=list)
    library: list[str] = Field(default_factory=list)
    ash_heap: list[str] = Field(default_factory=list)
    has_edge: bool = False
    transfers: int = 0
    victory_points: int = 0
    is_ousted: bool = False
    master_actions: int = 0
    out_of_turn_master_played: bool = False
    trifle_played_this_phase: bool = False
    # Political system
    votes: int = 0
    political_action_used: bool = False
    has_title: str = ''
    is_red_list: bool = False
    blood_hunt_active: bool = False

    def mark_out_of_turn_master(self) -> None:
        """Mark that this player played an out-of-turn master card.
        They will receive one fewer master phase action next turn."""
        self.out_of_turn_master_played = True


class GameState(BaseModel):
    game_id: str
    players: list[PlayerState] = Field(default_factory=list)
    cards: dict[str, CardInstance] = Field(default_factory=dict)
    turn_order: list[int] = Field(default_factory=list)
    current_turn: int = 0
    current_phase: Phase = Phase.unlock
    current_player_index: int = 0
    turn_number: int = 0
    blood_bank: int = 999_999
    edge_uncontrolled: bool = True
    _is_finished: bool = False
    # Political system
    current_referendum: Optional[dict] = None
    referendum_results: dict = Field(default_factory=dict)

    @property
    def current_player(self) -> Optional[PlayerState]:
        if self.current_player_index >= len(self.players):
            return None
        return self.players[self.current_player_index]

    @property
    def current_player_id(self) -> Optional[int]:
        p = self.current_player
        return p.id if p else None

    def player_by_id(self, player_id: int) -> Optional[PlayerState]:
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def card_by_id(self, card_instance_id: str) -> Optional[CardInstance]:
        return self.cards.get(card_instance_id)

    def cards_in_play(self, player_id: int) -> list[CardInstance]:
        return [
            c
            for c in self.cards.values()
            if c.position
            in (
                CardPosition.ready,
                CardPosition.torpor,
                CardPosition.in_play,
                CardPosition.attached,
            )
        ]

    def ready_minions(self, player_id: int) -> list[CardInstance]:
        return [c for c in self.cards.values() if c.is_ready]

    def next_player(self) -> None:
        self.current_player_index = (self.current_player_index + 1) % len(
            self.active_players
        )

    @property
    def active_players(self) -> list[PlayerState]:
        return [p for p in self.players if not p.is_ousted]

    def oust_player(self, player_id: int) -> list[str]:
        """Oust a player from the game.
        
        Returns list of card instance IDs that were removed from play.
        
        Rules:
        - Ousted player loses all pool
        - Predator gains 6 pool and 1 VP
        - If ousted at same time as prey, still gets VP but no pool
        - All ousted player's controlled cards are removed from game
        - Edge returns to uncontrolled if ousted player had it
        - Prey relationships update
        """
        player = self.player_by_id(player_id)
        if not player or player.is_ousted:
            return []

        removed_cards = []

        # Find predator BEFORE marking as ousted (predator_of uses active_players)
        predator = self.predator_of(player_id)

        # Handle Edge
        if player.has_edge:
            player.has_edge = False
            self.edge_uncontrolled = True

        # Now mark as ousted
        player.is_ousted = True

        # Award VP + pool to predator
        if predator and not predator.is_ousted:
            predator.victory_points += 1
            predator.pool += 6

        # Remove all cards controlled by ousted player from play
        prefix = f'p{player.id}_'
        card_ids_to_remove = [
            c.id for c in self.cards.values()
            if c.id.startswith(prefix)
            and c.position not in (CardPosition.removed,)
        ]
        for cid in card_ids_to_remove:
            inst = self.cards.get(cid)
            if inst:
                inst.position = CardPosition.removed
                removed_cards.append(cid)

        # Clear player's hand, library, crypt, ash_heap
        player.hand.clear()
        player.library.clear()
        player.crypt.clear()
        player.ash_heap.clear()
        player.pool = 0
        player.transfers = 0

        return removed_cards

    def predator_of(self, player_id: int) -> Optional[PlayerState]:
        """Return the predator of the given player.
        The predator is the player to the right (clockwise).
        When a player is ousted, the circle closes."""
        active = self.active_players
        if len(active) <= 1:
            return None
        for i, p in enumerate(active):
            if p.id == player_id:
                # Predator is the next player in the list (to the right)
                return active[(i + 1) % len(active)]
        return None

    def prey_of(self, player_id: int) -> Optional[PlayerState]:
        """Return the prey of the given player.
        The prey is the player to the left (counter-clockwise)."""
        active = self.active_players
        if len(active) <= 1:
            return None
        for i, p in enumerate(active):
            if p.id == player_id:
                # Prey is the previous player in the list (to the left)
                return active[(i - 1) % len(active)]
        return None

    def check_winner(self) -> Optional[PlayerState]:
        """Check if the game has a winner.
        
        Rules:
        - Game ends when only 1 Methuselah remains
        - Winner is the Methuselah with most VP
        - Tie = no winner
        """
        active = self.active_players
        if len(active) == 1:
            return active[0]
        return None

    def award_last_survivor_bonus(self) -> None:
        """Award +1 VP to the last surviving Methuselah."""
        active = self.active_players
        if len(active) == 1:
            active[0].victory_points += 1

    @property
    def is_finished(self) -> bool:
        """Check if the game is finished."""
        active = self.active_players
        return len(active) <= 1

    def get_final_scores(self) -> list[dict]:
        """Get final scores for all players."""
        scores = []
        for p in self.players:
            scores.append({
                'player_id': p.id,
                'username': p.username,
                'victory_points': p.victory_points,
                'is_ousted': p.is_ousted,
            })
        # Sort by VP descending
        scores.sort(key=lambda x: x['victory_points'], reverse=True)
        return scores
