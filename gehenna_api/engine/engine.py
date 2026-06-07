from __future__ import annotations

from typing import Optional

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.card_instance import CardPosition
from gehenna_api.engine.events import EventBus, EventType, GameEvent
from gehenna_api.engine.phases import PhaseManager
from gehenna_api.engine.state import GameState, Phase


class GameEngine:
    def __init__(
        self, state: GameState, bots: dict[int, Bot] | None = None
    ) -> None:
        self.state = state
        self.events = EventBus()
        self.phases = PhaseManager(state, self.events)
        self.bots = bots or {}
        self.log: list[dict] = []
        self._is_running = False
        self._subscribe_log()

    def _subscribe_log(self) -> None:
        def on_event(ev: GameEvent) -> None:
            if ev.type in (
                EventType.action_declared,
                EventType.card_played,
                EventType.pool_changed,
                EventType.player_ousted,
            ):
                self.log.append(
                    {
                        'type': ev.type.value,
                        'player_id': ev.player_id,
                        'data': ev.data,
                    }
                )
                if len(self.log) > 200:
                    self.log[:] = self.log[-100:]

        self.events.on(EventType.action_declared, on_event)
        self.events.on(EventType.card_played, on_event)
        self.events.on(EventType.pool_changed, on_event)
        self.events.on(EventType.player_ousted, on_event)

    def start(self) -> None:
        self._is_running = True
        self.state.current_phase = Phase.unlock
        self.state.turn_number = 0
        self.state.current_player_index = 0

        for player in self.state.players:
            self.phases.draw_cards(player, 7)
            for _ in range(4):
                if player.crypt:
                    cid = player.crypt.pop(0)
                    inst = self.state.card_by_id(cid)
                    if inst:
                        inst.position = CardPosition.uncontrolled
                        inst.locked = True

        self.events.emit(
            GameEvent(
                type=EventType.game_started,
                data={'game_id': self.state.game_id},
            )
        )

    def run_turn(self) -> None:
        if not self._is_running:
            return

        player = self.state.current_player
        if not player:
            return

        self.phases.execute_unlock()

        # Master phase — all active players play one master card each
        self.state.current_phase = Phase.master
        self.phases.execute_master(self.bots)

        # Minion phase — each active player with ready minions
        self.state.current_phase = Phase.minion
        self.phases.execute_minion(self.bots)

        # Influence phase
        self.state.current_phase = Phase.influence
        self.phases.execute_influence(player, self.state, self.bots)

        # Discard phase
        self.state.current_phase = Phase.discard
        self.phases.execute_discard(player, self.bots)

        self.phases._end_turn()

    @property
    def is_finished(self) -> bool:
        return self.state.check_winner() is not None

    def get_winner(self) -> Optional[int]:
        winner = self.state.check_winner()
        return winner.id if winner else None
