from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    game_started = 'game_started'
    phase_changed = 'phase_changed'
    turn_started = 'turn_started'
    card_drawn = 'card_drawn'
    card_played = 'card_played'
    card_burned = 'card_burned'
    action_declared = 'action_declared'
    action_blocked = 'action_blocked'
    action_resolved = 'action_resolved'
    combat_started = 'combat_started'
    strike_declared = 'strike_declared'
    damage_dealt = 'damage_dealt'
    minion_ousted = 'minion_ousted'
    player_ousted = 'player_ousted'
    pool_changed = 'pool_changed'
    blood_changed = 'blood_changed'
    edge_gained = 'edge_gained'
    edge_lost = 'edge_lost'
    game_ended = 'game_ended'


class GameEvent(BaseModel):
    type: EventType
    data: dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    player_id: Optional[int] = None


EventHandler = Callable[[GameEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}

    def on(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def off(self, event_type: EventType, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event: GameEvent) -> None:
        for handler in self._handlers.get(event.type, []):
            handler(event)

    def clear(self) -> None:
        self._handlers.clear()
