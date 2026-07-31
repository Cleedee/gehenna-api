"""Strategy Engine for V:TES bots.

Loads deck-specific strategy configurations and provides
decision-making based on priorities, thresholds, and metagame adaptation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.state import GameState


@dataclass
class ThreatAssessment:
    """Assesses threat level of a player."""

    pool_threshold: int = 20
    minion_threshold: int = 3
    title_bonus: int = 2
    bleed_power_threshold: int = 3

    def assess(self, state: GameState, player_id: int) -> float:
        """Return threat score 0-10."""
        player = state.player_by_id(player_id)
        if not player or player.is_ousted:
            return 0.0

        score = 0.0

        # Pool threat
        if player.pool >= self.pool_threshold:
            score += 3.0
        elif player.pool >= 15:
            score += 1.5

        # Minion count - check player's crypt cards that are ready
        player_crypt_ids = set(player.crypt)
        ready_minions = sum(
            1
            for c in state.cards.values()
            if c.id in player_crypt_ids
            and c.position == CardPosition.ready
            and c.tipo.strip().lower() in ("vampire", "ally", "imbued")
        )
        if ready_minions >= self.minion_threshold:
            score += 2.0
        elif ready_minions >= 2:
            score += 1.0

        # Titles
        if player.has_title:
            score += self.title_bonus

        # Victory points
        score += player.victory_points * 1.5

        return min(score, 10.0)


@dataclass
class ActionPriority:
    """Priority for a specific action type."""

    action_type: str
    base_weight: float = 1.0
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeckStrategy:
    """Strategy configuration for a specific deck."""

    deck_id: int
    name: str = ""

    # Action priorities (higher = more likely)
    bleed_priority: float = 1.0
    rush_priority: float = 0.0
    vote_priority: float = 0.0
    govern_priority: float = 0.0
    shroud_priority: float = 0.0
    stealth_priority: float = 0.0
    control_priority: float = 0.0
    bloat_priority: float = 0.0

    # Thresholds
    rush_threshold: float = 5.0  # Min threat to rush
    control_threshold: float = 6.0  # Min threat to control
    bleed_threshold: float = 0.0  # Always bleed
    bloat_threshold: float = 10.0  # Pool below this = bloat

    # Card preferences
    preferred_cards: list[str] = field(default_factory=list)
    avoided_cards: list[str] = field(default_factory=list)

    # Target preferences
    target_types: list[str] = field(default_factory=lambda: ["vampire"])
    target_min_pool: int = 0
    target_prefer_low_pool: bool = False

    # Metagame adaptation
    adapt_to_counters: bool = True
    stealth_if_blocked: bool = True
    rush_if_no_block: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeckStrategy:
        """Create strategy from dictionary."""
        return cls(
            deck_id=data.get("deck_id", 0),
            name=data.get("name", ""),
            bleed_priority=data.get("bleed_priority", 1.0),
            rush_priority=data.get("rush_priority", 0.0),
            vote_priority=data.get("vote_priority", 0.0),
            govern_priority=data.get("govern_priority", 0.0),
            shroud_priority=data.get("shroud_priority", 0.0),
            stealth_priority=data.get("stealth_priority", 0.0),
            control_priority=data.get("control_priority", 0.0),
            bloat_priority=data.get("bloat_priority", 0.0),
            rush_threshold=data.get("rush_threshold", 5.0),
            control_threshold=data.get("control_threshold", 6.0),
            bleed_threshold=data.get("bleed_threshold", 0.0),
            bloat_threshold=data.get("bloat_threshold", 10.0),
            preferred_cards=data.get("preferred_cards", []),
            avoided_cards=data.get("avoided_cards", []),
            target_types=data.get("target_types", ["vampire"]),
            target_min_pool=data.get("target_min_pool", 0),
            target_prefer_low_pool=data.get("target_prefer_low_pool", False),
            adapt_to_counters=data.get("adapt_to_counters", True),
            stealth_if_blocked=data.get("stealth_if_blocked", True),
            rush_if_no_block=data.get("rush_if_no_block", True),
        )


class StrategyEngine:
    """Main strategy engine that loads configs and makes decisions."""

    def __init__(self, strategies_dir: str | None = None):
        self.strategies: dict[int, DeckStrategy] = {}
        self.threat_assessor = ThreatAssessment()

        if strategies_dir:
            self.load_strategies(strategies_dir)

    def load_strategies(self, directory: str) -> None:
        """Load all strategy files from directory."""
        path = Path(directory)
        if not path.exists():
            return

        for file in path.glob("*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                strategy = DeckStrategy.from_dict(data)
                self.strategies[strategy.deck_id] = strategy
            except Exception:
                continue

    def get_strategy(self, deck_id: int) -> DeckStrategy:
        """Get strategy for a deck, or default."""
        return self.strategies.get(deck_id, DeckStrategy(deck_id=deck_id))

    def choose_action_type(
        self,
        state: GameState,
        player_id: int,
        minion_id: str,
        deck_id: int = 0,
    ) -> str:
        """Choose action type based on strategy."""
        strategy = self.get_strategy(deck_id)
        minion = state.card_by_id(minion_id)
        player = state.player_by_id(player_id)

        if not minion or not player:
            return "bleed"

        # Check if vampire or ally
        is_vampire = minion.tipo.strip().lower() in ("vampire", "imbued")
        is_ally = minion.tipo.strip().lower() == "ally"

        # Leave torpor if needed
        if minion.position == CardPosition.torpor:
            if is_vampire and minion.blood >= 2:
                return "leave_torpor"
            return "action_card"

        # Hunt if no blood
        if is_vampire and minion.blood == 0:
            return "hunt"

        # Assess threats
        prey = state.prey_of(player_id)
        predator = state.predator_of(player_id)

        prey_threat = (
            self.threat_assessor.assess(state, prey.id) if prey else 0
        )
        predator_threat = (
            self.threat_assessor.assess(state, predator.id) if predator else 0
        )

        # Check own pool
        own_pool_low = player.pool < strategy.bloat_threshold

        # Decide action based on priorities
        return self._decide_action(
            strategy=strategy,
            minion=minion,
            player=player,
            state=state,
            prey_threat=prey_threat,
            predator_threat=predator_threat,
            own_pool_low=own_pool_low,
            is_vampire=is_vampire,
            is_ally=is_ally,
        )

    def _decide_action(
        self,
        strategy: DeckStrategy,
        minion: CardInstance,
        player: Any,
        state: GameState,
        prey_threat: float,
        predator_threat: float,
        own_pool_low: bool,
        is_vampire: bool,
        is_ally: bool,
    ) -> str:
        """Core decision logic."""

        # 1. Bloat if pool is low
        if own_pool_low and strategy.bloat_priority > 0:
            if self._has_bloat_card(state, player):
                return "action_card"

        # 2. Rush if ally with rush ability
        if is_ally and strategy.rush_priority > 0:
            if self._has_rush_ability(minion):
                # Rush high-threat targets
                if predator_threat >= strategy.rush_threshold:
                    return "rush"
                if prey_threat >= strategy.rush_threshold:
                    return "rush"
                # Random rush based on priority
                if state.random.random() < strategy.rush_priority * 0.3:
                    return "rush"

        # 3. Control if threat is high
        if strategy.control_priority > 0:
            max_threat = max(prey_threat, predator_threat)
            if max_threat >= strategy.control_threshold:
                # Use control cards (Shroud, etc.)
                if self._has_control_card(state, player):
                    return "action_card"

        # 4. Govern if available and vampire
        if is_vampire and strategy.govern_priority > 0:
            if self._has_govern_card(state, player):
                if state.random.random() < strategy.govern_priority * 0.4:
                    return "action_card"

        # 5. Vote if available and vampire with title
        if (
            is_vampire
            and strategy.vote_priority > 0
            and player.has_title
        ):
            if self._has_political_card(state, player):
                if state.random.random() < strategy.vote_priority * 0.3:
                    return "political"

        # 6. Bleed (default)
        if strategy.bleed_priority > 0:
            # Check for stealth cards
            if strategy.stealth_priority > 0:
                if self._has_stealth_card(state, player):
                    if state.random.random() < strategy.stealth_priority * 0.5:
                        return "action_card"
            return "bleed"

        # Default
        return "bleed"

    def _has_rush_ability(self, minion: CardInstance) -> bool:
        """Check if ally has rush ability."""
        if minion.tipo.strip().lower() != "ally":
            return False
        text = (getattr(minion, "text", "") or "").lower()
        rush_patterns = [
            "enter combat with a minion as a (d) action",
            "enter combat with a ready minion",
            "can enter combat with a minion",
            "may enter combat with a minion",
        ]
        return any(p in text for p in rush_patterns)

    def _has_bloat_card(self, state: GameState, player: Any) -> bool:
        """Check if player has bloat cards in hand."""
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                name = card.name.lower()
                if any(
                    n in name
                    for n in ("villein", "minion tap", "blood doll", "vessel")
                ):
                    return True
        return False

    def _has_control_card(self, state: GameState, player: Any) -> bool:
        """Check if player has control cards."""
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                name = card.name.lower()
                if any(
                    n in name
                    for n in (
                        "shroud",
                        "govern",
                        "pentex",
                        "misdirection",
                    )
                ):
                    return True
        return False

    def _has_govern_card(self, state: GameState, player: Any) -> bool:
        """Check if player has Govern the Unaligned."""
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and "govern" in card.name.lower():
                return True
        return False

    def _has_political_card(self, state: GameState, player: Any) -> bool:
        """Check if player has political action card."""
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and card.tipo.strip().lower() == "political action":
                return True
        return False

    def _has_stealth_card(self, state: GameState, player: Any) -> bool:
        """Check if player has stealth cards."""
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                name = card.name.lower()
                if any(
                    n in name
                    for n in (
                        "cloak",
                        "shadow cloak",
                        "seduction",
                        "where the veil",
                    )
                ):
                    return True
        return False

    def choose_target(
        self,
        state: GameState,
        player_id: int,
        deck_id: int = 0,
    ) -> int | None:
        """Choose which player to target."""
        strategy = self.get_strategy(deck_id)
        player = state.player_by_id(player_id)
        if not player:
            return None

        # Get valid targets
        targets = []
        for p in state.players:
            if p.id == player_id or p.is_ousted:
                continue
            threat = self.threat_assessor.assess(state, p.id)
            targets.append((p, threat))

        if not targets:
            return None

        # Sort by threat (highest first for control, lowest for bleed)
        if strategy.control_priority > strategy.bleed_priority:
            targets.sort(key=lambda x: -x[1])
        else:
            # Prefer prey, then highest threat
            prey = state.prey_of(player_id)
            if prey and not prey.is_ousted:
                return prey.id
            targets.sort(key=lambda x: -x[1])

        return targets[0][0].id


# Default strategies for common deck archetypes
DEFAULT_STRATEGIES = {
    # Bleed deck
    1: DeckStrategy(
        deck_id=1,
        name="Rush Deck",
        bleed_priority=0.5,
        rush_priority=0.8,
        control_priority=0.3,
        rush_threshold=4.0,
    ),
    # Vote deck
    2: DeckStrategy(
        deck_id=2,
        name="Vote Deck",
        bleed_priority=0.6,
        vote_priority=0.8,
        control_priority=0.2,
    ),
    # Toolbox deck (generic)
    8: DeckStrategy(
        deck_id=8,
        name="Bruise & Bleed",
        bleed_priority=0.7,
        rush_priority=0.3,
        control_priority=0.3,
    ),
    # Deck 275 - Ally Toolbox
    275: DeckStrategy(
        deck_id=275,
        name="Path of Death Ally Toolbox",
        bleed_priority=0.6,
        rush_priority=0.5,
        govern_priority=0.4,
        shroud_priority=0.5,
        control_priority=0.4,
        bloat_priority=0.3,
        rush_threshold=5.0,
        control_threshold=6.0,
        bloat_threshold=12.0,
        preferred_cards=[
            "Freakish Conglomeration",
            "Govern the Unaligned",
            "Shroud of Decay",
            "Where the Veil Thins",
        ],
        target_types=["vampire", "ally"],
    ),
}
