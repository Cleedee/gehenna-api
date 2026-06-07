from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CardPosition(str, Enum):
    crypt = 'crypt'
    library = 'library'
    hand = 'hand'
    uncontrolled = 'uncontrolled'
    ready = 'ready'
    torpor = 'torpor'
    ash_heap = 'ash_heap'
    in_play = 'in_play'
    attached = 'attached'
    contested = 'contested'
    removed = 'removed'


class CardInstance(BaseModel):
    id: str
    card_id: int
    name: str
    position: CardPosition = CardPosition.library
    locked: bool = False
    blood: int = 0
    life: int = 0
    counters: dict[str, int] = Field(default_factory=dict)
    attached_to: Optional[str] = None
    attachments: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    tipo: str = ''
    pool_cost: int = 0

    strength: int = 1
    stealth: int = 0
    intercept: int = 0
    bleed: int = 0
    capacity: int = 0
    damage_taken: int = 0
    hunt: int = 1
    # Track actions performed this turn (reset each unlock phase)
    actions_this_turn: int = 0
    has_acted_this_turn: bool = False
    # Combat tracking
    maneuvers: int = 0
    damage_prevented: int = 0
    additional_strikes: int = 0
    first_strike: bool = False
    ranged: bool = False

    def lock(self) -> None:
        self.locked = True

    def unlock(self) -> None:
        self.locked = False

    def add_blood(self, amount: int) -> int:
        added = min(amount, self.capacity - self.blood)
        self.blood += added
        return added

    def take_damage(self, amount: int, aggravated: bool = False) -> int:
        if self.position == CardPosition.torpor:
            return 0
        can_mend = 0 if aggravated else min(self.blood, amount)
        self.blood -= can_mend
        self.damage_taken += amount - can_mend
        if self.damage_taken > 0 and self.position == CardPosition.ready:
            self.position = CardPosition.torpor
            self.locked = True
        return amount

    def mend_damage(self, amount: int) -> int:
        mended = min(self.damage_taken, amount)
        self.damage_taken -= mended
        if self.damage_taken <= 0:
            self.damage_taken = 0
        return mended

    @property
    def is_ready(self) -> bool:
        return self.position == CardPosition.ready and not self.locked

    @property
    def is_wounded(self) -> bool:
        return self.damage_taken > 0 or self.position == CardPosition.torpor

    @property
    def is_alive(self) -> bool:
        return self.position not in (
            CardPosition.ash_heap,
            CardPosition.removed,
        )
