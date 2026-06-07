from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    bleed = 'bleed'
    political = 'political'
    combat = 'combat'
    recruit = 'recruit'
    equip = 'equip'
    hunt = 'hunt'
    influence = 'influence'
    diablerie = 'diablerie'
    master = 'master'
    special = 'special'


class Action(BaseModel):
    id: str
    action_type: ActionType
    actor_id: str
    target_player_id: Optional[int] = None
    target_card_id: Optional[str] = None
    stealth: int = 0
    is_directed: bool = True
    is_blocked: bool = False
    blocker_id: Optional[str] = None
    is_resolved: bool = False
    cards_used: list[str] = Field(default_factory=list)
