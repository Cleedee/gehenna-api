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
