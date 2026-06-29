from __future__ import annotations

from typing import Optional

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.events import EventBus, EventType, GameEvent
from gehenna_api.engine.state import GameState, Phase, PlayerState

# Impulse system registry for card playability in game windows
try:
    from gehenna_api.data.cards.impulse_registry import (
        get_card_playability,
        get_window_effect,
    )
except ImportError:
    # Fallback if registry module doesn't exist yet
    def get_card_playability(card_name): return None  # type: ignore
    def get_window_effect(effect_name): return None  # type: ignore


MASTER_TIPOS = {'master'}

EVENT_TIPOS = {'event'}

TRIFLE_TIPOS = {'trifle', 'master/trifle'}

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
    'action',
    'action modifier',
    'political action',
    'equipment',
    'retainer',
    'ally',
    'conviction',
    'power',
    'imbued',
    'combo',
    'action / combat',
    'action / reaction',
    'action modifier / combat',
    'action modifier / reaction',
    'action modifier/combat',
    'action modifier/reaction',
    'action/combat',
    'reaction/action modifier',
    'reaction/combat',
    'combat / action',
    'combat/action modifier',
    'combat/reaction',
}

MINION_TIPOS = {
    'action',
    'action modifier',
    'political action',
    'reaction',
    'equipment',
    'retainer',
    'ally',
    'conviction',
    'power',
    'imbued',
    'combo',
    'action / combat',
    'action / reaction',
    'action modifier / combat',
    'action modifier / reaction',
    'action modifier/combat',
    'action modifier/reaction',
    'action/combat',
    'reaction/action modifier',
    # Additional aliases
    'equipment ',
    'retainer ',
    'ally ',
    'action/equipment',
    'action/retainer',
    'action/ally',
    'combat',
    'combat / action',
    'combat/action modifier',
    'combat/reaction',
    'ranged',
    'reaction/combat',
}

# Action card types (cards a minion can play as an action)
# Excludes Action Modifier, Reaction, Combat (pure) - those are played
# at different times during an action or combat
ACTION_TIPOS = {
    'action',
    'political action',
    'equipment',
    'retainer',
    'ally',
    'action / combat',
    'action / reaction',
    'action/combat',
    'action/equipment',
    'action/retainer',
    'action/ally',
    'equipment ',
    'retainer ',
    'ally ',
}

COMBAT_ONLY = {'combat'}

COMBAT_TIPOS = {
    'combat',
    'combat / action',
    'combat/action modifier',
    'combat/reaction',
}


def _tipo_key(raw: str) -> str:
    return raw.strip().lower()


def _is_master(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in MASTER_TIPOS


def _is_event(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in EVENT_TIPOS


def _is_minion(inst: CardInstance) -> bool:
    # Cards with "Action" (including "Action/Combat" hybrids)
    # OR hybrids like "Combat / Action" that have action abilities
    return _tipo_key(inst.tipo) in MINION_TIPOS


def _is_action_card(inst: CardInstance) -> bool:
    """Check if a card is an action card a minion can play."""
    return _tipo_key(inst.tipo) in ACTION_TIPOS


def _is_combat_only(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in COMBAT_ONLY


def _is_trifle(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in TRIFLE_TIPOS


def _is_master_or_trifle(inst: CardInstance) -> bool:
    return _tipo_key(inst.tipo) in ALL_MASTER_TIPOS


def _is_action_modifier(inst: CardInstance) -> bool:
    """Check if a card is an action modifier."""
    return _tipo_key(inst.tipo) in (
        'action modifier', 'action modifier / combat', 'action modifier/combat',
        'action modifier / reaction', 'action modifier/reaction', 'action / reaction',
    )


def _is_reaction(inst: CardInstance) -> bool:
    """Check if a card is a reaction card."""
    return _tipo_key(inst.tipo) in (
        'reaction', 'reaction/action modifier', 'reaction/combat', 'action / reaction',
    )


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
        player = self.state.current_player
        
        for card in self.state.cards.values():
            if card.position == CardPosition.ready:
                # Infernal minions do not unlock normally
                # Controller must burn 1 pool to unlock them
                if card.is_infernal:
                    # Auto-unlock Infernal if player has pool (bot behavior)
                    # In real game, player chooses whether to pay
                    if player and player.pool > 0:
                        player.pool -= 1
                        card.locked = False
                        self._log_action(
                            player,
                            f'{card.name} unlocks (Infernal, burned 1 pool)',
                        )
                        self.events.emit(
                            GameEvent(
                                type=EventType.pool_changed,
                                player_id=player.id,
                                data={'delta': -1, 'reason': 'infernal_unlock'},
                            )
                        )
                else:
                    card.locked = False

        if player:
            # Player with Edge gains 1 pool from blood bank
            if player.has_edge:
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
        player = self.state.current_player
        if not player or self.state.is_finished:
            return
        bot = bots.get(player.id)
        if bot:
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

    def _can_play_master(self, player: PlayerState, inst: CardInstance) -> bool:
        """Check if a master card can be played by the player."""
        # Reaction masters (like Direct Intervention) cannot be played during
        # the master phase; they are played out-of-turn in response to actions.
        if getattr(inst, 'master_type', None) == 'reaction':
            return False

        # Attached masters (Villein, Vessel, Blood Doll, etc.) require a ready
        # vampire you control to attach to
        if getattr(inst, 'master_type', None) == 'attached':
            has_ready_vampire = any(
                c.is_ready and c.tipo in ('Vampire', 'vampire', 'Imbued')
                for c in self.state.get_cards_in_play(player.id)
            )
            if not has_ready_vampire:
                return False

        # Unique cards: can't play a second copy if already in play by this player
        if inst.is_unique:
            name_lower = inst.name.lower()
            for c in self.state.cards.values():
                if (c.id != inst.id
                        and c.id.startswith(f'p{player.id}_')
                        and c.name.lower() == name_lower
                        and c.position in ('ready', 'attached', 'in_play')):
                    return False

        return True

    def _use_master_action(self, player: PlayerState, bot: Bot, master_card_played: bool) -> None:
        player.master_actions -= 1

        masters = _has_type(player.hand, self.state, _is_master_or_trifle)
        if not masters:
            self._log_action(player, 'pass (no master in hand)')
            return

        # Filter masters that can actually be played
        playable_masters = []
        for mid in masters:
            inst = self.state.card_by_id(mid)
            if inst and self._can_play_master(player, inst):
                playable_masters.append(mid)

        if not playable_masters:
            self._log_action(player, f'pass (no valid master to play)')
            return

        card_id = bot.choose_action(self.state, player.id)
        inst = self.state.card_by_id(card_id) if card_id else None

        if not inst or inst.id not in player.hand or not _is_master_or_trifle(inst):
            # Bot picked wrong type - use first valid master/trifle
            if playable_masters:
                inst = self.state.card_by_id(playable_masters[0])
            else:
                self._log_action(player, 'pass (no valid master)')
                return

        if not self._can_play_master(player, inst):
            # Master can't be played (e.g., Villein without vampire)
            self._log_action(player, f'pass ({inst.name} cannot be played)')
            return

        self._log_action(player, f'master: {inst.name}')

        # Determine master placement based on master_type
        master_type = getattr(inst, 'master_type', None)
        if master_type == 'attached':
            # Attach to a vampire (e.g., Villein, Blood Doll)
            target = self._choose_attachment_target(player, inst)
            if target:
                inst.attached_to = target.id
                target.attachments.append(inst.id)
                inst.position = 'attached'
                # Remove from hand when attached
                if inst.id in player.hand:
                    player.hand.remove(inst.id)
                    self.draw_cards(player, 1)
                self._log_action(player, f'{inst.name} attached to {target.name}')
                # Apply attached master effects (blood_capacity, etc.)
                self._apply_master_effects(player, inst)
            else:
                # No valid target, burn the card
                inst.position = 'ash_heap'
                if inst.id in player.hand:
                    player.hand.remove(inst.id)
                    self.draw_cards(player, 1)
                self._log_action(player, f'{inst.name} burned (no valid target)')
        elif master_type == 'permanent':
            # Permanent master stays in ready region
            inst.position = 'ready'
            # Remove from hand when put in play
            if inst.id in player.hand:
                player.hand.remove(inst.id)
                self.draw_cards(player, 1)
            self._log_action(player, f'{inst.name} in play (permanent)')
            # Apply permanent master effects
            self._apply_master_effects(player, inst)
        else:
            # Default: apply effect then burn
            self._apply_master_effects(player, inst)
            self._play_card(player, inst, 'ash_heap')

        # Trifle: gain +1 master phase action only if it's the FIRST master card played
        if _is_trifle(inst) and not master_card_played:
            player.master_actions += 1
            self._log_action(player, 'trifle: +1 master action')

    def _apply_master_effects(self, player: PlayerState, inst: CardInstance) -> None:
        """Apply effects from a master card."""
        # Effects can be in inst.effects or inst.abilities[*].effects
        # Normalize to dicts (CardEffect dataclass objects are converted)
        effects: list[dict] = []
        for e in inst.effects:
            if isinstance(e, dict):
                effects.append(e)
            else:
                effects.append({'function': getattr(e, 'function', ''), 'params': getattr(e, 'params', {})})
        abilities = getattr(inst, 'abilities', []) or []
        for ability in abilities:
            ability_effects = getattr(ability, 'effects', []) or []
            for ae in ability_effects:
                if isinstance(ae, dict):
                    effects.append(ae)
                else:
                    effects.append({'function': getattr(ae, 'function', ''), 'params': getattr(ae, 'params', {})})
        
        for effect in effects:
            func = effect.get('function', '')
            params = effect.get('params', {})
            if func == 'master.hand_size':
                # Increase hand size permanently
                old_size = player.hand_size
                player.hand_size += params.get('value', 1)
                # Draw cards to fill to the new hand size
                cards_to_draw = min(
                    player.hand_size - old_size,
                    player.hand_size - len(player.hand),
                )
                if cards_to_draw > 0:
                    self.draw_cards(player, cards_to_draw)
                self._log_action(
                    player,
                    f'{inst.name}: hand size +{params.get("value", 1)} (now {player.hand_size})',
                )
            elif func == 'master.uncontrolled_add_blood':
                # Move blood from blood bank to an uncontrolled vampire
                amount = params.get('amount', 1)
                min_capacity = params.get('min_capacity', 0)
                self._resolve_uncontrolled_add_blood(player, inst, amount, min_capacity)
            elif func == 'master.blood_capacity':
                # Increase target vampire's blood capacity (e.g., Vessel)
                # Target is already set via _use_master_action's attachment logic
                value = params.get('value', 1)
                target = self.state.card_by_id(getattr(inst, 'attached_to', ''))
                if target:
                    old_cap = target.capacity
                    target.capacity += value
                    self._log_action(
                        player,
                        f'{target.name}: blood capacity +{value} ({old_cap} → {target.capacity})',
                    )

    def _choose_attachment_target(self, player: PlayerState, inst: CardInstance) -> CardInstance | None:
        """Choose a target minion for an attached master card."""
        # Find ready vampires the player controls
        targets = [
            c for c in self.state.get_cards_in_play(player.id)
            if c.is_ready and c.tipo in ('Vampire', 'vampire', 'Imbued')
        ]
        if not targets:
            return None
        # Prefer vampires without attachments
        for t in targets:
            if not t.attachments:
                return t
        # Otherwise use first available
        return targets[0]

    def _resolve_uncontrolled_add_blood(
        self,
        player: PlayerState,
        inst: CardInstance,
        amount: int,
        min_capacity: int,
    ) -> None:
        """Move blood from blood bank to an uncontrolled vampire with capacity >= min_capacity.

        Effect used by: Zillah's Valley (move 4 blood to uncontrolled vampire cap 8+).
        """
        # Find uncontrolled vampires meeting the capacity requirement
        targets = [
            c for c in self.state.cards.values()
            if c.position == CardPosition.uncontrolled
            and c.id.startswith(f'p{player.id}_')
            and c.tipo in ('Vampire', 'vampire', 'Imbued')
            and c.capacity >= min_capacity
        ]

        if not targets:
            self._log_action(
                player,
                f'{inst.name}: no valid target (need uncontrolled vampire capacity {min_capacity}+)',
            )
            return

        # Pick the uncontrolled vampire closest to capacity (best use of blood)
        target = max(targets, key=lambda c: c.capacity - c.blood)

        # Transfer blood from blood bank to the target
        blood_to_add = min(amount, target.capacity - target.blood)
        if blood_to_add <= 0:
            self._log_action(
                player,
                f'{inst.name}: {target.name} already at full capacity',
            )
            return

        self.state.blood_bank -= blood_to_add
        target.blood += blood_to_add

        self._log_action(
            player,
            f'{inst.name}: {blood_to_add} blood to {target.name} '
            f'({target.blood}/{target.capacity})',
        )

        # Check if target reaches capacity and moves to ready
        if target.blood >= target.capacity:
            target.position = CardPosition.ready
            target.locked = False
            self._log_action(
                player,
                f'{target.name} moves to ready (blood {target.blood}/{target.capacity})',
            )

    # ── Minion phase ───────────────────────────────────────────────

    def execute_minion(self, bots: dict[int, Bot]) -> None:
        self.events.emit(
            GameEvent(
                type=EventType.phase_changed,
                data={'phase': 'minion'},
            )
        )
        player = self.state.current_player
        if not player or self.state.is_finished:
            return
        bot = bots.get(player.id)
        self._player_minion_phase(player, bots)

    def _player_minion_phase(self, player: PlayerState, bots: dict[int, Bot]) -> None:
        """Execute minion phase for a player.
        
        Each ready unlocked minion can perform one action.
        Basic actions (bleed, hunt) are intrinsic - no card required.
        Only ready unlocked minions can perform actions (rules).
        Vampires in torpor cannot act.
        
        Note: If a minion unlocks during this phase (due to card effects),
        it can perform another action (rules).
        """
        # Process minions in waves - keep checking for newly unlocked minions
        processed_this_wave = set()
        
        while True:
            ready_minions = self._get_ready_minions(player.id)
            # Filter out minions already processed this wave
            new_minions = [m for m in ready_minions if m.id not in processed_this_wave]
            
            if not new_minions:
                break
            
            for minion in new_minions:
                if self.state.is_finished:
                    return
                if minion.has_acted_this_turn:
                    processed_this_wave.add(minion.id)
                    continue
                    
                # Mandatory actions (hunt for vampires with 0 blood)
                if minion.blood == 0 and self._is_vampire(minion):
                    self._resolve_hunt(minion)
                    minion.lock()
                    processed_this_wave.add(minion.id)
                    continue
                
                # Non-mandatory actions
                self._minion_action(minion, player, bots)
                processed_this_wave.add(minion.id)
        
        if not processed_this_wave:
            self._log_action(player, 'skip (no ready minions)')

    def _get_ready_minions(self, player_id: int) -> list[CardInstance]:
        """Get all ready unlocked minions (Vampire/Imbued/Ally) for a player.
        Excludes non-minion permanents like Master locations."""
        minion_tipos = {'Vampire', 'vampire', 'Imbued', 'Ally'}
        prefix = f'p{player_id}_'
        return [
            c for c in self.state.cards.values()
            if c.id.startswith(prefix)
            and c.is_ready
            and c.tipo.strip() in minion_tipos
        ]

    def _get_torpor_minions(self, player_id: int) -> list[CardInstance]:
        """Get all minions (Vampire/Imbued/Ally) in torpor for a player."""
        minion_tipos = {'Vampire', 'vampire', 'Imbued', 'Ally'}
        prefix = f'p{player_id}_'
        return [
            c for c in self.state.cards.values()
            if c.id.startswith(prefix)
            and c.position == CardPosition.torpor
            and c.tipo.strip() in minion_tipos
        ]

    def _is_vampire(self, minion: CardInstance) -> bool:
        """Check if a minion is a vampire."""
        return minion.tipo in ('Vampire', 'vampire', 'Imbued')

    @staticmethod
    def _minion_has_discipline(minion: CardInstance, discipline: str) -> bool:
        """Check if a minion has a discipline at the required level.

        discipline format examples:
          'pre'  -> basic Presence
          'PRE'  -> superior Presence
        """
        if not minion.disciplines:
            return False
        return discipline in minion.disciplines.split('|')

    def _is_ally(self, minion: CardInstance) -> bool:
        """Check if a minion is an ally."""
        return minion.tipo == 'Ally'

    def _minion_action(
        self,
        minion: CardInstance,
        player: PlayerState,
        bots: dict[int, Bot],
    ) -> None:
        """Have a minion perform an action with full action resolution.

        Action resolution with impulse system (V:TES rules):
        1. Announce action (lock acting minion)
        2. [WINDOW as_announced] — out-of-turn masters, wake, reflex
        3. Block attempt phase with [WINDOW block_attempt]
           (stealth modifiers + intercept reactions in impulse cycle)
        4. [WINDOW after_blocks] — action modifiers (bleed, etc.) after blocks
        5. [WINDOW before_resolution] — reactions (Deflection, etc.)
        6. Resolve action
        """
        if minion.has_acted_this_turn:
            return

        bot = bots.get(player.id)
        if not bot:
            return

        action_type = bot.choose_action_type(self.state, player.id, minion.id)
        action_info = self._get_action_info(action_type, minion, player)

        # For action cards, peek at the card now so the announcement includes its name
        if action_type == 'action_card':
            action_cards = _has_type(player.hand, self.state, _is_action_card)
            if action_cards:
                card_id = bot.choose_action(self.state, player.id)
                inst = self.state.card_by_id(card_id) if card_id else None
                if not inst or inst.id not in player.hand or not _is_action_card(inst):
                    inst = self.state.card_by_id(action_cards[0])
                if inst:
                    action_info['name'] = inst.name
                    action_info['_action_card'] = inst.id
                    # Equipment / Retainer / Ally actions get +1 stealth by default
                    t = inst.tipo.strip().lower()
                    if t in ('equipment', 'retainer', 'ally'):
                        action_info['stealth'] = 1 + minion.stealth
                        action_info['directed'] = False

        # Create shared context for impulse windows
        context = {
            'minion': minion,
            'acting_player': player,
            'action_type': action_type,
            'action_info': action_info,
            'is_directed': action_info.get('directed', False),
        }

        # Step 1: Announce action
        self._log_action(player, f'{minion.name} announces {action_info["name"]}')
        minion.lock()

        # Step 2: [WINDOW as_announced]
        # Out-of-turn masters (Direct Intervention), wake effects, reflex cards
        self._process_window('as_announced', player, context, bots)

        if context.get('cancelled'):
            self._log_action(
                player, f'{action_info["name"]} cancelled'
            )
            minion.unlock()
            minion.has_acted_this_turn = False
            return

        # Step 3: Block attempt phase with [WINDOW block_attempt]
        # During block attempts, acting minion plays stealth modifiers
        # and blocking minion plays intercept reactions in impulse cycle
        blocked, blocker = self._resolve_block_attempts(
            minion, player, action_info, bots, context
        )

        if blocked:
            self._log_action(
                player, f'{action_info["name"]} blocked by {blocker.name}'
            )
            self._start_combat(minion, blocker)
            minion.has_acted_this_turn = True
            return

        # Step 4: [WINDOW after_blocks]
        # Action modifiers (bleed enhancers, etc.) after blocks declined
        self._process_window('after_blocks', player, context, bots)

        # Step 5: [WINDOW before_resolution]
        # Reactions can be played by other Methuselahs' minions
        # before the action resolves (Deflection, Delaying Tactics, etc.)
        self._process_window('before_resolution', player, context, bots)

        if context.get('cancelled'):
            self._log_action(
                player, f'{action_info["name"]} cancelled'
            )
            minion.unlock()
            minion.has_acted_this_turn = False
            return

        # Step 7: Resolve action
        if '_action_card' in action_info:
            action_info['resolve'](minion, player, bot, action_info)
        else:
            action_info['resolve'](minion, player, bot)
        minion.has_acted_this_turn = True

    def _play_stealth_modifiers(
        self, minion: CardInstance, player: PlayerState, action_info: dict, bot: Bot
    ) -> list:
        """Play stealth action modifiers reactively during a block attempt.

        The acting minion may play stealth modifiers when someone tries
        to block, to increase stealth and avoid the block.
        """
        mods = []
        mod_cards = _has_type(player.hand, self.state, _is_action_modifier)
        for mod_id in mod_cards:
            mod_card = self.state.card_by_id(mod_id)
            if not mod_card or mod_card.stealth <= 0:
                continue
            cost = mod_card.pool_cost if mod_card.pool_cost > 0 else 0
            if minion.blood < cost:
                continue
            minion.blood -= cost
            if mod_card.id in player.hand:
                player.hand.remove(mod_card.id)
            mod_card.position = CardPosition.ash_heap
            mods.append(mod_card)
            self._log_action(
                player,
                f'{minion.name} plays {mod_card.name} (stealth modifier)',
            )
            break  # one stealth modifier per block attempt
        return mods

    def _play_block_reactions(
        self, blocker: CardInstance, blocker_player: PlayerState,
        action_info: dict, bot: Bot,
    ) -> None:
        """Play reaction cards during a block attempt to increase intercept.

        The blocking minion can play up to one reaction card that grants
        intercept to help block the action.
        """
        for cid in blocker_player.hand:
            card = self.state.card_by_id(cid)
            if not card:
                continue
            if card.tipo.strip().lower() != 'reaction':
                continue
            if card.intercept > 0:
                if cid in blocker_player.hand:
                    blocker_player.hand.remove(cid)
                card.position = CardPosition.ash_heap
                action_info['reaction_intercept'] = (
                    action_info.get('reaction_intercept', 0) + card.intercept
                )
                self._log_action(
                    blocker_player,
                    f'{blocker.name} plays {card.name} (reaction)',
                )
                break  # one reaction per block attempt

    def _play_action_modifiers(
        self, minion: CardInstance, player: PlayerState, action_info: dict, bot: Bot
    ) -> list:
        """Play action modifiers for an action (after blocks are declined).

        Action modifiers are played by the acting minion (or other minions
        controlled by the same Methuselah for 'other than acting minion' cards).

        Returns list of modifier cards played.
        """
        modifiers = []
        # Check hand for action modifier cards
        mod_cards = _has_type(player.hand, self.state, _is_action_modifier)
        if not mod_cards:
            return modifiers

        # Bot decides whether to play a modifier (simplified: always play if available)
        for mod_id in mod_cards:
            mod_card = self.state.card_by_id(mod_id)
            if not mod_card:
                continue
            # Skip pure stealth modifiers after blocks are declined
            # Per VTES rules, stealth can only be increased during a block attempt
            if mod_card.stealth > 0 and mod_card.bleed == 0:
                continue
            # Check if minion can pay the cost
            cost = mod_card.pool_cost if mod_card.pool_cost > 0 else 0
            if minion.blood < cost:
                continue
            # Play the modifier
            minion.blood -= cost
            if mod_card.id in player.hand:
                player.hand.remove(mod_card.id)
            mod_card.position = CardPosition.ash_heap
            modifiers.append(mod_card)
            self._log_action(
                player,
                f'{minion.name} plays {mod_card.name} (action modifier)',
            )
            # Only one modifier per action (simplified)
            break

        return modifiers

    def _apply_modifier_effects(self, action_info: dict, modifiers: list) -> None:
        """Apply effects of action modifiers to the action."""
        for mod in modifiers:
            # Apply stealth bonus
            action_info['stealth'] = action_info.get('stealth', 0) + mod.stealth
            # Apply bleed bonus
            if 'bleed_bonus' not in action_info:
                action_info['bleed_bonus'] = 0
            action_info['bleed_bonus'] += mod.bleed
            # Apply intercept bonus (for reaction-like modifiers)
            action_info['intercept_bonus'] = action_info.get('intercept_bonus', 0) + mod.intercept

    def _play_reactions(
        self, minion: CardInstance, player: PlayerState, action_info: dict, bot: Bot
    ) -> list:
        """Play reaction cards in response to an action.

        Reactions are played by ready unlocked minions controlled by
        other Methuselahs (not the acting minion's controller).

        Returns list of reaction cards played.
        """
        reactions = []

        # Determine who can play reactions
        # For directed actions: only the target can play reactions
        # For undirected actions: prey and predator can play reactions
        reaction_players = self._get_reaction_players(player.id, action_info)

        for rp in reaction_players:
            if rp.is_ousted:
                continue
            rp_bot = None  # Would need bot for this player
            # Check for reaction cards in hand
            react_cards = _has_type(rp.hand, self.state, _is_reaction)
            if not react_cards:
                continue
            # Simplified: play first available reaction
            for react_id in react_cards:
                react_card = self.state.card_by_id(react_id)
                if not react_card:
                    continue
                # Check cost
                cost = react_card.pool_cost if react_card.pool_cost > 0 else 0
                # Find a ready unlocked minion to pay the cost
                ready_minions = [
                    c for c in self.state.cards.values()
                    if c.id.startswith(f'p{rp.id}_') and c.is_ready
                ]
                payer = None
                for rm in ready_minions:
                    if rm.blood >= cost:
                        payer = rm
                        break
                if not payer:
                    continue
                # Play the reaction
                payer.blood -= cost
                if react_card.id in rp.hand:
                    rp.hand.remove(react_card.id)
                react_card.position = CardPosition.ash_heap
                reactions.append(react_card)
                self._log_action(
                    rp,
                    f'{payer.name} plays {react_card.name} (reaction)',
                )
                # Apply reaction effects
                self._apply_single_reaction(action_info, react_card)
                break  # One reaction per player per action

        return reactions

    def _get_reaction_players(self, acting_player_id: int, action_info: dict) -> list:
        """Get list of players who can react to an action."""
        players = []
        acting_player = self.state.player_by_id(acting_player_id)

        if action_info.get('directed'):
            # Directed: only target can react
            target = self.state.prey_of(acting_player_id)
            if target and not target.is_ousted:
                players.append(target)
        else:
            # Undirected: prey first, then predator
            prey = self.state.prey_of(acting_player_id)
            predator = self.state.predator_of(acting_player_id)
            if prey and not prey.is_ousted:
                players.append(prey)
            if predator and not predator.is_ousted:
                players.append(predator)

        return players

    def _apply_single_reaction(self, action_info: dict, react_card: CardInstance) -> None:
        """Apply effects of a single reaction card."""
        # Reactions can increase intercept (making block easier)
        action_info['reaction_intercept'] = action_info.get('reaction_intercept', 0) + react_card.intercept
        # Reactions can increase stealth (making action harder to block)
        action_info['reaction_stealth'] = action_info.get('reaction_stealth', 0) + react_card.stealth

    def _apply_reaction_effects(self, action_info: dict, reactions: list) -> None:
        """Apply effects of all reaction cards."""
        # Effects already applied in _apply_single_reaction
        pass

    def _get_action_info(self, action_type: str, minion: CardInstance, player: PlayerState) -> dict:
        """Get action properties for an action type."""
        if action_type == 'bleed':
            prey = self.state.prey_of(player.id)
            is_directed = prey is not None
            info = {
                'name': f'bleed' + (f' {prey.username}' if prey else ''),
                'stealth': minion.stealth,
                'directed': is_directed,
                'resolve': lambda m, p, b: self._resolve_bleed_action(m, p, info),
            }
            return info
        elif action_type == 'hunt':
            return {
                'name': 'hunt',
                'stealth': 1 + minion.stealth,
                'directed': False,
                'resolve': lambda m, p, b: self._resolve_hunt(m),
            }
        elif action_type == 'leave_torpor':
            return {
                'name': 'leave torpor',
                'stealth': 1 + minion.stealth,
                'directed': False,
                'resolve': lambda m, p, b: self._resolve_leave_torpor(m, p),
            }
        elif action_type == 'rescue':
            target = self._find_torpor_target(minion, player)
            is_directed = target is not None and self._player_id_for_minion(target) != player.id
            stealth = 0 + minion.stealth if is_directed else 1 + minion.stealth
            return {
                'name': f'rescue {target.name}' if target else 'rescue',
                'stealth': stealth,
                'directed': is_directed,
                'resolve': lambda m, p, b: self._resolve_rescue(m, p, target),
            }
        elif action_type == 'diablerie':
            target = self._find_torpor_target(minion, player)
            is_directed = target is not None and self._player_id_for_minion(target) != player.id
            stealth = 0 + minion.stealth if is_directed else 1 + minion.stealth
            return {
                'name': f'diablerize {target.name}' if target else 'diablerie',
                'stealth': stealth,
                'directed': is_directed,
                'resolve': lambda m, p, b: self._resolve_diablerie(m, p, target),
            }
        elif action_type == 'political':
            return {
                'name': 'political action',
                'stealth': 1 + minion.stealth,
                'directed': False,
                'resolve': lambda m, p, b: self._resolve_political_action(m, p),
            }
        else:
            return {
                'name': 'action',
                'stealth': minion.stealth,
                'directed': False,
                'resolve': lambda m, p, b, ai=None: self._play_action_card(m, p, b, ai),
            }

    def _find_torpor_target(self, minion: CardInstance, player: PlayerState) -> Optional[CardInstance]:
        """Find a vampire in torpor that can be targeted by rescue or diablerie."""
        # First look for own vampires in torpor
        prefix = f'p{player.id}_'
        for c in self.state.cards.values():
            if c.id.startswith(prefix) and c.position == CardPosition.torpor:
                if c.tipo in ('Vampire', 'vampire', 'Imbued'):
                    return c
        # Then look for other players' vampires in torpor
        for c in self.state.cards.values():
            if c.position == CardPosition.torpor:
                if c.tipo in ('Vampire', 'vampire', 'Imbued'):
                    return c
        return None

    def _resolve_block_attempts(
        self,
        minion: CardInstance,
        player: PlayerState,
        action_info: dict,
        bots: dict[int, Bot],
        context: dict,
    ) -> tuple[bool, Optional[CardInstance]]:
        """Resolve block attempts for an action using impulse windows.

        Uses the [WINDOW block_attempt] to manage the stealth/intercept
        impulse cycle between the acting minion and the blocker.

        Returns (blocked, blocker):
        - blocked: True if action was blocked
        - blocker: The CardInstance that blocked (None if not blocked)

        Rules:
        - Directed actions: Only target Methuselah can block
        - Undirected actions: Prey and Predator can block (prey first)
        - Block succeeds if blocker's intercept >= acting minion's stealth
        - Blocker must be ready and unlocked
        """
        bot = bots.get(player.id)

        # Determine who can block
        potential_blockers = []

        if action_info['directed']:
            # Directed: only target can block
            target = self.state.prey_of(player.id)
            if target:
                for b in self._get_blocking_minions(target.id, context):
                    if b not in potential_blockers:
                        potential_blockers.append(b)
        else:
            # Undirected: prey first, then predator
            prey = self.state.prey_of(player.id)
            predator = self.state.predator_of(player.id)
            seen_players = set()
            for who in (prey, predator):
                if who and who.id not in seen_players:
                    seen_players.add(who.id)
                    potential_blockers.extend(self._get_blocking_minions(who.id, context))

        # Check if any potential blocker can intercept
        for blocker in potential_blockers:
            blocker_player = self.state.player_by_id(
                self._player_id_for_minion(blocker)
            )
            if not blocker_player:
                continue

            # Pre-check: skip if blocker has no chance of blocking
            acting_stealth = action_info['stealth']
            potential_intercept = blocker.intercept
            for cid in blocker_player.hand:
                c = self.state.card_by_id(cid)
                if c and c.tipo.strip().lower() == 'reaction' and c.intercept > 0:
                    potential_intercept += c.intercept
                    break
            if potential_intercept < acting_stealth:
                continue

            # Bot decides whether to attempt block
            should_block = bot.choose_block(
                self.state, blocker_player.id, minion.id
            )

            if not should_block:
                continue

            # Blocker attempts to block — open block_attempt window
            # with impulse cycling between acting player and blocker
            action_info['reaction_intercept'] = 0
            context['modifier_stealth'] = 0
            context['reaction_intercept'] = 0

            block_context = {
                **context,
                'blocker': blocker,
                'blocker_player': blocker_player,
            }

            self._process_window('block_attempt', player, block_context, bots)

            # Recalculate after impulse window completed
            modifier_stealth = block_context.get('modifier_stealth', 0)
            action_info['stealth'] = action_info.get('stealth', 0) + modifier_stealth
            reaction_intercept = block_context.get('reaction_intercept', 0)
            acting_stealth = action_info['stealth']
            blocker_intercept = blocker.intercept + reaction_intercept

            if blocker_intercept >= acting_stealth:
                blocker.lock()
                return True, blocker
            else:
                self._log_action(
                    blocker_player,
                    f'{blocker.name} fails to block {minion.name} '
                    f'(intercept {blocker_intercept} < stealth {acting_stealth})'
                )

        return False, None

    def _get_blocking_minions(
        self,
        player_id: int,
        context: dict | None = None,
    ) -> list[CardInstance]:
        """Get all minions that can block for a player.

        Returns ready unlocked minions (Vampire/Imbued/Ally) plus any
        woken minions (locked ready minions that were woken by cards
        like On the Qui Vive or Wake with Evening's Freshness).
        """
        minion_tipos = {'Vampire', 'vampire', 'Imbued', 'Ally'}
        prefix = f'p{player_id}_'
        woken_ids = set(context.get('woken_minions', [])) if context else set()

        result = []
        for c in self.state.cards.values():
            if not c.id.startswith(prefix):
                continue
            if c.tipo.strip() not in minion_tipos:
                continue
            # Normal ready unlocked minions
            if c.is_ready:
                result.append(c)
            # Woken minions (locked but awoken by a wake effect)
            elif c.position == CardPosition.ready and c.id in woken_ids:
                result.append(c)
        return result

    def _start_combat(self, attacker: CardInstance, defender: CardInstance) -> None:
        """Start and resolve combat between two minions.

        Combat sequence (per round):
        1. Before Range - play cards before range is chosen
        2. Determine Range - close (default) or long via maneuvers
        3. Before Strikes - play cards before strikes
        4. Strike - each minion chooses and resolves strike
        5. Damage Resolution - prevent and mend damage
        6. Press - continue or end combat
        7. End of Round - end of round effects
        """
        attacker_player = self.state.player_by_id(self._player_id_for_minion(attacker))
        defender_player = self.state.player_by_id(self._player_id_for_minion(defender))

        self.events.emit(
            GameEvent(
                type=EventType.combat_started,
                data={'attacker': attacker.name, 'defender': defender.name},
            )
        )

        round_num = 0
        max_rounds = 20
        while round_num < max_rounds:
            round_num += 1
            combat_ended = self._execute_combat_round(
                attacker, defender, attacker_player, defender_player, round_num
            )
            if combat_ended:
                break
            if not self._is_combatant_ready(attacker) or not self._is_combatant_ready(defender):
                break

        self.events.emit(
            GameEvent(
                type=EventType.combat_ended,
                data={
                    'attacker': attacker.name,
                    'defender': defender.name,
                    'rounds': round_num,
                },
            )
        )

    def _execute_combat_round(
        self,
        attacker: CardInstance,
        defender: CardInstance,
        attacker_player: PlayerState,
        defender_player: PlayerState,
        round_num: int,
    ) -> bool:
        """Execute one round of combat with full 7-step sequence.

        Returns True if combat ended.
        """
        # Reset per-round combat state
        attacker.damage_prevented = 0
        defender.damage_prevented = 0
        attacker.additional_strikes = 0
        defender.additional_strikes = 0
        attacker.maneuvers = 0
        defender.maneuvers = 0
        attacker.first_strike = False
        defender.first_strike = False
        attacker.ranged = False
        defender.ranged = False

        # Step 1: Before Range - play cards before range is determined
        self._play_before_range(attacker, defender, attacker_player, defender_player)

        # Step 2: Determine Range via maneuvers (close default, long via maneuvers)
        current_range = self._determine_range(attacker, defender, attacker_player, defender_player)

        # Step 3: Before Strikes - play combat cards before strikes
        self._play_before_strikes(attacker, defender, attacker_player, defender_player, current_range)

        # Step 4: Strike - acting minion chooses first, then defender
        # Attacker chooses without knowing defender's choice
        atk_strike = self._choose_strike(attacker, defender, current_range, is_attacker=True)
        # Defender chooses knowing attacker's strike
        def_strike = self._choose_strike(defender, attacker, current_range, is_attacker=False, opponent_strike=atk_strike)

        # Resolve strikes (includes first strike resolution order)
        combat_ended = self._resolve_strikes(
            attacker, defender, atk_strike, def_strike, current_range
        )
        if combat_ended:
            return True

        # Step 5: Damage Resolution (handled in take_damage)
        if not self._is_combatant_ready(attacker) or not self._is_combatant_ready(defender):
            return True

        # Step 6: Press - check if combat continues
        combat_continues = self._play_press(attacker, defender, attacker_player, defender_player)
        if not combat_continues:
            return True

        # Step 7: End of Round (placeholder)
        return False

    def _choose_strike(
        self,
        striker: CardInstance,
        opponent: CardInstance,
        current_range: str,
        is_attacker: bool,
        opponent_strike: dict | None = None,
    ) -> dict:
        """Choose a strike for a minion.

        Checks the controlling player's hand for combat cards that
        can be used as strikes. The bot chooses between available
        options.

        Strike types:
        - hand_strike: damage = strength, close range only
        - dodge: 0 damage, protects from opponent's strike, any range
        - combat_ends: ends combat immediately, any range, resolves first
        - steal_blood: steals blood, not damage, any range
        - first_strike: resolves before normal strikes
        - ranged: works at any range

        Default: hand_strike.

        If opponent_strike is provided (defender choosing after attacker),
        the minion can make smarter decisions based on opponent's choice.
        """
        player_id = self._player_id_for_minion(striker)
        player = self.state.player_by_id(player_id)
        bot = None  # We don't have the bot reference here, use fallback

        # Look for combat cards in player's hand
        combat_cards = [
            self.state.card_by_id(cid)
            for cid in player.hand
            if _is_combat_only(self.state.card_by_id(cid))
        ] if player else []
        combat_cards = [c for c in combat_cards if c is not None]

        if combat_cards:
            # Pick first available combat card as strike
            for c in combat_cards:
                strike_type = self._classify_combat_strike(c, current_range, striker)
                if strike_type:
                    # Play the card
                    if c.id in player.hand:
                        player.hand.remove(c.id)
                        self.draw_cards(player, 1)
                    c.position = CardPosition.ash_heap
                    self._log_action(
                        player,
                        f'{striker.name} plays {c.name} (combat)',
                    )
                    return strike_type

        # Special: The Unnamed can burn 1 blood for 2R aggravated strike
        if 'strike_blood_for_aggravated' in striker.special_effects and striker.blood >= 1:
            striker.blood -= 1
            self._log_action(
                player,
                f'{striker.name} burns 1 blood for 2R aggravated strike',
            )
            return {
                'type': 'hand_strike',
                'damage': 2,
                'aggravated': True,
                'ranged': True,
                'steal_amount': 0,
                'dodge': False,
                'combat_ends': False,
                'first_strike': False,
            }

        # Fallback: basic hand strike
        return {
            'type': 'hand_strike',
            'damage': striker.strength,
            'aggravated': False,
            'steal_amount': 0,
            'dodge': False,
            'combat_ends': False,
            'first_strike': False,
            'ranged': False,
        }

    def _resolve_strikes(
        self,
        attacker: CardInstance,
        defender: CardInstance,
        atk_strike: dict,
        def_strike: dict,
        current_range: str,
    ) -> bool:
        """Resolve strikes from both combatants.

        Resolution order:
        1. Combat Ends (resolves first, before everything)
        2. First Strike (resolves before normal strikes)
        3. Normal Strikes (simultaneous)

        Returns True if combat ended.
        """
        # Combat ends resolves first, before everything else
        if atk_strike.get('combat_ends'):
            self._log_action(
                self.state.player_by_id(self._player_id_for_minion(attacker)),
                f'{attacker.name} plays combat ends',
            )
            return True
        if def_strike.get('combat_ends'):
            self._log_action(
                self.state.player_by_id(self._player_id_for_minion(defender)),
                f'{defender.name} plays combat ends',
            )
            return True

        # Determine strike properties
        atk_dodges = atk_strike.get('dodge', False)
        def_dodges = def_strike.get('dodge', False)
        atk_first = atk_strike.get('first_strike', False)
        def_first = def_strike.get('first_strike', False)
        atk_ranged = atk_strike.get('ranged', False)
        def_ranged = def_strike.get('ranged', False)

        # Resolve steal_blood (happens before damage, not preventable)
        if atk_strike.get('steal_amount', 0) > 0:
            self._steal_blood(attacker, defender, atk_strike['steal_amount'])
        if def_strike.get('steal_amount', 0) > 0:
            self._steal_blood(defender, attacker, def_strike['steal_amount'])

        # Determine effective ranges
        atk_effective_range = current_range if not atk_ranged else 'any'
        def_effective_range = current_range if not def_ranged else 'any'

        # Resolve strikes based on first strike
        # If both have first strike, resolve simultaneously
        # If only one has first strike, that one resolves first
        if atk_first and def_first:
            # Both first strike - resolve simultaneously
            self._apply_strike_damage(attacker, defender, atk_strike, def_strike, atk_effective_range, def_dodges)
            self._apply_strike_damage(defender, attacker, def_strike, atk_strike, def_effective_range, atk_dodges)
        elif atk_first:
            # Attacker strikes first
            self._apply_strike_damage(attacker, defender, atk_strike, def_strike, atk_effective_range, def_dodges)
            # Check if defender is still alive to strike back
            if self._is_combatant_ready(defender):
                self._apply_strike_damage(defender, attacker, def_strike, atk_strike, def_effective_range, atk_dodges)
        elif def_first:
            # Defender strikes first
            self._apply_strike_damage(defender, attacker, def_strike, atk_strike, def_effective_range, atk_dodges)
            # Check if attacker is still alive to strike back
            if self._is_combatant_ready(attacker):
                self._apply_strike_damage(attacker, defender, atk_strike, def_strike, atk_effective_range, def_dodges)
        else:
            # No first strike - resolve simultaneously
            self._apply_strike_damage(attacker, defender, atk_strike, def_strike, atk_effective_range, def_dodges)
            self._apply_strike_damage(defender, attacker, def_strike, atk_strike, def_effective_range, atk_dodges)

        # Log dodges
        if atk_dodges:
            self._log_action(
                self.state.player_by_id(self._player_id_for_minion(attacker)),
                f'{attacker.name} dodges',
            )
        if def_dodges:
            self._log_action(
                self.state.player_by_id(self._player_id_for_minion(defender)),
                f'{defender.name} dodges',
            )

        return False

    def _apply_strike_damage(
        self,
        striker: CardInstance,
        target: CardInstance,
        strike: dict,
        opponent_strike: dict,
        effective_range: str,
        opponent_dodges: bool,
    ) -> None:
        """Apply damage from a strike to the target."""
        if opponent_dodges:
            return

        strike_type = strike.get('type', 'hand_strike')

        # Torpor strike: send opponent to torpor
        if strike_type == 'torpor':
            target.take_damage(target.blood + 1)  # enough to send to torpor
            player = self.state.player_by_id(self._player_id_for_minion(striker))
            self._log_action(
                player,
                f'{striker.name} sends {target.name} to torpor',
            )
            return

        # Burn ally: remove ally from game
        if strike_type == 'burn_ally':
            target.position = CardPosition.ash_heap
            player = self.state.player_by_id(self._player_id_for_minion(striker))
            self._log_action(
                player,
                f'{striker.name} burns {target.name}',
            )
            return

        # Combat ends, dodge, etc. - no damage
        if strike_type not in ('hand_strike',):
            return

        if effective_range not in ('close', 'any'):
            return

        # Special effect: The Unnamed can burn 1 blood for 2R aggravated
        dmg = strike['damage']
        aggravated = strike.get('aggravated', False)
        if 'strike_blood_for_aggravated' in striker.special_effects and striker.blood >= 1:
            if not aggravated:  # Only apply if not already aggravated
                striker.blood -= 1
                aggravated = True
                dmg = 2
                self._log_action(
                    self.state.player_by_id(self._player_id_for_minion(striker)),
                    f'{striker.name} burns 1 blood for 2R aggravated strike',
                )

        if dmg > 0:
            target.take_damage(dmg, aggravated)
            dmg_type = 'aggravated' if aggravated else 'normal'
            self._log_action(
                self.state.player_by_id(self._player_id_for_minion(target)),
                f'{target.name} takes {dmg} {dmg_type} damage from {striker.name}',
            )

    def _steal_blood(self, thief: CardInstance, victim: CardInstance, amount: int) -> None:
        """Steal blood from victim and give to thief."""
        stolen = min(amount, victim.blood)
        if stolen <= 0:
            return
        victim.blood -= stolen
        thief.add_blood(stolen)
        self._log_action(
            self.state.player_by_id(self._player_id_for_minion(thief)),
            f'{thief.name} steals {stolen} blood from {victim.name}',
        )

    def _is_combatant_ready(self, minion: CardInstance) -> bool:
        """Check if a minion is still ready for combat."""
        return minion.position == CardPosition.ready and minion.blood > 0

    def _play_before_range(
        self, attacker: CardInstance, defender: CardInstance,
        attacker_player: PlayerState, defender_player: PlayerState,
    ) -> None:
        """Step 1: Play combat cards before range is determined.

        Both combatants may play cards that grant maneuvers
        or affect the upcoming range determination.
        """
        # Attacker plays first
        self._play_combat_before_range(attacker, attacker_player, is_attacker=True)
        self._play_combat_before_range(defender, defender_player, is_attacker=False)

    def _play_combat_before_range(
        self, minion: CardInstance, player: PlayerState,
        is_attacker: bool,
    ) -> None:
        """Play combat cards that grant maneuvers before range."""
        combat_cards = [
            self.state.card_by_id(cid)
            for cid in player.hand
            if _is_combat_only(self.state.card_by_id(cid))
        ] if player else []
        combat_cards = [c for c in combat_cards if c is not None]
        for c in combat_cards:
            if c.maneuvers > 0:
                if c.id in player.hand:
                    player.hand.remove(c.id)
                    self.draw_cards(player, 1)
                c.position = CardPosition.ash_heap
                self._log_action(player, f'{minion.name} plays {c.name} (combat)')
                minion.maneuvers += c.maneuvers
                break

    def _classify_combat_strike(
        self, card: CardInstance, current_range: str, striker: CardInstance
    ) -> dict | None:
        """Classify a combat card into a strike dict based on its name."""
        name = (card.name or '').lower()

        # Strike: dodge
        if 'mist' in name or 'dodge' in name:
            return {
                'type': 'dodge',
                'damage': 0,
                'aggravated': False,
                'steal_amount': 0,
                'dodge': True,
                'combat_ends': False,
                'first_strike': False,
                'ranged': False,
            }

        # Strike: combat ends
        if any(kw in name for kw in ('meld', 'oubliette', 'shadow body', 'earth')):
            return {
                'type': 'combat_ends',
                'damage': 0,
                'aggravated': False,
                'steal_amount': 0,
                'dodge': False,
                'combat_ends': True,
                'first_strike': False,
                'ranged': False,
            }

        # Strike: torpor (send opposing vampire to torpor)
        if 'entomb' in name or 'torpor' in name:
            return {
                'type': 'torpor',
                'damage': striker.strength,
                'aggravated': False,
                'steal_amount': 0,
                'dodge': False,
                'combat_ends': False,
                'first_strike': False,
                'ranged': False,
            }

        return None

    def _play_combat_before_strikes(
        self, minion: CardInstance, player: PlayerState,
        current_range: str,
    ) -> None:
        """Play combat cards that buff before strikes."""
        pass

    def _try_press(self, minion: CardInstance, player: PlayerState) -> bool:
        """Check if a minion can and wants to press (continue combat)."""
        name = (minion.name or '').lower()
        # Simplified: check if minion has abilities that allow press
        # (e.g., certain weapons or combat cards)
        # For now, default to no press
        return False

    def _determine_range(
        self, attacker: CardInstance, defender: CardInstance,
        attacker_player: PlayerState, defender_player: PlayerState,
    ) -> str:
        """Step 2: Determine combat range via maneuvers.

        Default is close range. Maneuvers can change to long range.
        Acting minion maneuvers first, then defender.
        A minion cannot play two maneuvers in a row.
        """
        current_range = 'close'

        # Check for weapons/combat cards that grant maneuvers
        atk_maneuvers = self._count_maneuvers(attacker)
        def_maneuvers = self._count_maneuvers(defender)

        # Acting minion maneuvers first
        if atk_maneuvers > 0:
            current_range = 'long'
            self._log_action(attacker_player, f'{attacker.name} maneuvers to long range')

        # Defender can counter-maneuver
        if def_maneuvers > 0:
            # Defender counters: if attacker went long, defender can go close
            if current_range == 'long':
                current_range = 'close'
                self._log_action(defender_player, f'{defender.name} maneuvers back to close range')
            else:
                current_range = 'long'
                self._log_action(defender_player, f'{defender.name} maneuvers to long range')

        # Additional maneuvers (if both have more than 1)
        # Simplified: only one maneuver exchange per round

        return current_range

    def _count_maneuvers(self, minion: CardInstance) -> int:
        """Count available maneuvers for a minion.

        From weapons attached to the minion.
        """
        maneuvers = minion.maneuvers  # Base maneuvers from card
        # Check attached weapons/equipment for maneuvers
        if minion.attachments:
            for att_id in minion.attachments:
                att = self.state.card_by_id(att_id)
                if att:
                    maneuvers += getattr(att, 'maneuvers', 0)
        return maneuvers

    def _play_before_strikes(
        self, attacker: CardInstance, defender: CardInstance,
        attacker_player: PlayerState, defender_player: PlayerState,
        current_range: str,
    ) -> None:
        """Step 3: Play combat cards before strikes.

        Acting minion plays first, then defender.
        Cards can: increase strength, grant first strike, grant additional strikes, etc.
        """
        # Attacker plays first
        self._play_combat_before_strikes(attacker, attacker_player, current_range)
        self._play_combat_before_strikes(defender, defender_player, current_range)

    def _play_additional_strikes(
        self, attacker: CardInstance, defender: CardInstance,
        attacker_player: PlayerState, defender_player: PlayerState,
        current_range: str,
    ) -> None:
        """Handle additional strikes after the first pair.

        Acting minion decides first, then defender.
        """
        atk_strikes = attacker.additional_strikes
        def_strikes = defender.additional_strikes

        # Resolve additional strikes
        # Simplified: skip for now
        pass

    def _play_damage_prevention(
        self, minion: CardInstance, player: PlayerState, damage: int
    ) -> int:
        """Step 5b: Play damage prevention cards.

        Returns remaining damage after prevention.
        """
        prevented = minion.damage_prevented
        remaining = max(0, damage - prevented)
        if prevented > 0:
            self._log_action(
                player,
                f'{minion.name} prevents {minimized} damage',
            )
        return remaining

    def _play_press(
        self, attacker: CardInstance, defender: CardInstance,
        attacker_player: PlayerState, defender_player: PlayerState,
    ) -> bool:
        """Step 6: Press phase.

        Returns True if combat should continue.
        Acting minion decides first, then defender.
        """
        # Attacker decides first
        if self._try_press(attacker, attacker_player):
            self._log_action(attacker_player, f'{attacker.name} presses')
            # Defender can counter-press
            if self._try_press(defender, defender_player):
                self._log_action(defender_player, f'{defender.name} presses back')
                return True
            return True
        # Defender can press if attacker doesn't
        if self._try_press(defender, defender_player):
            self._log_action(defender_player, f'{defender.name} presses')
            return True
        return False

    def _resolve_bleed_action(
        self,
        minion: CardInstance,
        player: PlayerState,
        action_info: dict | None = None,
    ) -> None:
        """Resolve a bleed action from a minion (after successful block attempt resolution).

        Target: prey (directed action), or redirect target from Deflection.
        Effect: Target loses pool equal to bleed amount (intrinsic 1 + card modifier)
        Edge: If bleed is successful against predator, gain the Edge

        Special: The Unnamed (201411) gains 2 pool after successful bleed.
        """
        # Determine target (supports redirect from Deflection)
        redirect_to_id = None
        if action_info:
            redirect_to_id = action_info.get('redirect_to')

        if redirect_to_id:
            target = self.state.player_by_id(redirect_to_id)
        else:
            target = self.state.prey_of(player.id)

        if not target:
            self._log_action(player, f'{minion.name} bleed - no valid target')
            return

        # Intrinsic bleed is 1
        bleed_amount = 1 + minion.bleed
        if action_info:
            bleed_amount += action_info.get('bleed_bonus', 0)
        target.pool -= bleed_amount
        target_name = f'{target.username} (redirected)' if redirect_to_id else target.username
        self._log_action(player, f'{minion.name} bleeds {target_name} ({bleed_amount} pool)')
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

        # Special effect: The Unnamed gains 2 pool after successful bleed
        if 'bleed_gain_pool' in minion.special_effects:
            pool_gain = 2
            player.pool += pool_gain
            self._log_action(player, f'{minion.name} gains {pool_gain} pool from successful bleed')
            self.events.emit(
                GameEvent(
                    type=EventType.pool_changed,
                    player_id=player.id,
                    data={'delta': pool_gain, 'reason': 'unnamed_bleed'},
                )
            )

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

    def _resolve_leave_torpor(self, minion: CardInstance, player: PlayerState) -> None:
        """Resolve a leave torpor action.

        Cost: 2 blood (paid by the acting vampire)
        Effect: Vampire moves from torpor to ready, unlocked.
        The vampire must have at least 2 blood to attempt this.
        """
        if minion.blood < 2:
            self._log_action(
                player,
                f'{minion.name} cannot leave torpor (needs 2 blood, has {minion.blood})',
            )
            return

        minion.blood -= 2
        minion.position = CardPosition.ready
        minion.locked = False
        minion.damage_taken = 0
        self._log_action(
            player,
            f'{minion.name} leaves torpor (burned 2 blood)',
        )

    def _resolve_rescue(
        self, minion: CardInstance, player: PlayerState, target: Optional[CardInstance]
    ) -> None:
        """Resolve a rescue from torpor action.

        Cost: 2 blood (can be split between acting and rescued vampire)
        Effect: Target vampire moves from torpor to ready, unlocked.
        The rescued vampire does not lock or unlock.
        """
        if target is None:
            self._log_action(player, f'{minion.name} rescue - no valid target')
            return

        # Check if acting vampire can pay (simplified: acting vampire pays)
        if minion.blood < 2:
            self._log_action(
                player,
                f'{minion.name} cannot rescue (needs 2 blood, has {minion.blood})',
            )
            return

        minion.blood -= 2
        target.position = CardPosition.ready
        target.locked = False
        target.damage_taken = 0
        self._log_action(
            player,
            f'{minion.name} rescues {target.name} from torpor',
        )

    def _resolve_diablerie(
        self, minion: CardInstance, player: PlayerState, target: Optional[CardInstance]
    ) -> None:
        """Resolve a diablerie action.

        Cost: None
        Effect:
        1. All blood on victim moves to diablerist
        2. Victim is burned (cards and counters burned)
        3. If victim was older (higher capacity), diablerist may gain a Discipline
        """
        if target is None:
            self._log_action(player, f'{minion.name} diablerie - no valid target')
            return

        # Step 1: Move all blood from victim to diablerist
        blood_stolen = target.blood
        if blood_stolen > 0:
            minion.add_blood(blood_stolen)
            target.blood = 0

        # Step 2: Burn the victim
        target.position = CardPosition.ash_heap
        target.blood = 0
        target.damage_taken = 0

        self._log_action(
            player,
            f'{minion.name} diablerizes {target.name}',
        )

        # Step 3: Check if victim was older (higher capacity)
        if target.capacity > minion.capacity:
            # Diablerist gains +1 capacity (simplified - no Discipline card search)
            minion.capacity += 1
            self._log_action(
                player,
                f'{minion.name} grows stronger (capacity {minion.capacity - 1} -> {minion.capacity})',
            )

        # Blood hunt referendum after diablerie
        self._call_blood_hunt(player.id)

    def _resolve_political_action(
        self, minion: CardInstance, player: PlayerState
    ) -> None:
        """Resolve a political action.

        Cost: blood cost listed on the political action card.
        Effect: Call a referendum.

        Rules:
        - Only one political action per turn per vampire
        - Undirected action (can be blocked by prey/predator)
        - If successful, a referendum is called
        - Terms of referendum chosen after action succeeds
        """
        # Mark political action as used
        player.political_action_used = True

        # Find and pay for political action card in hand
        pol_card_id = None
        for cid in player.hand:
            card = self.state.card_by_id(cid)
            if card and card.tipo.strip().lower() == 'political action':
                pol_card_id = cid
                # Pay blood cost
                cost = card.pool_cost if card.pool_cost > 0 else 0
                minion.blood -= cost
                # Remove from hand and burn
                player.hand.remove(cid)
                self.draw_cards(player, 1)
                card.position = CardPosition.ash_heap
                break

        if pol_card_id is None:
            self._log_action(player, f'{minion.name} has no political action card')
            return

        # Create and conduct referendum
        referendum = self._call_referendum(player, minion)

        if referendum['passed']:
            self._log_action(
                player,
                f'{minion.name} calls referendum: {referendum["name"]} - PASSED',
            )
            self._resolve_referendum_effects(referendum, player)
        else:
            self._log_action(
                player,
                f'{minion.name} calls referendum: {referendum["name"]} - FAILED',
            )

    def _call_referendum(
        self, player: PlayerState, minion: CardInstance
    ) -> dict:
        """Conduct a referendum.

        Steps:
        1. Polling - cards usable before votes are cast
        2. Votes - all Methuselahs cast votes
        3. Resolve - if more for than against, passes

        Returns dict with referendum results.
        """
        # Gather votes from all players
        votes_for = 0
        votes_against = 0
        vote_log = []

        for p in self.state.active_players:
            player_votes = self._count_votes(p)
            # Simplified: acting player votes for, others vote against
            if p.id == player.id:
                votes_for += player_votes
                vote_log.append(f'{p.username}: +{player_votes} for')
            else:
                # Other players vote against (simplified)
                votes_against += player_votes
                vote_log.append(f'{p.username}: +{player_votes} against')

        passed = votes_for > votes_against

        return {
            'name': 'Referendum',
            'caller': player.username,
            'votes_for': votes_for,
            'votes_against': votes_against,
            'passed': passed,
            'vote_log': vote_log,
        }

    def _count_votes(self, player: PlayerState) -> int:
        """Count votes for a player.

        Sources:
        - Political action cards (1 vote each, max 1 per player)
        - Titles: Primogen (1), Prince/Baron (2), Justicar (3), Inner Circle (4)
        - Edge (1 vote if burned)
        - Ready titled vampires
        """
        votes = player.votes

        # Add title votes
        if player.has_title:
            title_votes = {
                'primogen': 1,
                'prince': 2,
                'baron': 2,
                'justicar': 3,
                'inner_circle': 4,
            }
            votes += title_votes.get(player.has_title.lower(), 0)

        # Count ready titled minions
        prefix = f'p{player.id}_'
        for c in self.state.cards.values():
            if c.id.startswith(prefix) and c.is_ready and c.tipo in ('Vampire', 'vampire', 'Imbued'):
                # Check if vampire has a title (simplified)
                if hasattr(c, 'title') and c.title:
                    votes += title_votes.get(c.title.lower(), 0)

        return votes

    def _resolve_referendum_effects(self, referendum: dict, caller: PlayerState) -> None:
        """Resolve the effects of a passed referendum.

        Simplified: just log the result.
        Full implementation would apply specific referendum effects.
        """
        # Placeholder for specific referendum effects
        pass

    def _call_blood_hunt(self, diablerist_id: int) -> bool:
        """Call a blood hunt referendum after diablerie.

        Automatic referendum (not an action, cannot be blocked).
        If passed, the diablerist is burned.

        Returns True if blood hunt passes (diablerist is burned).
        """
        diablerist = self.state.player_by_id(diablerist_id)
        if not diablerist:
            return False

        # Blood hunt: all players vote
        # Simplified: blood hunt passes if majority votes for
        votes_for = 0
        votes_against = 0

        for p in self.state.active_players:
            if p.id == diablerist_id:
                # Diablerist votes against their own blood hunt
                votes_against += self._count_votes(p)
            else:
                # Others vote for (simplified)
                votes_for += self._count_votes(p)

        passed = votes_for > votes_against

        if passed:
            self._log_action(
                diablerist,
                f'Blood hunt called on {diablerist.username} - PASSED',
            )
            # Burn the diablerist
            self._burn_player(diablerist_id)
        else:
            self._log_action(
                diablerist,
                f'Blood hunt called on {diablerist.username} - FAILED',
            )

        return passed

    def _burn_player(self, player_id: int) -> None:
        """Burn a player (blood hunt execution).

        All cards controlled by the player are burned.
        Player is ousted.
        """
        player = self.state.player_by_id(player_id)
        if not player:
            return

        # Burn all controlled cards
        prefix = f'p{player_id}_'
        for c in self.state.cards.values():
            if c.id.startswith(prefix):
                c.position = CardPosition.ash_heap
                c.blood = 0
                c.life = 0

        # Oust the player
        player.is_ousted = True
        player.pool = 0
        player.blood_hunt_active = False

        self._log_action(player, f'{player.username} is burned by blood hunt')

    def _player_id_for_minion(self, minion: CardInstance) -> int:
        """Get the player ID that controls a minion."""
        parts = minion.id.split('_')
        if parts[0].startswith('p'):
            return int(parts[0][1:])
        return 0

    def _play_action_card(self, minion: CardInstance, player: PlayerState, bot: Bot, action_info: dict | None = None) -> None:
        """Play an action card from hand for a minion action.

        Handles: bleed, equip, employ retainer, recruit ally, political, combat.
        """
        action_cards = _has_type(player.hand, self.state, _is_action_card)
        if not action_cards:
            self._log_action(player, f'{minion.name} defaults to bleed (no action card)')
            self._resolve_bleed(minion, player)
            return

        # Use pre-selected card if available (from announcement phase)
        pre_selected_id = (action_info or {}).get('_action_card')
        if pre_selected_id and pre_selected_id in player.hand:
            inst = self.state.card_by_id(pre_selected_id)
        else:
            card_id = bot.choose_action(self.state, player.id)
            inst = self.state.card_by_id(card_id) if card_id else None

        if not inst or inst.id not in player.hand or not _is_action_card(inst):
            inst = self.state.card_by_id(action_cards[0])

        tipo_lower = (inst.tipo or '').lower()

        if 'bleed' in tipo_lower:
            self._resolve_bleed_with_card(minion, player, inst)
        elif 'equipment' in tipo_lower or 'equip' in tipo_lower:
            self._resolve_equip(minion, player, inst)
        elif 'retainer' in tipo_lower:
            self._resolve_employ_retainer(minion, player, inst)
        elif 'ally' in tipo_lower:
            self._resolve_recruit_ally(minion, player, inst)
        elif 'political' in tipo_lower:
            self._log_action(player, f'{minion.name} political: {inst.name}')
            self._play_card(player, inst, 'ash_heap')
        else:
            # Generic action card — check abilities for discipline-based effects
            effect_desc = self._resolve_action_card_abilities(minion, player, inst)
            if effect_desc:
                self._log_action(player, f'{minion.name} action: {inst.name} ({effect_desc})')
            else:
                self._log_action(player, f'{minion.name} action: {inst.name}')
            self._play_card(player, inst, 'ash_heap')

    def _resolve_action_card_abilities(
        self,
        minion: CardInstance,
        player: PlayerState,
        card: CardInstance,
    ) -> str | None:
        """Check a generic action card's abilities, find which ones the
        minion qualifies for (discipline-based), apply available modifier
        effects (bleed, stealth, intercept), and return a description of
        the selected effect.

        Returns a short description string like '+1 bleed' or '+1 stealth',
        or None if no abilities match.
        """
        abilities = getattr(card, 'abilities', []) or []
        if not abilities:
            return None

        # Find which abilities the minion qualifies for
        usable: list[dict] = []
        for ab in abilities:
            if isinstance(ab, dict):
                disciplines = ab.get('disciplines', [])
            else:
                disciplines = getattr(ab, 'disciplines', None) or []
            if not disciplines:
                usable.append(ab)
                continue
            # Check if minion has any of the required disciplines
            for disc in disciplines:
                if self._minion_has_discipline(minion, disc):
                    usable.append(ab)
                    break

        if not usable:
            return None

        # Pick the highest-level ability (prefer superior disciplines)
        def _disc_level(ab) -> int:
            if isinstance(ab, dict):
                discs = ab.get('disciplines', [])
            else:
                discs = getattr(ab, 'disciplines', None) or []
            # Superior (uppercase) = 2, basic (lowercase) = 1, none = 0
            return max((2 if d.isupper() else 1) for d in discs) if discs else 0

        chosen = max(usable, key=_disc_level)

        # Get effects from the chosen ability
        if isinstance(chosen, dict):
            effects = chosen.get('effects', [])
        else:
            effects = getattr(chosen, 'effects', None) or []

        effect_desc_parts: list[str] = []
        for eff in effects:
            if isinstance(eff, dict):
                func = eff.get('function', '')
                params = eff.get('params', {})
                text = eff.get('text', '')
            else:
                func = getattr(eff, 'function', None) or ''
                params = getattr(eff, 'params', None) or {}
                text = getattr(eff, 'text', None) or ''

            if func == 'modifier.bleed':
                bonus = params.get('value', 1)
                minion.bleed += bonus
                effect_desc_parts.append(f'+{bonus} bleed')
            elif func == 'modifier.stealth':
                bonus = params.get('value', 1)
                minion.stealth += bonus
                effect_desc_parts.append(f'+{bonus} stealth')
            elif func == 'modifier.intercept':
                bonus = params.get('value', 1)
                minion.intercept += bonus
                effect_desc_parts.append(f'+{bonus} intercept')
            else:
                if text:
                    effect_desc_parts.append(text)

        return ', '.join(effect_desc_parts) if effect_desc_parts else None

    def _resolve_bleed_with_card(self, minion: CardInstance, player: PlayerState, card: CardInstance) -> None:
        """Resolve an enhanced bleed using an action card."""
        bleed_amount = 1 + card.bleed
        target = self.state.prey_of(player.id)
        if target:
            target.pool -= bleed_amount
            self._log_action(player, f'{minion.name} bleeds {target.username} with {card.name} ({bleed_amount} pool)')
            self._play_card(player, card, 'ash_heap')
            # Edge: if bleed is successful against the predator, gain the Edge
            predator = self.state.predator_of(player.id)
            if predator and target.id == predator.id:
                self._grant_edge(player)
        else:
            self._log_action(player, f'{minion.name} bleed with {card.name} - no valid target')
            self._play_card(player, card, 'ash_heap')

    def _resolve_equip(self, minion: CardInstance, player: PlayerState, card: CardInstance) -> None:
        """Resolve an equip action.

        Cost: blood cost listed on the equipment card.
        Effect: Equipment is placed on the acting minion.
        """
        # Check blood cost
        if card.pool_cost > 0:
            if minion.blood < card.pool_cost:
                self._log_action(player, f'{minion.name} cannot equip {card.name} (needs {card.pool_cost} blood)')
                return
            minion.blood -= card.pool_cost

        # Attach equipment to minion
        card.position = CardPosition.attached
        card.attached_to = minion.id
        if minion.attachments is None:
            minion.attachments = []
        minion.attachments.append(card.id)
        # Remove from hand
        if card.id in player.hand:
            player.hand.remove(card.id)
            self.draw_cards(player, 1)
        self._log_action(player, f'{minion.name} equips {card.name}')

    def _resolve_employ_retainer(self, minion: CardInstance, player: PlayerState, card: CardInstance) -> None:
        """Resolve an employ retainer action.

        Cost: blood cost listed on the retainer card.
        Effect: Retainer is placed on the acting minion with starting life.
        """
        # Check blood cost
        cost = card.pool_cost if card.pool_cost > 0 else 0
        if cost > 0:
            if minion.blood < cost:
                self._log_action(player, f'{minion.name} cannot employ {card.name} (needs {cost} blood)')
                return
            minion.blood -= cost

        # Attach retainer to minion with starting life
        card.position = CardPosition.attached
        card.attached_to = minion.id
        card.life = card.capacity  # Use capacity as starting life for retainers
        if minion.attachments is None:
            minion.attachments = []
        minion.attachments.append(card.id)
        # Remove from hand
        if card.id in player.hand:
            player.hand.remove(card.id)
            self.draw_cards(player, 1)
        self._log_action(player, f'{minion.name} employs {card.name}')

    def _resolve_recruit_ally(self, minion: CardInstance, player: PlayerState, card: CardInstance) -> None:
        """Resolve a recruit ally action.

        Cost: blood cost listed on the ally card.
        Effect: Ally is placed in ready region, cannot act this turn.
        """
        # Check blood cost
        cost = card.pool_cost if card.pool_cost > 0 else 0
        if cost > 0:
            if minion.blood < cost:
                self._log_action(player, f'{minion.name} cannot recruit {card.name} (needs {cost} blood)')
                return
            minion.blood -= cost

        # Place ally in ready region with starting life
        ally_id = f'p{player.id}_ally_{card.card_id}'
        ally = CardInstance(
            id=ally_id,
            card_id=card.card_id,
            name=card.name,
            position=CardPosition.ready,
            tipo='Ally',
            capacity=card.capacity,
            life=card.capacity,  # Start with full life
            blood=0,
            locked=True,  # Cannot act this turn
            strength=card.strength if card.strength > 0 else 1,
        )
        self.state.cards[ally_id] = ally
        # Remove card from hand
        if card.id in player.hand:
            player.hand.remove(card.id)
            self.draw_cards(player, 1)
        self._log_action(player, f'{minion.name} recruits {card.name}')

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
            # No one has it - claim from uncontrolled
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

        # No events to play - normal discard down to hand size
        max_hand = player.hand_size
        if len(player.hand) <= max_hand:
            self._log_action(player, 'discard - skip')
            return

        bot = bots.get(player.id)
        if not bot:
            excess = len(player.hand) - max_hand
            player.hand = player.hand[:-excess]
            self._log_action(player, f'discard - auto ({excess} cards)')
            return

        to_discard = len(player.hand) - max_hand
        for _ in range(to_discard):
            if not player.hand:
                break
            choice = bot.choose_discard(self.state, player.id, player.hand)
            if choice in player.hand:
                player.hand.remove(choice)
                player.ash_heap.append(choice)
        self._log_action(player, f'discard - {to_discard} cards')

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
        return self.state.random.choice(targets) if targets else None

    # =========================================================================
    # IMPULSE SYSTEM — Game Window Processing (Phase 1 Foundation)
    # =========================================================================

    def _process_window(
        self,
        window: str,
        acting_player: PlayerState | None,
        context: dict,
        bots: dict[int, Bot],
    ) -> bool:
        """Process a game window with impulse cycling.

        Iterates through players in impulse order, giving each the chance
        to play eligible cards. If any player plays a card, the acting
        player regains impulse (resets the cycle). Continues until all
        players pass consecutively.

        Args:
            window: The game window name (e.g. 'as_announced', 'block_attempt')
            acting_player: The player whose turn/action it is
            context: Shared context dict (action_info, minion, etc.)
            bots: Dict of player_id -> Bot for decision making

        Returns:
            True if the window was processed (always), False if timed out
        """
        order = self._get_impulse_order(window, acting_player, context)
        if not order:
            return False

        context['_window'] = window  # For cost lookup in helpers

        passed: set[int] = set()
        idx = 0
        rounds = 0
        max_rounds = 50  # Safety limit

        while len(passed) < len(order):
            rounds += 1
            if rounds > max_rounds:
                self._log_action(
                    acting_player,
                    f'[WARNING] Impulse window {window} timed out',
                )
                return False

            current_player = order[idx]

            if current_player.id in passed:
                idx = (idx + 1) % len(order)
                continue

            # Get cards this player can play in this window
            playables = self._get_playable_cards(
                current_player, window, context, bots
            )

            if playables:
                # Bot chooses which card to play
                card_id = self._choose_card_for_window(
                    current_player, playables, window, context, bots
                )
                if card_id:
                    card = self.state.card_by_id(card_id)
                    if card:
                        self._execute_card_in_window(
                            card, current_player, window, context
                        )
                        passed.clear()
                        # Acting player regains impulse
                        idx = 0
                        continue

            # Player passes
            passed.add(current_player.id)
            idx = (idx + 1) % len(order)

        return True

    def _get_impulse_order(
        self,
        window: str,
        acting_player: PlayerState | None,
        context: dict,
    ) -> list[PlayerState]:
        """Calculate the impulse order for a game window.

        Rules (V:TES Sequencing, p.8):
        - Acting Methuselah always has impulse first
        - During undirected action: prey first, then predator
        - Then everyone else in clockwise order
        - During block_attempt: acting minion's controller first, then blocker's
        - During after_blocks: only the acting player
        """
        if not acting_player:
            return list(self.state.players)

        # Windows restricted to acting player only
        if window == 'after_blocks':
            return [acting_player]

        # Block attempt: actives's controller then blocker's controller
        if window == 'block_attempt':
            blocker_player = context.get('blocker_player')
            result = [acting_player]
            if blocker_player and blocker_player.id != acting_player.id:
                result.append(blocker_player)
            return result

        # Full table order for announced/before_resolution/combat windows
        result = [acting_player]
        seen: set[int] = {acting_player.id}

        # Walk clockwise from acting player (prey first)
        current = self.state.prey_of(acting_player.id)
        while current and current.id not in seen:
            result.append(current)
            seen.add(current.id)
            current = self.state.prey_of(current.id)

        return result

    def _get_playable_cards(
        self,
        player: PlayerState,
        window: str,
        context: dict,
        bots: dict[int, Bot],
    ) -> list[CardInstance]:
        """Return cards in the player's hand that can be played in this window."""
        playables: list[CardInstance] = []

        for cid in list(player.hand):
            card = self.state.card_by_id(cid)
            if not card:
                continue

            if not self._can_play_in_window(card, window, context, player):
                continue

            if not self._can_afford_card(card, player, context):
                continue

            if not self._check_card_conditions(card, window, context):
                continue

            playables.append(card)

        return playables

    def _can_play_in_window(
        self,
        card: CardInstance,
        window: str,
        context: dict,
        player: PlayerState | None = None,
    ) -> bool:
        """Check if a card can be played in a specific game window.

        Priority:
        1. CARD_PLAYABILITY_REGISTRY (explicit mapping)
        2. CardInstance.playable_windows (from override JSONs)
        3. Heuristic rules by card tipo/master_type and player role

        For block_attempt window, the acting player can only play action
        modifiers (stealth), while the blocking player can only play
        reactions (intercept). This matches V:TES rules.
        """
        # 1. Check registry
        registry = get_card_playability(card.name)
        if registry:
            return window in registry.windows

        # 2. Check explicit playable_windows on the card instance
        if card.playable_windows:
            return window in card.playable_windows

        # 3. Heuristic rules
        tipo_key = card.tipo.strip().lower()
        acting_player = context.get('acting_player')
        is_acting_player = player is not None and acting_player is not None and player.id == acting_player.id
        is_out_of_turn = getattr(card, 'master_type', None) == 'reaction'

        # ── Out-of-turn master cards (e.g. Direct Intervention) ───────
        # Can be played in as_announced and before_resolution windows,
        # but NOT by the acting player (must be another player's turn)
        # and only ONE per turn cycle per player.
        if is_out_of_turn:
            if window not in ('as_announced', 'before_resolution'):
                return False
            # Cannot be played by the acting player (out-of-turn on own action)
            if is_acting_player:
                return False
            # Can only play one out-of-turn master per cycle
            if player and player.out_of_turn_master_played:
                return False
            return True

        # ── block_attempt ─────────────────────────────────────────────
        # Acting player: action modifiers with stealth
        # Blocking player: reaction cards with intercept
        if window == 'block_attempt':
            if is_acting_player:
                if tipo_key in ('action_modifier', 'action modifier'):
                    return card.stealth > 0
                return False
            else:
                if tipo_key == 'reaction':
                    return card.intercept > 0
                return False

        # ── after_blocks ──────────────────────────────────────────────
        # Only the acting player can play action modifiers (non-stealth)
        if window == 'after_blocks':
            if is_acting_player:
                if tipo_key in ('action_modifier', 'action modifier'):
                    if card.stealth > 0 and card.bleed == 0:
                        return False
                    return True
            return False

        # ── before_resolution ─────────────────────────────────────────
        # Non-acting players can play reactions
        if window == 'before_resolution':
            if not is_acting_player:
                if tipo_key == 'reaction':
                    return True
            return False

        # ── as_announced ──────────────────────────────────────────────
        # Non-acting players can play out-of-turn masters, wake, reflex
        if window == 'as_announced':
            if not is_acting_player:
                if is_out_of_turn:
                    return True
                # Wake effects (basic heuristic) can be played
                if card.name in ('Wake', 'On the Qui Vive', 'Wake with Evening\'s Freshness'):
                    return True
            return False

        return False

    def _can_afford_card(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> bool:
        """Check if the player can afford to play a card."""
        tipo_key = card.tipo.strip().lower()
        window = context.get('_window', '')

        # Check registry for cost info first
        registry = get_card_playability(card.name)
        if registry:
            if registry.cost_type == 'pool':
                return player.pool >= registry.cost_amount
            elif registry.cost_type == 'blood':
                if getattr(card, 'master_type', None) == 'reaction':
                    return player.pool >= registry.cost_amount
                minion = self._get_cost_paying_minion(card, player, context)
                return minion is not None and minion.blood >= registry.cost_amount

        # Fallback heuristic: determine cost type by card type
        cost = card.pool_cost if card.pool_cost > 0 else 0
        if cost <= 0:
            return True

        # Out-of-turn masters pay from pool
        if getattr(card, 'master_type', None) == 'reaction':
            return player.pool >= cost

        # Action modifiers: paid by the acting minion (blood)
        if tipo_key in ('action_modifier', 'action modifier'):
            minion = context.get('minion')
            return minion is not None and minion.blood >= cost

        # Reactions in block_attempt: paid by blocker (blood)
        if tipo_key == 'reaction' and window == 'block_attempt':
            blocker = context.get('blocker')
            return blocker is not None and blocker.blood >= cost

        # Reactions in before_resolution: paid by any ready minion (blood)
        if tipo_key == 'reaction' and window == 'before_resolution':
            return self._has_ready_minion_with_blood(player, cost)

        # Default: pool cost
        return player.pool >= cost

    def _get_cost_paying_minion(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> CardInstance | None:
        """Determine which minion pays the cost for a card, based on context."""
        tipo_key = card.tipo.strip().lower()
        window = context.get('_window', '')

        # Action modifiers: pay from acting minion
        if tipo_key in ('action_modifier', 'action modifier'):
            return context.get('minion')

        # Reactions in block_attempt: pay from blocker
        if tipo_key == 'reaction' and window == 'block_attempt':
            return context.get('blocker')

        # Reactions in before_resolution: pay from any ready minion
        if tipo_key == 'reaction' and window == 'before_resolution':
            cost = card.pool_cost if card.pool_cost > 0 else 0
            return self._find_ready_minion_with_blood(player, cost)

        return None

    def _has_ready_minion_with_blood(
        self, player: PlayerState, amount: int
    ) -> bool:
        """Check if the player has a ready minion with at least `amount` blood."""
        return self._find_ready_minion_with_blood(player, amount) is not None

    def _find_ready_minion_with_blood(
        self, player: PlayerState, amount: int
    ) -> CardInstance | None:
        """Find a ready minion controlled by the player with at least `amount` blood."""
        for c in self.state.cards.values():
            if (c.id.startswith(f'p{player.id}_')
                    and c.is_ready
                    and c.blood >= amount):
                return c
        return None

    def _check_card_conditions(
        self,
        card: CardInstance,
        window: str,
        context: dict,
    ) -> bool:
        """Check additional conditions from the registry for playing a card."""
        registry = get_card_playability(card.name)
        if not registry:
            return True

        for key, value in registry.conditions.items():
            if key == 'action_type':
                action_type = context.get('action_type')
                if action_type is None:
                    return False
                if isinstance(value, tuple):
                    if action_type not in value:
                        return False
                elif action_type != value:
                    return False

            elif key == 'is_directed':
                is_directed = context.get('is_directed', False)
                if is_directed != value:
                    return False

            elif key == 'minion_has_discipline':
                discipline = value
                minion = context.get('minion')
                if not minion or not self._minion_has_discipline(minion, discipline):
                    return False

        return True

    def _choose_card_for_window(
        self,
        player: PlayerState,
        cards: list[CardInstance],
        window: str,
        context: dict,
        bots: dict[int, Bot],
    ) -> str | None:
        """Choose which card to play in a window.

        Uses the player's bot if available, otherwise picks the first card.
        """
        bot = bots.get(player.id)
        if bot and hasattr(bot, 'choose_card_for_window'):
            return bot.choose_card_for_window(
                self.state, player.id, cards, window, context
            )
        # Default: play the first eligible card
        if cards:
            return cards[0].id
        return None

    def _execute_card_in_window(
        self,
        card: CardInstance,
        player: PlayerState,
        window: str,
        context: dict,
    ) -> None:
        """Execute a card's effect when played in a game window.

        Handles:
        - Paying costs
        - Removing from hand
        - Setting card position (ash_heap or bottom_of_library)
        - Calling the effect handler
        - Out-of-turn master tracking
        - Logging
        """
        # 1. Pay cost
        self._pay_window_card_cost(card, player, context)

        # 2. Remove from hand
        if card.id in player.hand:
            player.hand.remove(card.id)

        # 3. Determine effect and execute
        effect_name = ''
        registry = get_card_playability(card.name)
        if registry:
            effect_name = registry.effect
            effect_def = get_window_effect(effect_name)
            if effect_def:
                handler_name = effect_def.handler
                handler = getattr(self, handler_name, None)
                if handler:
                    handler(card, player, context)

        # 4. Position the card
        if getattr(card, 'master_type', None) == 'reaction':
            # Out-of-turn masters go to bottom of library
            card.position = CardPosition.bottom_of_library
            # Track out-of-turn master usage
            self._track_out_of_turn_master(player, card)
        else:
            card.position = CardPosition.ash_heap

        # 5. Log
        log_msg = f'{player.username} plays {card.name}'
        if window:
            log_msg += f' ({window})'
        if effect_name:
            log_msg += f' [{effect_name}]'
        self._log_action(player, log_msg)

        # 6. Emit event
        self.events.emit(
            GameEvent(
                type=EventType.card_played,
                player_id=player.id,
                data={
                    'card': card.name,
                    'window': window,
                    'effect': effect_name,
                },
            )
        )

    def _pay_window_card_cost(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Pay the cost for a card played in a game window.

        Cost resolution by priority:
        1. Registry-defined cost type and amount
        2. Heuristic by card type:
           - Out-of-turn masters: pool (from Methuselah)
           - Action modifiers: blood (from acting minion)
           - Reactions in block_attempt: blood (from blocker)
           - Reactions in before_resolution: blood (from any ready minion)
           - Default: pool
        """
        tipo_key = card.tipo.strip().lower()
        window = context.get('_window', '')

        # 1. Registry-defined cost
        registry = get_card_playability(card.name)
        if registry:
            if registry.cost_type == 'pool':
                player.pool -= registry.cost_amount
                return
            elif registry.cost_type == 'blood':
                # Out-of-turn masters with blood cost pay pool instead
                if getattr(card, 'master_type', None) == 'reaction':
                    player.pool -= registry.cost_amount
                    return
                minion = self._get_cost_paying_minion(card, player, context)
                if minion:
                    minion.blood -= registry.cost_amount
                return

        # 2. Heuristic cost
        cost = card.pool_cost if card.pool_cost > 0 else 0
        if cost <= 0:
            return

        # Out-of-turn masters pay from pool
        if getattr(card, 'master_type', None) == 'reaction':
            player.pool -= cost
            return

        # Action modifiers: paid by acting minion (blood)
        if tipo_key in ('action_modifier', 'action modifier'):
            minion = context.get('minion')
            if minion and minion.blood >= cost:
                minion.blood -= cost
            return

        # Reactions in block_attempt: paid by blocker (blood)
        if tipo_key == 'reaction' and window == 'block_attempt':
            blocker = context.get('blocker')
            if blocker and blocker.blood >= cost:
                blocker.blood -= cost
            return

        # Reactions in before_resolution: paid by any ready minion (blood)
        if tipo_key == 'reaction' and window == 'before_resolution':
            payer = self._find_ready_minion_with_blood(player, cost)
            if payer:
                payer.blood -= cost
            return

        # Default: pool cost
        if player.pool >= cost:
            player.pool -= cost

    def _track_out_of_turn_master(
        self,
        player: PlayerState,
        card: CardInstance,
    ) -> None:
        """Track that a player played an out-of-turn master card.

        Per V:TES rules:
        - Cannot play more than one out-of-turn master between own turns
        - Playing one reduces master phase actions in the next turn
        """
        if not player.out_of_turn_master_played:
            player.mark_out_of_turn_master()

    # =========================================================================
    # IMPULSE SYSTEM — Window Effect Handlers
    # =========================================================================

    def _apply_cancel_action(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Cancel the current action entirely.

        The acting minion unlocks and has_acted_this_turn is reset.
        The action card (if any) is not paid or burned.
        """
        minion = context.get('minion')
        if minion:
            minion.unlock()
            minion.has_acted_this_turn = False
        context['cancelled'] = True

    def _apply_stealth_modifier(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Add stealth from a modifier card to the action context."""
        context['modifier_stealth'] = (
            context.get('modifier_stealth', 0) + card.stealth
        )
        # Also update action_info.stealth if present
        action_info = context.get('action_info')
        if action_info:
            action_info['stealth'] = action_info.get('stealth', 0) + card.stealth

    def _apply_intercept_reaction(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Add intercept from a reaction card to the action context."""
        context['reaction_intercept'] = (
            context.get('reaction_intercept', 0) + card.intercept
        )

    def _apply_bleed_modifier(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Add bleed from a modifier card to the action context."""
        context['bleed_bonus'] = context.get('bleed_bonus', 0) + card.bleed

    def _apply_wake_minion(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Wake a locked ready minion so it can block or play reactions.

        Selects the first locked ready minion controlled by the player
        and marks it as woken for the duration of the action.
        Woken minions can attempt to block even if locked.
        """
        prefix = f'p{player.id}_'
        for c in self.state.cards.values():
            if (c.id.startswith(prefix)
                    and c.position == CardPosition.ready
                    and c.locked
                    and c.tipo.strip() in ('Vampire', 'vampire', 'Imbued', 'Ally')):
                woken = context.get('woken_minions', [])
                woken.append(c.id)
                context['woken_minions'] = woken
                self._log_action(player, f'{c.name} wakes up')
                return

        # No valid minion to wake
        self._log_action(
            player,
            f'wake failed (no locked ready minion to wake)',
        )

    def _apply_grant_intercept(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Grant intercept to a blocking minion."""
        context['reaction_intercept'] = (
            context.get('reaction_intercept', 0) + card.intercept
        )

    def _apply_redirect_bleed(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Redirect a bleed to another Methuselah.

        The bleed is redirected to the prey of the player playing this
        card (the reacting player), or to any other valid target.
        The acting minion still pays costs, but the bleed damage is
        applied to the new target.
        """
        # Choose target: prey of the player playing Deflection
        target = self.state.prey_of(player.id)
        if target and target.id != context.get('acting_player', player).id:
            context['redirect_to'] = target.id
            self._log_action(
                player,
                f'bleed redirected to {target.username}',
            )
        else:
            self._log_action(player, 'redirect bleed failed (no valid target)')

    def _apply_cancel_political(
        self,
        card: CardInstance,
        player: PlayerState,
        context: dict,
    ) -> None:
        """Cancel a political action/referendum.

        The acting minion unlocks and the action is cancelled.
        The card is removed from the action and the political
        action is stopped before the referendum is called.
        """
        minion = context.get('minion')
        if minion:
            minion.unlock()
            minion.has_acted_this_turn = False
        context['cancelled'] = True
        action_info = context.get('action_info', {})
        action_name = action_info.get('name', 'political action')
        self._log_action(
            player,
            f'{action_name} cancelled by {card.name}',
        )

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
            self.state.random.shuffle(player.library)
