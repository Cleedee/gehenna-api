from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Range(str, Enum):
    close = 'close'
    long = 'long'


class StrikeType(str, Enum):
    hand_strike = 'hand_strike'
    weapon = 'weapon'
    dodge = 'dodge'
    combat_ends = 'combat_ends'
    steal_blood = 'steal_blood'
    bite = 'bite'
    special = 'special'


class Strike(BaseModel):
    strike_type: StrikeType
    damage: int = 0
    aggravated: bool = False
    steal: int = 0
    manoeuvres: int = 0
    press: int = 0
    range: Optional[Range] = None


class CombatRound(BaseModel):
    range: Range = Range.close
    strikes_attacker: list[Strike] = Field(default_factory=list)
    strikes_defender: list[Strike] = Field(default_factory=list)
    press_count: int = 0
    is_finished: bool = False


class CombatState(BaseModel):
    attacker_id: str
    defender_id: str
    current_range: Range = Range.close
    round_number: int = 0
    rounds: list[CombatRound] = Field(default_factory=list)
    is_finished: bool = False
    winner_id: Optional[str] = None
