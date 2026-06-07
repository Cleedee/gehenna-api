from __future__ import annotations

import random
from typing import Optional

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.events import EventBus, EventType, GameEvent
from gehenna_api.engine.state import GameState, Phase, PlayerState


MASTER_TIPOS = {'Master', 'Master '}

EVENT_TIPOS = {'Event'}

TRIFLE_TIPOS = {'Trifle', 'Master/Trifle'}

# All playable master cards (regular masters + trifles)
ALL_MASTER_TIPOS = MASTER_TIPOS | TRIFLE_TIPOS

# Basic intrinsic actions (no action card required)
# These are natural powers of minions
BASIC_ACTIONS = {
    'bleed': 'Bleed',
    'hunt': 'Hunt',
    'leave_torpor': 'Leave Torpor',
    'rescue': 'Rescue from Torpor',
    'diablerie': 'Diablerie',
}

# Action card types (played from hand to enhance or enable special actions)
ACTION_CARD_TYPES = {
    'Action',
    'Action Modifier',
    'Political Action',
    'Equipment',
    'Retainer',
    'Ally',
    'Conviction',
    'Power',
    'Imbued',
    'Combo',
    'Action / Combat',
    'Action / Reaction',
    'Action Modifier / Combat',
    'Action Modifier / Reaction',
    'Action Modifier/Combat',
    'Action Modifier/Reaction',
    'Action/Combat',
    'Reaction/Action Modifier',
    'Reaction/Combat',
    'Combat / Action',
    'Combat/Action Modifier',
    'Combat/Reaction',
}

MINION_TIPOS = {
    'Action',
    'Action Modifier',
    'Political Action',
    'Reaction',
    'Equipment',
    'Retainer',
    'Ally',
    'Conviction',
    'Power',
    'Imbued',
    'Combo',
    'Action / Combat',
    'Action / Reaction',
    'Action Modifier / Combat',
    'Action Modifier / Reaction',
    'Action Modifier/Combat',
    'Action Modifier/Reaction',
    'Action/Combat',
    'Reaction/Action Modifier',
    'Reaction/Combat',
    'Combat / Action',
    'Combat/Action Modifier',
    'Combat/Reaction',
}

COMBAT_ONLY = {'Combat'}

COMBAT_TIPOS = {
    'Combat',
    'Combat / Action',
    'Combat/Action Modifier',
    'Combat/Reaction',
}


def _tipo_key(raw: str) -> str:
    return raw.strip()


def _is_master(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in MASTER_TIPOS


def _is_event(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in EVENT_TIPOS


def _is_minion(inst: CardInstance) -> bool:
    # Cards with "Action" (including "Action/Combat" hybrids)
    # OR hybrids like "Combat / Action" that have action abilities
    return _tipo_key(inst.tipo) in MINION_TIPOS


def _is_combat_only(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in COMBAT_ONLY


def _is_trifle(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in TRIFLE_TIPOS


def _is_master_or_trifle(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in ALL_MASTER_TIPOS


def _has_type(hand: list[str], state: GameState, checker) -> list[str]:
    return [c for c in hand if checker(state.card_by_id(c))]


class PhaseManager:
    def __init__(self, state: GameState, events: EventBus) -> None:
        self.state = state
        self.events = events

    def advance_phase(self) -> None:
        phases = list(Phase)
        current_idx = phases.index(self.state.current_phase)
        if current_idx < len(phases) - 1:
            self.state.current_phase = phases[current_idx + 1]
        else:
            self._end_turn()
            return
        self.events.emit(
            GameEvent(
                type=EventType.phase_changed,
                data={'phase': self.state.current_phase.value},
            )
        )

    def _end_turn(self) -> None:
        self.state.next_player()
        self.state.current_phase = Phase.unlock
        self.state.turn_number += 1
        self.events.emit(
            GameEvent(
                type=EventType.turn_started,
                data={
                    'player_id': self.state.current_player_id,
                    'turn': self.state.turn_number,
                },
            )
        )

    def execute_unlock(self) -> None:
        for card in self.state.cards.values():
            if card.position == CardPosition.ready:
                card.locked = False

        player = self.state.current_player
        if player and player.has_edge:
            # Player with Edge gains 1 pool from blood bank
            player.pool += 1
            self.events.emit(
                GameEvent(
                    type=EventType.pool_changed,
                    player_id=player.id,
                    data={'delta': 1, 'reason': 'edge'},
                )
            )

        self.events.emit(
            GameEvent(
                type=EventType.phase_changed,
                data={'phase': 'unlock'},
            )
        )

    # ── Master phase ───────────────────────────────────────────────

    def execute_master(self, bots: dict[int, Bot]) -> None:
        self.events.emit(
            GameEvent(
                type=EventType.phase_changed,
                data={'phase': 'master'},
            )
        )
        for player in self.state.active_players:
            if self.state.is_finished:
                return
            bot = bots.get(player.id)
            if not bot:
                continue
            self._player_master_phase(player, bot)

    def _player_master_phase(self, player: PlayerState, bot: Bot) -> None:
        # Track whether any master card has been played this phase
        # Trifle only grants +1 action if it's the FIRST master card played
        master_card_played = False

        # Calculate master phase actions: default 1
        # -1 if out-of-turn master was played last turn
        actions = 1
        if player.out_of_turn_master_played:
            actions -= 1
            player.out_of_turn_master_played = False
        if actions <= 0:
            self._log_action(player, 'master phase skipped (out-of-turn penalty)')
            return

        player.master_actions = actions

        while player.master_actions > 0:
            self._use_master_action(player, bot, master_card_played)
            master_card_played = True

    def _use_master_action(self, player: PlayerState, bot: Bot, master_card_played: bool) -> None:
        player.master_actions -= 1

        masters = _has_type(player.hand, self.state, _is_master_or_trifle)
        if not masters:
            self._log_action(player, 'pass (no master in hand)')
            return

        card_id = bot.choose_action(self.state, player.id)
        inst = self.state.card_by_id(card_id) if card_id else None

        if not inst or inst.id not in player.hand or not _is_master_or_trifle(inst):
            # Bot picked wrong type — use first valid master/trifle
            inst = self.state.card_by_id(masters[0])

        self._log_action(player, f'master: {inst.name}')
        self._play_card(player, inst, 'ash_heap')

        # Trifle: gain +1 master phase action only if it's the FIRST master card played
        if _is_trifle(inst) and not master_card_played:
            player.master_actions += 1
            self._log_action(player, 'trifle: +1 master action')

    # ── Minion phase ───────────────────────────────────────────────

    def execute_minion(self, bots: dict[int, Bot]) -> None:
        self.events.emit(
            GameEvent(
                type=EventType.phase_changed,
                data={'phase': 'minion'},
            )
        )
        for player in self.state.active_players:
            if self.state.is_finished:
                return
            bot = bots.get(player.id)
            if not bot:
                continue
            self._player_minion_phase(player, bot)

    def _player_minion_phase(self, player: PlayerState, bot: Bot) -> None:
        """Execute minion phase for a player.
        
        Each ready unlocked minion can perform one action.
        Basic actions (bleed, hunt) are intrinsic - no card required.
        Hunt is mandatory for vampires with 0 blood.
        """
        ready_minions = self._get_ready_minions(player.id)
        if not ready_minions:
            self._log_action(player, 'skip (no ready minions)')
            return

        # First, handle mandatory actions (hunt for vampires with 0 blood)
        for minion in ready_minions:
            if self.state.is_finished:
                return
            if minion.blood == 0 and self._is_vampire(minion):
                self._resolve_hunt(minion)
                minion.lock()

        # Then, handle non-mandatory actions for remaining ready minions
        for minion in self._get_ready_minions(player.id):
            if self.state.is_finished:
                return
            self._minion_action(minion, player, bot)

    def _get_ready_minions(self, player_id: int) -> list[CardInstance]:
        """Get all ready unlocked minions for a player."""
        prefix = f'p{player_id}_'
        return [
            c for c in self.state.cards.values()
            if c.id.startswith(prefix)
            and c.is_ready
        ]

    def _is_vampire(self, minion: CardInstance) -> bool:
        """Check if a minion is a vampire."""
        return minion.tipo in ('Vampire', 'vampire', 'Imbued')

    def _is_ally(self, minion: CardInstance) -> bool:
        """Check if a minion is an ally."""
        return minion.tipo == 'Ally'

    def _minion_action(self, minion: CardInstance, player: PlayerState, bot: Bot) -> None:
        """Have a minion perform an action.
        
        Basic intrinsic actions (no card required):
        - Bleed: Any ready minion
        - Hunt: Any ready vampire (mandatory if blood == 0)
        
        Action card actions (require card in hand):
        - Equip, Employ Retainer, Recruit Ally, Political Action, etc.
        """
        # Check if minion has already acted this turn
        if minion.has_acted_this_turn:
            return

        # Bot chooses action type
        action_type = bot.choose_action_type(self.state, player.id, minion.id)

        if action_type == 'bleed':
            self._resolve_bleed(minion, player)
        elif action_type == 'hunt':
            self._resolve_hunt(minion)
        else:
            # Try to play an action card
            self._play_action_card(minion, player, bot)

        # Lock the minion after acting
        minion.lock()
        minion.has_acted_this_turn = True

    def _resolve_bleed(self, minion: CardInstance, player: PlayerState) -> None:
        """Resolve a bleed action from a minion.
        
        Target: prey (directed action)
        Stealth: 0 (default)
        Effect: Target loses pool equal to bleed amount (intrinsic 1 + card modifier)
        Edge: If bleed is successful against predator, gain the Edge
        """
        target = self.state.prey_of(player.id)
        if not target:
            self._log_action(player, f'{minion.name} bleed — no valid target')
            return

        # Intrinsic bleed is 1
        bleed_amount = 1 + minion.bleed
        target.pool -= bleed_amount
        self._log_action(player, f'{minion.name} bleeds {target.username} ({bleed_amount} pool)')
        self.events.emit(
            GameEvent(
                type=EventType.pool_changed,
                player_id=target.id,
                data={'delta': -bleed_amount},
            )
        )

        # Edge: if bleed is successful against the predator, gain the Edge
        predator = self.state.predator_of(player.id)
        if predator and target.id == predator.id:
            self._grant_edge(player)

        if target.pool <= 0:
            self.state.oust_player(target.id)
            self.events.emit(
                GameEvent(
                    type=EventType.player_ousted,
                    player_id=target.id,
                    data={'player_id': target.id},
                )
            )

    def _resolve_hunt(self, minion: CardInstance) -> None:
        """Resolve a hunt action from a vampire.
        
        Target: None (undirected action)
        Stealth: +1 (default)
        Effect: Vampire gains blood equal to hunt amount (intrinsic 1)
        Mandatory for vampires with 0 blood.
        """
        # Intrinsic hunt amount is 1
        hunt_amount = 1 + minion.hunt
        blood_gained = minion.add_blood(hunt_amount)
        self._log_action(
            self.state.player_by_id(self._player_id_for_minion(minion)),
            f'{minion.name} hunts (+{blood_gained} blood)',
        )
        self.events.emit(
            GameEvent(
                type=EventType.blood_changed,
                player_id=self._player_id_for_minion(minion),
                data={'card': minion.name, 'blood_gained': blood_gained},
            )
        )

    def _player_id_for_minion(self, minion: CardInstance) -> int:
        """Get the player ID that controls a minion."""
        # Minion IDs are formatted as p{player_id}_...
        parts = minion.id.split('_')
        if parts[0].startswith('p'):
            return int(parts[0][1:])
        return 0

    def _play_action_card(self, minion: CardInstance, player: PlayerState, bot: Bot) -> None:
        """Play an action card from hand for a minion action."""
        action_cards = _has_type(player.hand, self.state, _is_minion)
        if not action_cards:
            # No action card available, default to basic bleed
            self._log_action(player, f'{minion.name} defaults to bleed (no action card)')
            self._resolve_bleed(minion, player)
            return

        card_id = bot.choose_action(self.state, player.id)
        inst = self.state.card_by_id(card_id) if card_id else None

        if not inst or inst.id not in player.hand or not _is_minion(inst):
            inst = self.state.card_by_id(action_cards[0])

        tipo_lower = (inst.tipo or '').lower()

        if 'bleed' in tipo_lower:
            # Enhanced bleed with action card
            bleed_amount = 1 + inst.bleed
            target = self.state.prey_of(player.id)
            if target:
                target.pool -= bleed_amount
                self._log_action(player, f'{minion.name} bleeds {target.username} with {inst.name} ({bleed_amount} pool)')
                self._play_card(player, inst, 'ash_heap')
        elif 'political' in tipo_lower:
            self._log_action(player, f'{minion.name} political: {inst.name}')
            self._play_card(player, inst, 'ash_heap')
        else:
            self._log_action(player, f'{minion.name} action: {inst.name}')
            self._play_card(player, inst, 'ash_heap')

    def _grant_edge(self, player: PlayerState) -> None:
        """Grant the Edge to the specified player.
        If another player has it, take it first.
        If uncontrolled, claim it."""
        if player.has_edge:
            return  # Already has it

        # Take from current holder if any
        for p in self.state.players:
            if p.has_edge:
                p.has_edge = False
                self.events.emit(
                    GameEvent(
                        type=EventType.edge_lost,
                        player_id=p.id,
                        data={'player': p.username},
                    )
                )
                break
        else:
            # No one has it — claim from uncontrolled
            self.state.edge_uncontrolled = False

        player.has_edge = True
        self.events.emit(
            GameEvent(
                type=EventType.edge_gained,
                player_id=player.id,
                data={'player': player.username},
            )
        )

    # ── Influence phase ────────────────────────────────────────────

    def _uncontrolled_vampires(
        self, player: PlayerState
    ) -> list[CardInstance]:
        prefix = f'p{player.id}_'
        return [
            c
            for c in self.state.cards.values()
            if c.position == CardPosition.uncontrolled
            and c.id.startswith(prefix)
        ]

    def execute_influence(
        self, player: PlayerState, state: GameState, bots: dict[int, Bot]
    ) -> None:
        self.events.emit(
            GameEvent(
                type=EventType.phase_changed,
                data={'phase': 'influence'},
            )
        )
        turn = self.state.turn_number
        if turn <= 2:
            player.transfers = turn + 1
        else:
            player.transfers = 4

        self._player_influence_phase(player, state)

    def _player_influence_phase(
        self, player: PlayerState, state: GameState
    ) -> None:
        # 1. Move uncontrolled vampires with blood >= capacity to ready
        for inst in self._uncontrolled_vampires(player):
            if inst.blood >= inst.capacity:
                inst.position = CardPosition.ready
                inst.locked = False
                self._log_action(
                    player, f'{inst.name} moves to ready (blood {inst.blood}/{inst.capacity})'
                )

        # 2. Spend transfers to add blood to uncontrolled vampires
        uncontrolled = self._uncontrolled_vampires(player)
        for inst in uncontrolled:
            while player.transfers >= 1 and player.pool >= 1 and inst.blood < inst.capacity:
                player.transfers -= 1
                player.pool -= 1
                inst.blood += 1
                self._log_action(
                    player,
                    f'add blood to {inst.name} '
                    f'({inst.blood}/{inst.capacity}, '
                    f'{player.transfers} transfers left)',
                )

        # 2b. After adding blood, move any vampires that reached capacity to ready
        for inst in self._uncontrolled_vampires(player):
            if inst.blood >= inst.capacity:
                inst.position = CardPosition.ready
                inst.locked = False
                self._log_action(
                    player, f'{inst.name} moves to ready (blood {inst.blood}/{inst.capacity})'
                )

        # 3. Bring vampire from crypt to uncontrolled (4 transfers + 1 pool)
        if player.transfers >= 4 and player.pool >= 1 and player.crypt:
            cid = player.crypt[0]
            inst = state.card_by_id(cid)
            if inst:
                player.transfers -= 4
                player.pool -= 1
                player.crypt.remove(cid)
                inst.position = CardPosition.uncontrolled
                inst.locked = True
                inst.blood = 0
                self._log_action(
                    player,
                    f'influence {inst.name} from crypt '
                    f'({player.transfers} transfers left)',
                )
                self.events.emit(
                    GameEvent(
                        type=EventType.blood_changed,
                        player_id=player.id,
                        data={'card': inst.name, 'transfers': 4},
                    )
                )

        self._log_action(
            player,
            f'influence done ({player.transfers} transfers unused)',
        )

    # ── Discard phase ──────────────────────────────────────────────

    def execute_discard(
        self, player: PlayerState, bots: dict[int, Bot]
    ) -> None:
        self.events.emit(
            GameEvent(
                type=EventType.phase_changed,
                data={'phase': 'discard'},
            )
        )

        events = _has_type(player.hand, self.state, _is_event)
        if events:
            inst = self.state.card_by_id(events[0])
            if inst:
                self._log_action(player, f'event: {inst.name}')
                self._play_card(player, inst, 'ash_heap')
                return

        # No events to play — normal discard down to hand size
        if len(player.hand) <= 7:
            self._log_action(player, 'discard — skip')
            return

        bot = bots.get(player.id)
        if not bot:
            excess = len(player.hand) - 7
            player.hand = player.hand[:-excess]
            self._log_action(player, f'discard — auto ({excess} cards)')
            return

        to_discard = len(player.hand) - 7
        for _ in range(to_discard):
            if not player.hand:
                break
            choice = bot.choose_discard(self.state, player.id, player.hand)
            if choice in player.hand:
                player.hand.remove(choice)
                player.ash_heap.append(choice)
        self._log_action(player, f'discard — {to_discard} cards')

    # ── Helpers ────────────────────────────────────────────────────

    def _play_card(
        self,
        player: PlayerState,
        inst: CardInstance,
        destination: str,
    ) -> None:
        player.hand.remove(inst.id)
        if destination == 'ash_heap':
            player.ash_heap.append(inst.id)
            inst.position = CardPosition.ash_heap
        self.events.emit(
            GameEvent(
                type=EventType.card_played,
                player_id=player.id,
                data={'card_name': inst.name, 'card_id': inst.id},
            )
        )
        # Draw replacement immediately
        self.draw_cards(player, 1)

    def _pick_random_target(
        self, player: PlayerState
    ) -> Optional[PlayerState]:
        targets = [p for p in self.state.active_players if p.id != player.id]
        return random.choice(targets) if targets else None

    def _log_action(self, player: PlayerState, message: str) -> None:
        self.events.emit(
            GameEvent(
                type=EventType.action_declared,
                player_id=player.id,
                data={
                    'player': player.username,
                    'text': message,
                },
            )
        )

    def draw_cards(self, player: PlayerState, count: int) -> list[str]:
        drawn = []
        for _ in range(count):
            if not player.library:
                self._shuffle_ash_into_library(player)
                if not player.library:
                    break
            card_id = player.library.pop(0)
            player.hand.append(card_id)
            drawn.append(card_id)
        return drawn

    @staticmethod
    def _shuffle_ash_into_library(player: PlayerState) -> None:
        if player.ash_heap:
            player.library = player.ash_heap[:]
            player.ash_heap = []
            random.shuffle(player.library)
