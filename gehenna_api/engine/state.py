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
    is_finished: bool = False
    edge_uncontrolled: bool = True

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

    def oust_player(self, player_id: int) -> None:
        player = self.player_by_id(player_id)
        if player:
            player.is_ousted = True
            if player.has_edge:
                player.has_edge = False
                self.edge_uncontrolled = True

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
        active = self.active_players
        if len(active) <= 1:
            return active[0] if active else None
        return None
