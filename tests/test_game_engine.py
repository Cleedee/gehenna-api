"""Tests for the V:TES game engine."""

import pytest

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.ai.random_bot import RandomBot
from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.engine import GameEngine
from gehenna_api.engine.state import GameState, PlayerState


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def basic_state():
    """Create a basic 2-player game state."""
    state = GameState(game_id="test")
    state.edge_uncontrolled = True
    for pid in range(1, 3):
        p = PlayerState(id=pid, username=f"P{pid}", pool=30)
        for i in range(10):
            c = CardInstance(
                id=f"p{pid}_lib_{i}", card_id=100 + i, name=f"Card{pid}_{i}",
                position=CardPosition.library, tipo="Master", pool_cost=0,
            )
            state.cards[c.id] = c
            p.library.append(c.id)
        for i in range(6):
            c = CardInstance(
                id=f"p{pid}_crypt_{i}", card_id=i, name=f"Vamp{pid}_{i}",
                position=CardPosition.crypt, tipo="Vampire", capacity=5, blood=0,
            )
            state.cards[c.id] = c
            p.crypt.append(c.id)
        state.players.append(p)
    return state


@pytest.fixture
def engine(basic_state):
    """Create a started GameEngine."""
    engine = GameEngine(basic_state)
    engine.start()
    return engine


def make_ready(state, player_id, crypt_idx, blood=3, **kwargs):
    """Helper to move a crypt card to ready."""
    c = state.card_by_id(f"p{player_id}_crypt_{crypt_idx}")
    c.position = CardPosition.ready
    c.blood = blood
    c.locked = False
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


# ── Game Setup Tests ────────────────────────────────────────────────────────


class TestGameSetup:
    def test_start_draws_7_cards(self, engine):
        for p in engine.state.players:
            assert len(p.hand) == 7

    def test_start_moves_4_crypt_to_uncontrolled(self, engine):
        for p in engine.state.players:
            uncontrolled = [
                c for c in engine.state.cards.values()
                if c.id.startswith(f"p{p.id}_")
                and c.position == CardPosition.uncontrolled
            ]
            assert len(uncontrolled) == 4

    def test_start_crypt_has_2_remaining(self, engine):
        for p in engine.state.players:
            assert len(p.crypt) == 2

    def test_edge_starts_uncontrolled(self, engine):
        assert engine.state.edge_uncontrolled is True
        for p in engine.state.players:
            assert p.has_edge is False

    def test_players_start_with_30_pool(self, engine):
        for p in engine.state.players:
            assert p.pool == 30

    def test_start_sets_turn_number_0(self, engine):
        assert engine.state.turn_number == 0

    def test_start_is_running(self, basic_state):
        engine = GameEngine(basic_state)
        engine.start()
        assert engine._is_running is True


# ── Unlock Phase Tests ──────────────────────────────────────────────────────


class TestUnlockPhase:
    def test_unlock_unlocks_locked_cards(self, basic_state):
        engine = GameEngine(basic_state)
        make_ready(engine.state, 1, 0, locked=True)
        engine.phases.execute_unlock()
        c = engine.state.card_by_id("p1_crypt_0")
        assert c.locked is False

    def test_edge_gives_1_pool(self, basic_state):
        p1 = basic_state.players[0]
        p1.has_edge = True
        initial = p1.pool
        engine = GameEngine(basic_state)
        engine.phases.execute_unlock()
        assert p1.pool == initial + 1

    def test_uncontrolled_edge_granted_to_first_player(self, basic_state):
        engine = GameEngine(basic_state)
        engine.start()
        engine.phases.execute_unlock()
        # P1 (current player) should get the uncontrolled Edge
        assert basic_state.edge_uncontrolled is False
        assert basic_state.current_player.has_edge is True


# ── Master Phase Tests ──────────────────────────────────────────────────────


class TestMasterPhase:
    def test_master_plays_card(self, engine):
        p1 = engine.state.players[0]
        initial_ash = len(p1.ash_heap)
        engine.phases.execute_master({p1.id: RandomBot()})
        assert len(p1.ash_heap) == initial_ash + 1


# ── Minion Phase Tests ──────────────────────────────────────────────────────


class TestMinionPhase:
    def test_no_ready_minions_skips(self, engine):
        engine.phases.execute_minion({p.id: RandomBot() for p in engine.state.players})
        log_texts = [e["data"].get("text", "") for e in engine.log]
        assert any("skip" in t.lower() for t in log_texts)

    def test_bleed_blocked_by_interceptor(self, basic_state):
        """Bleed is blocked when blocker has intercept >= stealth."""
        make_ready(basic_state, 1, 0, blood=3)
        make_ready(basic_state, 2, 0, blood=3, intercept=5)
        # Draw cards manually (don't call start)
        for pid in range(1, 3):
            p = basic_state.players[pid - 1]
            for i in range(7):
                if p.library:
                    cid = p.library.pop(0)
                    p.hand.append(cid)
        engine = GameEngine(basic_state)
        engine._is_running = True
        bots = {p.id: RandomBot() for p in basic_state.players}
        initial_pool = basic_state.players[1].pool
        engine.phases.execute_minion(bots)
        # Block succeeds (intercept 5 >= stealth 0)
        assert basic_state.players[1].pool == initial_pool

    def test_hunt_mandatory_for_0_blood(self, basic_state):
        # Don't call start() - it moves crypt to uncontrolled
        # Set up manually instead
        c = make_ready(basic_state, 1, 0, blood=0)
        # Draw 7 library cards to hand
        p1 = basic_state.players[0]
        for i in range(7):
            if p1.library:
                cid = p1.library.pop(0)
                p1.hand.append(cid)
        engine = GameEngine(basic_state)
        engine._is_running = True
        bots = {p.id: RandomBot() for p in basic_state.players}
        engine.phases.execute_minion(bots)
        assert c.blood >= 1

    def test_minion_locks_after_action(self, basic_state):
        make_ready(basic_state, 1, 0, blood=3)
        make_ready(basic_state, 2, 0, blood=3, intercept=5)  # Will block P1
        engine = GameEngine(basic_state)
        engine.start()
        bots = {p.id: RandomBot() for p in basic_state.players}
        engine.phases.execute_minion(bots)
        c = basic_state.card_by_id("p1_crypt_0")
        assert c.locked is True


# ── Block System Tests ──────────────────────────────────────────────────────


class TestBlockSystem:
    def test_block_succeeds_intercept_ge_stealth(self, basic_state):
        """Block succeeds when intercept >= stealth."""
        make_ready(basic_state, 1, 0, blood=3, stealth=0)
        make_ready(basic_state, 2, 0, blood=3, intercept=1)
        engine = GameEngine(basic_state)
        engine.start()
        bots = {p.id: RandomBot() for p in basic_state.players}
        initial_pool = basic_state.players[1].pool
        engine.phases.execute_minion(bots)
        assert basic_state.players[1].pool == initial_pool
        assert basic_state.card_by_id("p2_crypt_0").locked is True

    def test_block_fails_intercept_lt_stealth(self, basic_state):
        """Block fails when intercept < stealth."""
        # Don't call start() - it moves crypt to uncontrolled
        make_ready(basic_state, 1, 0, blood=0, stealth=5)  # Hunt with high stealth
        make_ready(basic_state, 2, 0, blood=3, intercept=0)  # Can't block
        # Draw cards manually
        for pid in range(1, 3):
            p = basic_state.players[pid - 1]
            for i in range(7):
                if p.library:
                    cid = p.library.pop(0)
                    p.hand.append(cid)
        engine = GameEngine(basic_state)
        engine._is_running = True
        bots = {p.id: RandomBot() for p in basic_state.players}
        c = basic_state.card_by_id("p1_crypt_0")
        engine.phases.execute_minion(bots)
        assert c.blood > 0  # Hunt succeeded

    def test_directed_action_only_target_blocks(self, basic_state):
        """Only target can block directed actions."""
        # P2 (prey of P1) bleeds P1 - only P1 can block
        make_ready(basic_state, 2, 0, blood=3, stealth=0)
        # Give P1 a blocker with low intercept
        make_ready(basic_state, 1, 0, blood=3, intercept=0)
        engine = GameEngine(basic_state)
        engine.start()
        bots = {p.id: RandomBot() for p in basic_state.players}
        p1_initial_pool = basic_state.players[0].pool
        engine.phases.execute_minion(bots)
        # P1's blocker has intercept 0, P2's bleed has stealth 0
        # block succeeds (0 >= 0), so P1 pool unchanged
        assert basic_state.players[0].pool == p1_initial_pool


# ── Influence Phase Tests ───────────────────────────────────────────────────


class TestInfluencePhase:
    def test_adds_blood(self, basic_state):
        c = basic_state.card_by_id("p1_crypt_0")
        c.position = CardPosition.uncontrolled
        c.blood = 0
        c.locked = True
        engine = GameEngine(basic_state)
        engine.start()
        engine.state.turn_number = 3
        engine.phases.execute_influence(basic_state.players[0], engine.state, {})
        assert c.blood > 0

    def test_moves_to_ready_when_full(self, basic_state):
        c = basic_state.card_by_id("p1_crypt_0")
        c.position = CardPosition.uncontrolled
        c.blood = 0
        c.locked = True
        c.capacity = 4
        engine = GameEngine(basic_state)
        engine.start()
        engine.state.turn_number = 3
        engine.phases.execute_influence(basic_state.players[0], engine.state, {})
        assert c.position == CardPosition.ready

    def test_costs_pool(self, basic_state):
        c = basic_state.card_by_id("p1_crypt_0")
        c.position = CardPosition.uncontrolled
        c.blood = 0
        c.locked = True
        engine = GameEngine(basic_state)
        engine.start()
        engine.state.turn_number = 3
        p1 = basic_state.players[0]
        initial = p1.pool
        engine.phases.execute_influence(p1, engine.state, {})
        assert p1.pool < initial


# ── Edge Tests ──────────────────────────────────────────────────────────────


class TestEdge:
    def test_starts_uncontrolled(self):
        state = GameState(game_id="edge")
        assert state.edge_uncontrolled is True

    def test_lost_on_oust(self, basic_state):
        p1 = basic_state.players[0]
        p1.has_edge = True
        basic_state.edge_uncontrolled = False
        basic_state.oust_player(p1.id)
        assert p1.has_edge is False
        assert basic_state.edge_uncontrolled is True


# ── Predator/Prey Tests ─────────────────────────────────────────────────────


class TestPredatorPrey:
    def test_two_player_prey(self, basic_state):
        assert basic_state.prey_of(1).id == 2
        assert basic_state.prey_of(2).id == 1

    def test_two_player_predator(self, basic_state):
        assert basic_state.predator_of(1).id == 2
        assert basic_state.predator_of(2).id == 1

    def test_three_player_prey(self):
        state = GameState(game_id="3p")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        assert state.prey_of(1).id == 3
        assert state.prey_of(2).id == 1
        assert state.prey_of(3).id == 2

    def test_three_player_predator(self):
        state = GameState(game_id="3p")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        assert state.predator_of(1).id == 2
        assert state.predator_of(2).id == 3
        assert state.predator_of(3).id == 1

    def test_prey_updates_after_oust(self):
        state = GameState(game_id="3p")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        state.oust_player(3)
        assert state.prey_of(1).id == 2

    def test_single_player_no_prey(self):
        state = GameState(game_id="1p")
        p = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p)
        assert state.prey_of(1) is None


# ── Turn Flow Tests ─────────────────────────────────────────────────────────


class TestTurnFlow:
    def test_turn_increments(self, engine):
        initial = engine.state.turn_number
        engine.run_turn()
        assert engine.state.turn_number == initial + 1

    def test_turn_advances_player(self, engine):
        initial = engine.state.current_player_id
        engine.run_turn()
        assert engine.state.current_player_id != initial


# ── Card Instance Tests ─────────────────────────────────────────────────────


class TestCardInstance:
    def test_is_ready(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, locked=False)
        assert c.is_ready is True

    def test_not_ready_when_locked(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, locked=True)
        assert c.is_ready is False

    def test_not_ready_in_crypt(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.crypt)
        assert c.is_ready is False

    def test_add_blood(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, blood=0, capacity=5)
        assert c.add_blood(3) == 3
        assert c.blood == 3

    def test_add_blood_capped(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, blood=3, capacity=5)
        assert c.add_blood(5) == 2
        assert c.blood == 5

    def test_take_damage(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, blood=3, capacity=5)
        c.take_damage(2)
        assert c.blood == 1
        assert c.damage_taken == 0

    def test_take_damage_torpor(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, blood=1, capacity=5)
        c.take_damage(3)
        assert c.position == CardPosition.torpor
        assert c.locked is True

    def test_lock_unlock(self):
        c = CardInstance(id="t", card_id=1, name="T")
        c.lock()
        assert c.locked is True
        c.unlock()
        assert c.locked is False

    def test_is_alive(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready)
        assert c.is_alive is True
        c.position = CardPosition.ash_heap
        assert c.is_alive is False
        c.position = CardPosition.removed
        assert c.is_alive is False

    def test_is_wounded(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready)
        assert c.is_wounded is False
        c.damage_taken = 1
        assert c.is_wounded is True
        c.position = CardPosition.torpor
        assert c.is_wounded is True

    def test_mend_damage(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, damage_taken=3)
        mended = c.mend_damage(2)
        assert mended == 2
        assert c.damage_taken == 1

    def test_take_damage_aggravated(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, blood=3, capacity=5)
        c.take_damage(2, aggravated=True)
        # Aggravated damage doesn't burn blood, goes straight to damage_taken
        assert c.blood == 3
        assert c.damage_taken == 2
        assert c.position == CardPosition.torpor

    def test_take_damage_kills_empty_vampire(self):
        c = CardInstance(id="t", card_id=1, name="T", position=CardPosition.ready, blood=0, capacity=5)
        c.take_damage(1)
        # No blood to mend, goes to torpor
        assert c.position == CardPosition.torpor

    def test_strength_default(self):
        c = CardInstance(id="t", card_id=1, name="T")
        assert c.strength == 1

    def test_hunt_default(self):
        c = CardInstance(id="t", card_id=1, name="T")
        assert c.hunt == 1

    def test_stealth_intercept_default(self):
        c = CardInstance(id="t", card_id=1, name="T")
        assert c.stealth == 0
        assert c.intercept == 0
        assert c.bleed == 0

    def test_actions_tracking(self):
        c = CardInstance(id="t", card_id=1, name="T")
        assert c.has_acted_this_turn is False
        assert c.actions_this_turn == 0
        c.has_acted_this_turn = True
        c.actions_this_turn = 1
        assert c.has_acted_this_turn is True
        assert c.actions_this_turn == 1


# ── Combat Tests ────────────────────────────────────────────────────────────


class TestCombat:
    def _make_combat_state(self, p1_blood=4, p1_str=2, p2_blood=3, p2_str=1, p2_intercept=5):
        """Helper to create a 2-player state with combat-ready minions."""
        state = GameState(game_id="combat")
        state.edge_uncontrolled = True
        for pid in range(1, 3):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)

        attacker = CardInstance(
            id="p1_atk", card_id=1, name="Attacker",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=p1_blood, locked=False, strength=p1_str,
        )
        state.cards[attacker.id] = attacker

        defender = CardInstance(
            id="p2_def", card_id=2, name="Defender",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=p2_blood, locked=False, strength=p2_str,
            intercept=p2_intercept,
        )
        state.cards[defender.id] = defender

        return state, attacker, defender

    def test_combat_deals_damage(self):
        """Combat should deal damage based on strength."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=4, p1_str=2, p2_blood=3, p2_str=1
        )
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._start_combat(attacker, defender)
        assert defender.blood == 1  # 3 - 2
        assert attacker.blood == 3  # 4 - 1

    def test_combat_both_survive(self):
        """Both combatants should survive if damage doesn't exceed blood."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=5, p1_str=1, p2_blood=5, p2_str=1
        )
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._start_combat(attacker, defender)
        assert attacker.position == CardPosition.ready
        assert defender.position == CardPosition.ready

    def test_combat_sends_to_torpor(self):
        """Vampire should go to torpor when damage exceeds blood."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=5, p1_str=5, p2_blood=2, p2_str=1
        )
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._start_combat(attacker, defender)
        assert defender.position == CardPosition.torpor

    def test_combat_runs_without_error(self):
        """Combat should run without errors."""
        state, attacker, defender = self._make_combat_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._start_combat(attacker, defender)
        # Combat should complete and log damage
        log_texts = [e["data"].get("text", "") for e in engine.log]
        assert any("damage" in t.lower() for t in log_texts)

    def test_combat_through_block(self):
        """Combat should trigger when action is blocked."""
        state = GameState(game_id="block_combat")
        state.edge_uncontrolled = True

        for pid in range(1, 3):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            for i in range(6):
                c = CardInstance(
                    id=f"p{pid}_crypt_{i}", card_id=i, name=f"Vamp{pid}_{i}",
                    position=CardPosition.crypt, tipo="Vampire", capacity=5, blood=0,
                )
                state.cards[c.id] = c
                p.crypt.append(c.id)
            blocker = CardInstance(
                id=f"p{pid}_blocker", card_id=99, name=f"Blocker{pid}",
                position=CardPosition.ready, tipo="Vampire", capacity=5, blood=3,
                locked=False, intercept=5, strength=1,
            )
            state.cards[blocker.id] = blocker
            p.crypt.append(blocker.id)
            state.players.append(p)

        attacker = state.card_by_id("p1_crypt_0")
        attacker.position = CardPosition.ready
        attacker.blood = 4
        attacker.locked = False
        attacker.strength = 2

        engine = GameEngine(state)
        for pid in range(1, 3):
            p = state.players[pid - 1]
            for i in range(7):
                if p.library:
                    cid = p.library.pop(0)
                    p.hand.append(cid)

        bots = {p.id: RandomBot() for p in state.players}
        engine.phases.execute_minion(bots)

        # Combat should have occurred (blocker blocked, combat triggered)
        log_texts = [e["data"].get("text", "") for e in engine.log]
        assert any("blocked" in t.lower() for t in log_texts)
        assert any("damage" in t.lower() for t in log_texts)

    def test_combat_damage_log(self):
        """Combat should log damage dealt."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=4, p1_str=3, p2_blood=3, p2_str=2
        )
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._start_combat(attacker, defender)
        log_texts = [e["data"].get("text", "") for e in engine.log]
        assert any("damage" in t.lower() for t in log_texts)

    def test_combat_close_range_default(self):
        """Combat should default to close range."""
        state, attacker, defender = self._make_combat_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._start_combat(attacker, defender)
        assert attacker.blood < 4
        assert defender.blood < 3

    def test_combat_strength_matters(self):
        """Higher strength should deal more damage."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=10, p1_str=5, p2_blood=10, p2_str=1
        )
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._start_combat(attacker, defender)
        assert (10 - defender.blood) > (10 - attacker.blood)

    def test_first_strike_kills_before_counter(self):
        """First strike should resolve before normal strike."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=10, p1_str=5, p2_blood=3, p2_str=5
        )
        engine = GameEngine(state)
        engine._is_running = True
        # Simulate attacker using first strike
        atk_strike = {
            'type': 'hand_strike', 'damage': 5, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': True, 'ranged': False,
        }
        def_strike = {
            'type': 'hand_strike', 'damage': 5, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': False, 'ranged': False,
        }
        engine.phases._resolve_strikes(attacker, defender, atk_strike, def_strike, 'close')
        # Defender should be in torpor (took 5 damage, only had 3 blood)
        # and shouldn't have struck back
        assert defender.position == CardPosition.torpor
        assert attacker.blood == 10  # No damage from defender (killed before counter)

    def test_dodge_protects_from_first_strike(self):
        """Dodge should protect from first strike."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=10, p1_str=5, p2_blood=10, p2_str=1
        )
        engine = GameEngine(state)
        engine._is_running = True
        # Attacker uses first strike, defender dodges
        atk_strike = {
            'type': 'hand_strike', 'damage': 5, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': True, 'ranged': False,
        }
        def_strike = {
            'type': 'hand_strike', 'damage': 0, 'aggravated': False,
            'steal_amount': 0, 'dodge': True, 'combat_ends': False,
            'first_strike': False, 'ranged': False,
        }
        engine.phases._resolve_strikes(attacker, defender, atk_strike, def_strike, 'close')
        # Defender should be unharmed (dodged)
        assert defender.blood == 10

    def test_combat_ends_resolves_first(self):
        """Combat ends should resolve before first strike."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=10, p1_str=5, p2_blood=10, p2_str=5
        )
        engine = GameEngine(state)
        engine._is_running = True
        # Attacker plays combat ends, defender plays first strike
        atk_strike = {
            'type': 'hand_strike', 'damage': 0, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': True,
            'first_strike': False, 'ranged': False,
        }
        def_strike = {
            'type': 'hand_strike', 'damage': 5, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': True, 'ranged': False,
        }
        result = engine.phases._resolve_strikes(attacker, defender, atk_strike, def_strike, 'close')
        assert result is True  # Combat ended
        assert defender.blood == 10  # No damage
        assert attacker.blood == 10  # No damage

    def test_both_first_strike_simultaneous(self):
        """When both use first strike, resolve simultaneously."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=10, p1_str=3, p2_blood=10, p2_str=3
        )
        engine = GameEngine(state)
        engine._is_running = True
        atk_strike = {
            'type': 'hand_strike', 'damage': 3, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': True, 'ranged': False,
        }
        def_strike = {
            'type': 'hand_strike', 'damage': 3, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': True, 'ranged': False,
        }
        engine.phases._resolve_strikes(attacker, defender, atk_strike, def_strike, 'close')
        # Both should take damage (simultaneous resolution)
        assert attacker.blood == 7  # 10 - 3
        assert defender.blood == 7  # 10 - 3

    def test_ranged_strike_works_at_long_range(self):
        """Ranged strikes should work at any range."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=10, p1_str=3, p2_blood=10, p2_str=3
        )
        engine = GameEngine(state)
        engine._is_running = True
        atk_strike = {
            'type': 'hand_strike', 'damage': 3, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': False, 'ranged': True,
        }
        def_strike = {
            'type': 'hand_strike', 'damage': 3, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': False, 'ranged': False,
        }
        # At long range, only ranged strikes work
        engine.phases._resolve_strikes(attacker, defender, atk_strike, def_strike, 'long')
        # Defender took damage (attacker's ranged strike worked)
        assert defender.blood == 7
        # Attacker didn't take damage (defender's non-ranged strike doesn't work at long)
        assert attacker.blood == 10

    def test_aggravated_damage(self):
        """Aggravated damage cannot be mended with blood."""
        state, attacker, defender = self._make_combat_state(
            p1_blood=10, p1_str=3, p2_blood=10, p2_str=1
        )
        engine = GameEngine(state)
        engine._is_running = True
        atk_strike = {
            'type': 'hand_strike', 'damage': 2, 'aggravated': True,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': False, 'ranged': False,
        }
        def_strike = {
            'type': 'hand_strike', 'damage': 1, 'aggravated': False,
            'steal_amount': 0, 'dodge': False, 'combat_ends': False,
            'first_strike': False, 'ranged': False,
        }
        engine.phases._resolve_strikes(attacker, defender, atk_strike, def_strike, 'close')
        # Defender: 2 aggravated damage -> cannot mend -> goes to torpor
        assert defender.position == CardPosition.torpor
        assert defender.blood == 10  # Blood not burned for aggravated


# ── Leave Torpor / Rescue / Diablerie Tests ─────────────────────────────────


class TestLeaveTorpor:
    def _make_torpor_state(self, blood=3, damage_taken=2):
        state = GameState(game_id="torpor")
        p1 = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p1)
        c = CardInstance(
            id="p1_vamp", card_id=1, name="Vampire",
            position=CardPosition.torpor, tipo="Vampire",
            capacity=5, blood=blood, damage_taken=damage_taken,
        )
        state.cards[c.id] = c
        return state, c, p1

    def test_leave_torpor_success(self):
        """Vampire with 2+ blood should leave torpor."""
        state, vampire, player = self._make_torpor_state(blood=3)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_leave_torpor(vampire, player)
        assert vampire.position == CardPosition.ready
        assert vampire.blood == 1  # 3 - 2
        assert vampire.damage_taken == 0

    def test_leave_torpor_insufficient_blood(self):
        """Vampire with < 2 blood cannot leave torpor."""
        state, vampire, player = self._make_torpor_state(blood=1)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_leave_torpor(vampire, player)
        assert vampire.position == CardPosition.torpor
        assert vampire.blood == 1

    def test_leave_torpor_exact_blood(self):
        """Vampire with exactly 2 blood can leave torpor."""
        state, vampire, player = self._make_torpor_state(blood=2)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_leave_torpor(vampire, player)
        assert vampire.position == CardPosition.ready
        assert vampire.blood == 0


class TestRescue:
    def _make_rescue_state(self, rescuer_blood=4, victim_blood=0, victim_dmg=3):
        state = GameState(game_id="rescue")
        p1 = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p1)
        rescuer = CardInstance(
            id="p1_rescuer", card_id=1, name="Rescuer",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=rescuer_blood,
        )
        state.cards[rescuer.id] = rescuer
        victim = CardInstance(
            id="p1_victim", card_id=2, name="Victim",
            position=CardPosition.torpor, tipo="Vampire",
            capacity=5, blood=victim_blood, damage_taken=victim_dmg,
        )
        state.cards[victim.id] = victim
        return state, rescuer, victim, p1

    def test_rescue_success(self):
        """Rescuer with 2+ blood should rescue vampire from torpor."""
        state, rescuer, victim, player = self._make_rescue_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_rescue(rescuer, player, victim)
        assert victim.position == CardPosition.ready
        assert victim.damage_taken == 0
        assert rescuer.blood == 2  # 4 - 2

    def test_rescue_insufficient_blood(self):
        """Rescuer with < 2 blood cannot rescue."""
        state, rescuer, victim, player = self._make_rescue_state(rescuer_blood=1)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_rescue(rescuer, player, victim)
        assert victim.position == CardPosition.torpor

    def test_rescue_no_target(self):
        """Rescue with no target should fail gracefully."""
        state, rescuer, _, player = self._make_rescue_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_rescue(rescuer, player, None)
        assert rescuer.blood == 4  # Unchanged

    def test_rescued_victim_not_locked(self):
        """Rescued vampire should not be locked."""
        state, rescuer, victim, player = self._make_rescue_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_rescue(rescuer, player, victim)
        assert victim.locked is False


class TestDiablerie:
    def _make_diablerie_state(self, diablerist_cap=5, victim_cap=7, victim_blood=4):
        state = GameState(game_id="diablerie")
        p1 = PlayerState(id=1, username="P1", pool=30)
        p2 = PlayerState(id=2, username="P2", pool=30)
        state.players.extend([p1, p2])
        diablerist = CardInstance(
            id="p1_diabolist", card_id=1, name="Diablerist",
            position=CardPosition.ready, tipo="Vampire",
            capacity=diablerist_cap, blood=2,
        )
        state.cards[diablerist.id] = diablerist
        victim = CardInstance(
            id="p2_victim", card_id=2, name="Victim",
            position=CardPosition.torpor, tipo="Vampire",
            capacity=victim_cap, blood=victim_blood, damage_taken=2,
        )
        state.cards[victim.id] = victim
        return state, diablerist, victim, p1

    def test_diablerie_burns_victim(self):
        """Diablerie should burn the victim."""
        state, diablerist, victim, player = self._make_diablerie_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_diablerie(diablerist, player, victim)
        assert victim.position == CardPosition.ash_heap

    def test_diablerie_steals_blood(self):
        """Diablerist should gain victim's blood."""
        state, diablerist, victim, player = self._make_diablerie_state()
        engine = GameEngine(state)
        engine._is_running = True
        initial_blood = diablerist.blood
        engine.phases._resolve_diablerie(diablerist, player, victim)
        assert diablerist.blood > initial_blood

    def test_diablerie_gains_capacity_if_victim_older(self):
        """Diablerist should gain +1 capacity if victim was older."""
        state, diablerist, victim, player = self._make_diablerie_state(
            diablerist_cap=5, victim_cap=7
        )
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_diablerie(diablerist, player, victim)
        assert diablerist.capacity == 6  # 5 + 1

    def test_diablerie_no_capacity_gain_if_victim_younger(self):
        """Diablerist should not gain capacity if victim was younger."""
        state, diablerist, victim, player = self._make_diablerie_state(
            diablerist_cap=7, victim_cap=5
        )
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_diablerie(diablerist, player, victim)
        assert diablerist.capacity == 7  # Unchanged

    def test_diablerie_no_target(self):
        """Diablerie with no target should fail gracefully."""
        state, diablerist, _, player = self._make_diablerie_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_diablerie(diablerist, player, None)
        assert diablerist.blood == 2  # Unchanged


# ── Ousting and Victory Tests ───────────────────────────────────────────────


class TestOusting:
    def _make_3p_state(self):
        """Create a 3-player state."""
        state = GameState(game_id="oust")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            for i in range(6):
                c = CardInstance(
                    id=f"p{pid}_crypt_{i}", card_id=i, name=f"Vamp{pid}_{i}",
                    position=CardPosition.crypt, tipo="Vampire", capacity=5, blood=0,
                )
                state.cards[c.id] = c
                p.crypt.append(c.id)
            state.players.append(p)
        return state

    def test_oust_removes_cards(self):
        """Ousting should remove all controlled cards from play."""
        state = self._make_3p_state()
        removed = state.oust_player(3)
        # All P3 cards should be removed
        for c in state.cards.values():
            if c.id.startswith("p3_"):
                assert c.position == CardPosition.removed
        assert len(removed) == 6  # 6 crypt cards

    def test_oust_clears_player_state(self):
        """Ousting should clear player's hand, library, crypt, pool."""
        state = self._make_3p_state()
        p3 = state.players[2]
        # Add some cards to hand
        p3.hand = ["card1", "card2"]
        state.oust_player(3)
        assert p3.is_ousted is True
        assert p3.pool == 0
        assert len(p3.hand) == 0
        assert len(p3.library) == 0
        assert len(p3.crypt) == 0
        assert len(p3.ash_heap) == 0

    def test_oust_awards_vp_and_pool_to_predator(self):
        """Predator should gain 6 pool and 1 VP when prey is ousted."""
        state = self._make_3p_state()
        # In 3-player: P1's predator is P2, P2's predator is P3, P3's predator is P1
        # Oust P3 -> P1 is predator
        state.oust_player(3)
        p1 = state.players[0]
        assert p1.victory_points == 1
        assert p1.pool == 36  # 30 + 6

    def test_oust_edge_returns_to_uncontrolled(self):
        """Edge should return to uncontrolled if ousted player had it."""
        state = self._make_3p_state()
        p3 = state.players[2]
        p3.has_edge = True
        state.edge_uncontrolled = False
        state.oust_player(3)
        assert p3.has_edge is False
        assert state.edge_uncontrolled is True

    def test_oust_already_ousted_player(self):
        """Ousting an already ousted player should do nothing."""
        state = self._make_3p_state()
        state.oust_player(3)
        p1 = state.players[0]
        initial_vp = p1.victory_points
        initial_pool = p1.pool
        # Try to oust again
        removed = state.oust_player(3)
        assert len(removed) == 0
        assert p1.victory_points == initial_vp
        assert p1.pool == initial_pool

    def test_oust_updates_prey(self):
        """Prey relationships should update after ousting."""
        state = self._make_3p_state()
        # Before: P1's prey is P3
        assert state.prey_of(1).id == 3
        state.oust_player(3)
        # After: P1's prey should be P2
        assert state.prey_of(1).id == 2

    def test_oust_updates_predator(self):
        """Predator relationships should update after ousting."""
        state = self._make_3p_state()
        # Before: P1's predator is P2
        assert state.predator_of(1).id == 2
        state.oust_player(3)
        # After: P1's predator should still be P2
        assert state.predator_of(1).id == 2


class TestVictory:
    def test_winner_last_survivor(self):
        """Last surviving player should win."""
        state = GameState(game_id="victory")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        state.oust_player(2)
        state.oust_player(3)
        winner = state.check_winner()
        assert winner is not None
        assert winner.id == 1
        # Award last survivor bonus
        state.award_last_survivor_bonus()
        # P1 got VP from ousting P2 (predator) and P3 (predator), plus last survivor
        assert winner.victory_points >= 1

    def test_winner_with_oust_vp(self):
        """Winner should have VP from ousting + last survivor."""
        state = GameState(game_id="victory2")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        state.oust_player(3)
        state.oust_player(2)
        winner = state.check_winner()
        assert winner is not None
        assert winner.id == 1
        # Award last survivor bonus
        state.award_last_survivor_bonus()
        assert winner.victory_points == 3  # 2 from ousting + 1 last survivor

    def test_no_winner_multiple_players(self):
        """No winner when multiple players remain."""
        state = GameState(game_id="no_win")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        state.oust_player(3)
        winner = state.check_winner()
        assert winner is None

    def test_game_is_finished(self):
        """Game should be finished when only 1 player remains."""
        state = GameState(game_id="finished")
        state.edge_uncontrolled = True
        for pid in range(1, 3):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        state.oust_player(2)
        assert state.is_finished is True

    def test_game_not_finished(self):
        """Game should not be finished with multiple players."""
        state = GameState(game_id="not_finished")
        state.edge_uncontrolled = True
        for pid in range(1, 3):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        assert state.is_finished is False

    def test_final_scores(self):
        """Final scores should be sorted by VP descending."""
        state = GameState(game_id="scores")
        state.edge_uncontrolled = True
        for pid in range(1, 4):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        state.oust_player(3)
        state.oust_player(2)
        # Award last survivor bonus
        state.award_last_survivor_bonus()
        scores = state.get_final_scores()
        assert scores[0]["username"] == "P1"
        assert scores[0]["victory_points"] == 3
        assert scores[1]["victory_points"] == 0
        assert scores[2]["victory_points"] == 0

    def test_two_player_oust(self):
        """In 2-player game, ousting one player ends the game."""
        state = GameState(game_id="2p_oust")
        state.edge_uncontrolled = True
        for pid in range(1, 3):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        state.oust_player(2)
        winner = state.check_winner()
        assert winner is not None
        assert winner.id == 1
        # Award last survivor bonus
        state.award_last_survivor_bonus()
        assert winner.victory_points == 2  # 1 from ousting + 1 last survivor

    def test_oust_pool_zero(self):
        """Player with 0 pool should be ousted."""
        state = GameState(game_id="pool_zero")
        state.edge_uncontrolled = True
        for pid in range(1, 3):
            p = PlayerState(id=pid, username=f"P{pid}", pool=30)
            state.players.append(p)
        p2 = state.players[1]
        p2.pool = 0
        state.oust_player(2)
        assert p2.is_ousted is True


# ── Action Modifiers and Reactions Tests ────────────────────────────────────


class TestActionModifiers:
    def _make_modifier_state(self, mod_stealth=1, mod_bleed=1, mod_cost=1, minion_blood=4):
        state = GameState(game_id="mod")
        p1 = PlayerState(id=1, username="P1", pool=30)
        p2 = PlayerState(id=2, username="P2", pool=30)
        state.players.extend([p1, p2])
        minion = CardInstance(
            id="p1_vamp", card_id=1, name="Vampire",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=minion_blood,
        )
        state.cards[minion.id] = minion
        mod = CardInstance(
            id="p1_mod", card_id=100, name="Bonding",
            position=CardPosition.hand, tipo="Action Modifier",
            pool_cost=mod_cost, stealth=mod_stealth, bleed=mod_bleed,
        )
        state.cards[mod.id] = mod
        p1.hand.append(mod.id)
        return state, minion, mod, p1, p2

    def test_modifier_increases_stealth(self):
        """Action modifier should increase action stealth."""
        state, minion, mod, p1, p2 = self._make_modifier_state(mod_stealth=2)
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        modifiers = engine.phases._play_action_modifiers(minion, p1, action_info, RandomBot())
        engine.phases._apply_modifier_effects(action_info, modifiers)
        assert action_info['stealth'] == 2

    def test_modifier_increases_bleed(self):
        """Action modifier should increase bleed amount."""
        state, minion, mod, p1, p2 = self._make_modifier_state(mod_bleed=2)
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        modifiers = engine.phases._play_action_modifiers(minion, p1, action_info, RandomBot())
        engine.phases._apply_modifier_effects(action_info, modifiers)
        assert action_info.get('bleed_bonus', 0) == 2

    def test_modifier_costs_blood(self):
        """Playing action modifier should cost blood."""
        state, minion, mod, p1, p2 = self._make_modifier_state(mod_cost=2)
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        modifiers = engine.phases._play_action_modifiers(minion, p1, action_info, RandomBot())
        assert minion.blood == 2  # 4 - 2
        assert len(modifiers) == 1

    def test_modifier_insufficient_blood(self):
        """Cannot play modifier without enough blood."""
        state, minion, mod, p1, p2 = self._make_modifier_state(mod_cost=3, minion_blood=2)
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        modifiers = engine.phases._play_action_modifiers(minion, p1, action_info, RandomBot())
        assert len(modifiers) == 0
        assert minion.blood == 2  # Unchanged

    def test_modifier_removes_from_hand(self):
        """Playing modifier should remove card from hand."""
        state, minion, mod, p1, p2 = self._make_modifier_state()
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        modifiers = engine.phases._play_action_modifiers(minion, p1, action_info, RandomBot())
        assert mod.id not in p1.hand
        assert mod.position == CardPosition.ash_heap

    def test_no_modifier_in_hand(self):
        """No modifiers played if none in hand."""
        state = GameState(game_id="no_mod")
        p1 = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p1)
        minion = CardInstance(
            id="p1_vamp", card_id=1, name="Vampire",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=4,
        )
        state.cards[minion.id] = minion
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        modifiers = engine.phases._play_action_modifiers(minion, p1, action_info, RandomBot())
        assert len(modifiers) == 0


class TestReactions:
    def _make_reaction_state(self, react_intercept=2, react_cost=1, blocker_blood=3):
        state = GameState(game_id="react")
        p1 = PlayerState(id=1, username="P1", pool=30)
        p2 = PlayerState(id=2, username="P2", pool=30)
        state.players.extend([p1, p2])
        # Attacker minion
        attacker = CardInstance(
            id="p1_vamp", card_id=1, name="Attacker",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=4,
        )
        state.cards[attacker.id] = attacker
        # Blocker with reaction card
        blocker = CardInstance(
            id="p2_vamp", card_id=2, name="Blocker",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=blocker_blood, intercept=0,
        )
        state.cards[blocker.id] = blocker
        # Reaction card in blocker's hand
        react = CardInstance(
            id="p2_react", card_id=100, name="Telepathic Misdirection",
            position=CardPosition.hand, tipo="Reaction",
            pool_cost=react_cost, intercept=react_intercept,
        )
        state.cards[react.id] = react
        p2.hand.append(react.id)
        return state, attacker, blocker, react, p1, p2

    def test_reaction_increases_intercept(self):
        """Reaction should increase blocker's intercept."""
        state, attacker, blocker, react, p1, p2 = self._make_reaction_state()
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        reactions = engine.phases._play_reactions(attacker, p1, action_info, RandomBot())
        assert action_info.get('reaction_intercept', 0) == 2

    def test_reaction_costs_blood(self):
        """Playing reaction should cost blood."""
        state, attacker, blocker, react, p1, p2 = self._make_reaction_state()
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        engine.phases._play_reactions(attacker, p1, action_info, RandomBot())
        assert blocker.blood == 2  # 3 - 1

    def test_reaction_removes_from_hand(self):
        """Playing reaction should remove card from hand."""
        state, attacker, blocker, react, p1, p2 = self._make_reaction_state()
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        engine.phases._play_reactions(attacker, p1, action_info, RandomBot())
        assert react.id not in p2.hand
        assert react.position == CardPosition.ash_heap

    def test_reaction_helps_block(self):
        """Reaction with intercept bonus should help block."""
        state, attacker, blocker, react, p1, p2 = self._make_reaction_state(
            react_intercept=3, blocker_blood=3
        )
        engine = GameEngine(state)
        engine._is_running = True
        # Attacker has stealth 0, blocker has intercept 0
        # Without reaction: block succeeds (0 >= 0)
        # With reaction: block still succeeds (0 + 3 >= 0)
        action_info = {'stealth': 0, 'directed': True}
        reactions = engine.phases._play_reactions(attacker, p1, action_info, RandomBot())
        # Reaction adds intercept bonus
        assert action_info.get('reaction_intercept', 0) == 3

    def test_no_reaction_without_target(self):
        """No reactions if no valid target."""
        state = GameState(game_id="no_react")
        p1 = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p1)
        attacker = CardInstance(
            id="p1_vamp", card_id=1, name="Attacker",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=4,
        )
        state.cards[attacker.id] = attacker
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': False}
        reactions = engine.phases._play_reactions(attacker, p1, action_info, RandomBot())
        assert len(reactions) == 0

    def test_reaction_insufficient_blood(self):
        """Cannot play reaction without enough blood."""
        state, attacker, blocker, react, p1, p2 = self._make_reaction_state(
            react_cost=5, blocker_blood=2
        )
        engine = GameEngine(state)
        engine._is_running = True
        action_info = {'stealth': 0, 'directed': True}
        reactions = engine.phases._play_reactions(attacker, p1, action_info, RandomBot())
        assert len(reactions) == 0
        assert blocker.blood == 2  # Unchanged


# ── Equip / Retainer / Ally Tests ───────────────────────────────────────────


class TestEquip:
    def _make_equip_state(self, minion_blood=4, equip_cost=1):
        state = GameState(game_id="equip")
        p1 = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p1)
        minion = CardInstance(
            id="p1_vamp", card_id=1, name="Vampire",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=minion_blood,
        )
        state.cards[minion.id] = minion
        equip = CardInstance(
            id="p1_eq", card_id=100, name="Sword",
            position=CardPosition.hand, tipo="Equipment",
            pool_cost=equip_cost,
        )
        state.cards[equip.id] = equip
        p1.hand.append(equip.id)
        return state, minion, equip, p1

    def test_equip_success(self):
        """Equip should attach equipment to minion."""
        state, minion, equip, player = self._make_equip_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_equip(minion, player, equip)
        assert equip.position == CardPosition.attached
        assert equip.attached_to == minion.id
        assert minion.blood == 3  # 4 - 1
        assert equip.id in minion.attachments

    def test_equip_removes_from_hand(self):
        """Equip should remove card from hand."""
        state, minion, equip, player = self._make_equip_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_equip(minion, player, equip)
        assert equip.id not in player.hand

    def test_equip_insufficient_blood(self):
        """Equip should fail if minion doesn't have enough blood."""
        state, minion, equip, player = self._make_equip_state(minion_blood=0, equip_cost=1)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_equip(minion, player, equip)
        assert equip.position == CardPosition.hand  # Not equipped
        assert equip.id in player.hand

    def test_equip_no_cost(self):
        """Equip with 0 cost should work without blood."""
        state, minion, equip, player = self._make_equip_state(minion_blood=1, equip_cost=0)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_equip(minion, player, equip)
        assert equip.position == CardPosition.attached
        assert minion.blood == 1  # Unchanged

    def test_multiple_equipment(self):
        """Minion can have multiple equipment."""
        state, minion, equip1, player = self._make_equip_state()
        equip2 = CardInstance(
            id="p1_eq2", card_id=101, name="Shield",
            position=CardPosition.hand, tipo="Equipment",
            pool_cost=1,
        )
        state.cards[equip2.id] = equip2
        player.hand.append(equip2.id)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_equip(minion, player, equip1)
        engine.phases._resolve_equip(minion, player, equip2)
        assert len(minion.attachments) == 2
        assert equip1.position == CardPosition.attached
        assert equip2.position == CardPosition.attached


class TestEmployRetainer:
    def _make_retainer_state(self, minion_blood=4, retainer_cost=1, retainer_cap=2):
        state = GameState(game_id="retainer")
        p1 = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p1)
        minion = CardInstance(
            id="p1_vamp", card_id=1, name="Vampire",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=minion_blood,
        )
        state.cards[minion.id] = minion
        retainer = CardInstance(
            id="p1_ret", card_id=100, name="Guard Dog",
            position=CardPosition.hand, tipo="Retainer",
            pool_cost=retainer_cost, capacity=retainer_cap,
        )
        state.cards[retainer.id] = retainer
        p1.hand.append(retainer.id)
        return state, minion, retainer, p1

    def test_employ_retainer_success(self):
        """Employ retainer should attach to minion with life."""
        state, minion, retainer, player = self._make_retainer_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_employ_retainer(minion, player, retainer)
        assert retainer.position == CardPosition.attached
        assert retainer.attached_to == minion.id
        assert retainer.life == 2  # capacity as starting life
        assert minion.blood == 3  # 4 - 1

    def test_employ_retainer_removes_from_hand(self):
        """Employ retainer should remove card from hand."""
        state, minion, retainer, player = self._make_retainer_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_employ_retainer(minion, player, retainer)
        assert retainer.id not in player.hand

    def test_employ_retainer_insufficient_blood(self):
        """Employ retainer should fail if not enough blood."""
        state, minion, retainer, player = self._make_retainer_state(minion_blood=0)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_employ_retainer(minion, player, retainer)
        assert retainer.position == CardPosition.hand

    def test_multiple_retainers(self):
        """Minion can have multiple retainers."""
        state, minion, ret1, player = self._make_retainer_state()
        ret2 = CardInstance(
            id="p1_ret2", card_id=101, name="Wolf",
            position=CardPosition.hand, tipo="Retainer",
            pool_cost=1, capacity=3,
        )
        state.cards[ret2.id] = ret2
        player.hand.append(ret2.id)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_employ_retainer(minion, player, ret1)
        engine.phases._resolve_employ_retainer(minion, player, ret2)
        assert len(minion.attachments) == 2


class TestRecruitAlly:
    def _make_ally_state(self, minion_blood=4, ally_cost=2, ally_cap=3):
        state = GameState(game_id="ally")
        p1 = PlayerState(id=1, username="P1", pool=30)
        state.players.append(p1)
        minion = CardInstance(
            id="p1_vamp", card_id=1, name="Vampire",
            position=CardPosition.ready, tipo="Vampire",
            capacity=5, blood=minion_blood,
        )
        state.cards[minion.id] = minion
        ally_card = CardInstance(
            id="p1_al", card_id=100, name="Mage",
            position=CardPosition.hand, tipo="Ally",
            pool_cost=ally_cost, capacity=ally_cap,
        )
        state.cards[ally_card.id] = ally_card
        p1.hand.append(ally_card.id)
        return state, minion, ally_card, p1

    def test_recruit_ally_success(self):
        """Recruit ally should create ally in ready region."""
        state, minion, ally_card, player = self._make_ally_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_recruit_ally(minion, player, ally_card)
        # Ally should be in ready region
        allies = [
            c for c in state.cards.values()
            if c.tipo == 'Ally' and c.position == CardPosition.ready
        ]
        assert len(allies) == 1
        ally = allies[0]
        assert ally.life == 3  # Full life
        assert ally.locked is True  # Cannot act this turn

    def test_recruit_ally_costs_blood(self):
        """Recruit ally should cost blood."""
        state, minion, ally_card, player = self._make_ally_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_recruit_ally(minion, player, ally_card)
        assert minion.blood == 2  # 4 - 2

    def test_recruit_ally_insufficient_blood(self):
        """Recruit ally should fail if not enough blood."""
        state, minion, ally_card, player = self._make_ally_state(minion_blood=1, ally_cost=2)
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_recruit_ally(minion, player, ally_card)
        allies = [
            c for c in state.cards.values()
            if c.tipo == 'Ally' and c.position == CardPosition.ready
        ]
        assert len(allies) == 0

    def test_recruit_ally_removes_card(self):
        """Recruit ally should remove card from hand."""
        state, minion, ally_card, player = self._make_ally_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_recruit_ally(minion, player, ally_card)
        assert ally_card.id not in player.hand

    def test_ally_cannot_act_first_turn(self):
        """Ally should be locked on first turn."""
        state, minion, ally_card, player = self._make_ally_state()
        engine = GameEngine(state)
        engine._is_running = True
        engine.phases._resolve_recruit_ally(minion, player, ally_card)
        allies = [
            c for c in state.cards.values()
            if c.tipo == 'Ally' and c.position == CardPosition.ready
        ]
        assert allies[0].locked is True
        assert allies[0].has_acted_this_turn is False
