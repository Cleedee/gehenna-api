"""Strategy Engine for V:TES bots.

Loads deck-specific strategy configurations and provides
decision-making based on priorities, thresholds, and metagame adaptation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.state import GameState


class GamePhase(str, Enum):
    """Game phases for strategy adaptation."""
    EARLY = "early"      # Turns 1-5: Development, setup
    MID = "mid"          # Turns 6-15: Balanced play
    LATE = "late"        # Turns 16+: Aggressive, endgame
    FINAL = "final"      # Last 2 players: All-out attack


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
class PhaseAdjustments:
    """Priority adjustments for a specific game phase."""
    bleed_modifier: float = 0.0
    rush_modifier: float = 0.0
    vote_modifier: float = 0.0
    shroud_modifier: float = 0.0
    stealth_modifier: float = 0.0
    control_modifier: float = 0.0
    bloat_modifier: float = 0.0

    # Threshold adjustments
    rush_threshold_modifier: float = 0.0
    control_threshold_modifier: float = 0.0
    bloat_threshold_modifier: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhaseAdjustments:
        return cls(
            bleed_modifier=data.get("bleed_modifier", 0.0),
            rush_modifier=data.get("rush_modifier", 0.0),
            vote_modifier=data.get("vote_modifier", 0.0),

            shroud_modifier=data.get("shroud_modifier", 0.0),
            stealth_modifier=data.get("stealth_modifier", 0.0),
            control_modifier=data.get("control_modifier", 0.0),
            bloat_modifier=data.get("bloat_modifier", 0.0),
            rush_threshold_modifier=data.get("rush_threshold_modifier", 0.0),
            control_threshold_modifier=data.get("control_threshold_modifier", 0.0),
            bloat_threshold_modifier=data.get("bloat_threshold_modifier", 0.0),
        )


@dataclass
class DeckStrategy:
    """Strategy configuration for a specific deck."""

    deck_id: int
    name: str = ""

    # Base action priorities (higher = more likely)
    bleed_priority: float = 1.0
    rush_priority: float = 0.0
    vote_priority: float = 0.0
    # govern_priority removed: Govern serves two purposes:
    # 1. Blood acceleration (early game, uncontrolled vampires)
    # 2. Bleed action (mid/late game)
    # This is handled by bleed_priority + phase logic
    shroud_priority: float = 0.0
    stealth_priority: float = 0.0
    control_priority: float = 0.0
    bloat_priority: float = 0.0

    # Base thresholds
    rush_threshold: float = 5.0  # Min threat to rush
    control_threshold: float = 6.0  # Min threat to control
    bleed_threshold: float = 0.0  # Always bleed
    bloat_threshold: float = 10.0  # Pool below this = bloat

    # Phase-specific adjustments
    early_phase: PhaseAdjustments = field(default_factory=PhaseAdjustments)
    mid_phase: PhaseAdjustments = field(default_factory=PhaseAdjustments)
    late_phase: PhaseAdjustments = field(default_factory=PhaseAdjustments)
    final_phase: PhaseAdjustments = field(default_factory=PhaseAdjustments)

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

    def get_phase_adjustments(self, phase: GamePhase) -> PhaseAdjustments:
        """Get adjustments for a specific phase."""
        if phase == GamePhase.EARLY:
            return self.early_phase
        elif phase == GamePhase.MID:
            return self.mid_phase
        elif phase == GamePhase.LATE:
            return self.late_phase
        elif phase == GamePhase.FINAL:
            return self.final_phase
        return PhaseAdjustments()

    def get_adjusted_priority(
        self, base: float, modifier: float
    ) -> float:
        """Apply phase modifier to base priority, clamped 0-1."""
        return max(0.0, min(1.0, base + modifier))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeckStrategy:
        """Create strategy from dictionary."""

        def _parse_phase(data: dict | None) -> PhaseAdjustments:
            if data:
                return PhaseAdjustments.from_dict(data)
            return PhaseAdjustments()

        return cls(
            deck_id=data.get("deck_id", 0),
            name=data.get("name", ""),
            bleed_priority=data.get("bleed_priority", 1.0),
            rush_priority=data.get("rush_priority", 0.0),
            vote_priority=data.get("vote_priority", 0.0),

            shroud_priority=data.get("shroud_priority", 0.0),
            stealth_priority=data.get("stealth_priority", 0.0),
            control_priority=data.get("control_priority", 0.0),
            bloat_priority=data.get("bloat_priority", 0.0),
            rush_threshold=data.get("rush_threshold", 5.0),
            control_threshold=data.get("control_threshold", 6.0),
            bleed_threshold=data.get("bleed_threshold", 0.0),
            bloat_threshold=data.get("bloat_threshold", 10.0),
            early_phase=_parse_phase(data.get("early_phase")),
            mid_phase=_parse_phase(data.get("mid_phase")),
            late_phase=_parse_phase(data.get("late_phase")),
            final_phase=_parse_phase(data.get("final_phase")),
            preferred_cards=data.get("preferred_cards", []),
            avoided_cards=data.get("avoided_cards", []),
            target_types=data.get("target_types", ["vampire"]),
            target_min_pool=data.get("target_min_pool", 0),
            target_prefer_low_pool=data.get("target_prefer_low_pool", False),
            adapt_to_counters=data.get("adapt_to_counters", True),
            stealth_if_blocked=data.get("stealth_if_blocked", True),
            rush_if_no_block=data.get("rush_if_no_block", True),
        )


class CardKnowledge:
    """Maps cards to situations and helps decide which card to use.
    
    This class provides intelligence about:
    - Which cards are useful in which situations
    - How to prioritize cards based on game state
    - When to hold cards for later
    """
    
    # Card categories and their uses
    CARD_CATEGORIES = {
        # Defense
        'deflection': ['defense', 'redirect'],
        'delaying_tactics': ['defense', 'vote'],
        
        # Stealth
        'shadow_cloak': ['stealth', 'protection'],
        'seduction': ['stealth', 'control'],
        'where_the_veil': ['stealth', 'control'],
        
        # Bleed
        'govern': ['bleed', 'acceleration'],
        'shroud': ['bleed', 'control'],
        'deep_song': ['bleed'],
        
        # Rush
        'ambush': ['rush', 'combat'],
        'bums_rush': ['rush', 'combat'],
        'big_game': ['rush', 'combat'],
        
        # Control
        'pentex': ['control', 'lock'],
        'misdirection': ['control', 'redirect'],
        
        # Bloat
        'villein': ['bloat', 'pool'],
        'minion_tap': ['bloat', 'pool'],
        'blood_doll': ['bloat', 'pool'],
        
        # Masters
        'dreams': ['master', 'draw'],
        'visit_capuchin': ['master', 'hand_size'],
    }
    
    def __init__(self, state: GameState, player_id: int):
        self.state = state
        self.player_id = player_id
        self.player = state.player_by_id(player_id)
    
    def get_card_category(self, card: CardInstance) -> str:
        """Get the primary category of a card."""
        if not card:
            return 'unknown'
        
        name_lower = card.name.lower()
        
        # Check by name pattern
        for key, categories in self.CARD_CATEGORIES.items():
            if key.replace('_', ' ') in name_lower:
                return categories[0]
        
        # Check by type
        tipo = card.tipo.strip().lower()
        if tipo == 'action':
            return 'bleed'
        elif tipo == 'action modifier':
            return 'modifier'
        elif tipo == 'reaction':
            return 'defense'
        elif tipo == 'political action':
            return 'vote'
        elif tipo == 'master':
            return 'master'
        
        return 'unknown'
    
    def get_useful_cards_for_situation(self, situation: str) -> list[str]:
        """Get card names useful for a specific situation.
        
        Situations:
        - 'defense': incoming bleed or attack
        - 'bleed': attacking prey
        - 'rush': attacking a specific target
        - 'bloat': need pool
        - 'control': need to control board
        - 'stealth': need to avoid blockers
        """
        useful = []
        for name, categories in self.CARD_CATEGORIES.items():
            if situation in categories:
                useful.append(name)
        return useful
    
    def prioritize_cards_for_situation(
        self, situation: str
    ) -> list[tuple[CardInstance, int]]:
        """Prioritize cards in hand for a specific situation.
        
        Returns list of (card, priority) tuples sorted by priority.
        """
        if not self.player:
            return []
        
        prioritized = []
        for cid in self.player.hand:
            card = self.state.card_by_id(cid)
            if card:
                category = self.get_card_category(card)
                priority = self._calculate_priority(card, category, situation)
                prioritized.append((card, priority))
        
        # Sort by priority (highest first)
        prioritized.sort(key=lambda x: -x[1])
        return prioritized
    
    def _calculate_priority(
        self, card: CardInstance, category: str, situation: str
    ) -> int:
        """Calculate priority for a card in a given situation."""
        priority = 0
        
        # Base priority by category-situation match
        priority_map = {
            ('defense', 'defense'): 100,
            ('bleed', 'bleed'): 90,
            ('rush', 'rush'): 90,
            ('bloat', 'bloat'): 80,
            ('control', 'control'): 80,
            ('stealth', 'stealth'): 70,
            ('modifier', 'bleed'): 60,
            ('vote', 'vote'): 60,
            ('master', 'any'): 50,
        }
        
        priority = priority_map.get((category, situation), 0)
        
        # Bonus for superior cards
        if card.is_superior:
            priority += 20
        
        # Bonus for cards with bleed
        if card.bleed > 0:
            priority += card.bleed * 10
        
        # Bonus for cards with stealth
        if card.stealth > 0:
            priority += card.stealth * 10
        
        return priority
    
    def should_hold_card(self, card: CardInstance) -> bool:
        """Determine if we should hold a card for later.
        
        Hold if:
        - Card is high priority for future situations
        - Card is unique/powerful
        - We don't need it now
        """
        if not card:
            return False
        
        # Always hold deflection unless critical
        if 'deflection' in card.name.lower():
            return True
        
        # Hold high-value cards
        if card.bleed >= 2 or card.stealth >= 2:
            return True
        
        return False
    
    def get_best_card_for_action(
        self, action_type: str
    ) -> CardInstance | None:
        """Get the best card to play for a specific action type.
        
        Args:
            action_type: 'bleed', 'rush', 'vote', etc.
        """
        prioritized = self.prioritize_cards_for_situation(action_type)
        if prioritized:
            return prioritized[0][0]
        return None


class CardTiming:
    """Handles timing decisions for when to play cards.
    
    Key V:TES timing rules:
    1. Modifiers only AFTER predator confirms they're bleeding
    2. Stealth when there are dangerous blockers
    3. Deflection only against bleeds >= 2
    4. Rush only against real threats
    5. Govern sup when there's a cheap vampire in uncontrolled
    """
    
    def __init__(self, state: GameState, player_id: int):
        self.state = state
        self.player_id = player_id
        self.player = state.player_by_id(player_id)
    
    def should_play_deflection(self, bleed_amount: int) -> bool:
        """Decide whether to play Deflection.
        
        Rules:
        - Only play against bleeds >= 2 (not worth it for small bleeds)
        - Always play if pool <= 10 (critical)
        - Consider predator's remaining actions
        """
        if not self.player:
            return False
        
        # Always deflect big bleeds
        if bleed_amount >= 3:
            return True
        
        # Deflect medium bleeds if pool is low
        if bleed_amount >= 2 and self.player.pool <= 15:
            return True
        
        # Don't waste deflection on small bleeds
        return False
    
    def should_play_stealth(self, action_type: str = 'bleed') -> bool:
        """Decide whether to play stealth cards.
        
        Rules:
        - Play stealth when predator has blockers
        - Play stealth for important actions (bleed, rush)
        - Don't waste stealth on minor actions
        """
        predator = self.state.predator_of(self.player_id)
        if not predator:
            return False
        
        # Check if predator has ready minions (potential blockers)
        predator_crypt_ids = set(predator.crypt)
        ready_minions = sum(
            1
            for c in self.state.cards.values()
            if c.id in predator_crypt_ids
            and c.position == CardPosition.ready
            and c.tipo.strip().lower() in ('vampire', 'ally', 'imbued')
        )
        
        # Play stealth if predator has blockers
        if ready_minions >= 2:
            return True
        
        # Play stealth for important actions
        if action_type in ('bleed', 'rush') and ready_minions >= 1:
            return True
        
        return False
    
    def should_play_modifier(self, modifier_type: str = 'bleed') -> bool:
        """Decide whether to play action modifiers.
        
        Rules:
        - Only play AFTER action is confirmed successful
        - Don't play if action will be blocked anyway
        - Consider modifier value vs risk
        """
        # For now, return True if we have modifiers
        # In a full implementation, this would check:
        # - Was the action already attempted?
        # - Did it get blocked?
        # - What's the success probability?
        return True
    
    def should_play_govern_sup(self) -> bool:
        """Decide whether to use Govern the Unaligned (superior) for acceleration.
        
        Rules:
        - Only use when there's a cheap vampire in uncontrolled
        - Prefer vampires with cap 3-5 (most benefit)
        - Don't use if no uncontrolled vampires
        """
        if not self.player:
            return False
        
        # Check for uncontrolled vampires needing blood
        for cid in self.player.crypt:
            card = self.state.card_by_id(cid)
            if (
                card
                and card.position == CardPosition.uncontrolled
                and card.blood < card.capacity
                and card.capacity <= 6  # Prefer cheaper vampires
            ):
                return True
        
        return False
    
    def should_rush_target(self, target_id: str) -> bool:
        """Decide whether to rush a specific target.
        
        Rules:
        - Rush high-threat targets (high capacity vampires)
        - Rush targets with valuable abilities
        - Don't rush small allies (waste of resources)
        """
        target = self.state.card_by_id(target_id)
        if not target:
            return False
        
        # Rush vampires with high capacity
        if target.tipo.strip().lower() == 'vampire' and target.capacity >= 5:
            return True
        
        # Rush allies with rush ability (they're threats)
        if target.tipo.strip().lower() == 'ally':
            text = (getattr(target, 'text', '') or '').lower()
            if 'enter combat' in text:
                return True
        
        return False
    
    def get_card_priority(self, card: CardInstance) -> int:
        """Get priority for playing a card (higher = play first).
        
        Priority order:
        1. Deflection (defense)
        2. Stealth (if needed)
        3. Action modifiers (after action confirmed)
        4. Action cards (bleed, rush)
        5. Master cards
        """
        if not card:
            return 0
        
        name = card.name.lower()
        tipo = card.tipo.strip().lower()
        
        # Deflection - highest priority (defense)
        if 'deflection' in name:
            return 100
        
        # Stealth cards
        if any(n in name for n in ('cloak', 'seduction', 'where the veil')):
            return 80
        
        # Action modifiers
        if tipo == 'action modifier':
            return 60
        
        # Action cards (bleed, rush)
        if tipo == 'action':
            return 40
        
        # Political actions
        if tipo == 'political action':
            return 40
        
        # Master cards
        if tipo == 'master':
            return 20
        
        return 0
    

class GameStateAnalyzer:
    """Analyzes the game state including prey/predator/cross relationships."""

    def __init__(self, state: GameState, player_id: int):
        self.state = state
        self.player_id = player_id
        self.player = state.player_by_id(player_id)
        
        # Calculate relationships
        self.prey = state.prey_of(player_id)
        self.predator = state.predator_of(player_id)
        self.cross_players = self._calculate_cross_players()
        
    def _calculate_cross_players(self) -> list:
        """Calculate cross-table players (not prey or predator)."""
        active = self.state.active_players
        cross = []
        for p in active:
            if p.id == self.player_id:
                continue
            if self.prey and p.id == self.prey.id:
                continue
            if self.predator and p.id == self.predator.id:
                continue
            cross.append(p)
        return cross
    
    def get_predator_of(self, player_id: int) -> 'PlayerState | None':
        """Get the predator of any player."""
        return self.state.predator_of(player_id)
    
    def get_prey_of(self, player_id: int) -> 'PlayerState | None':
        """Get the prey of any player."""
        return self.state.prey_of(player_id)
    
    def should_help_cross(self, cross_player, threat_assessor: ThreatAssessment) -> bool:
        """Determine if we should help a cross player.
        
        We help cross players by attacking their predator, which:
        1. Weakens a common threat
        2. Creates goodwill
        3. May lead to indirect benefits
        """
        if not cross_player:
            return False
        
        # Get the predator of the cross player
        cross_predator = self.get_predator_of(cross_player.id)
        if not cross_predator:
            return False
        
        # Assess threats
        my_threat = threat_assessor.assess(self.state, self.player_id)
        cross_threat = threat_assessor.assess(self.state, cross_player.id)
        predator_threat = threat_assessor.assess(self.state, cross_predator.id)
        
        # Help if:
        # 1. Cross predator is a significant threat (to us or cross)
        if predator_threat > 5.0:
            return True
        
        # 2. Cross is weak and we want an ally
        if cross_player.pool < 10 and cross_threat < 3.0:
            return True
        
        # 3. We're strong enough to help without risk
        if my_threat > 6.0 and self.player.pool > 15:
            return True
        
        return False
    
    def get_strategic_position(self, threat_assessor: ThreatAssessment) -> str:
        """Evaluate our strategic position.
        
        Returns:
        - 'aggressive': We're winning, press advantage
        - 'defensive': We're losing, need to survive
        - 'diplomatic': Balanced, help cross to build alliances
        - 'balanced': Normal play
        """
        if not self.player:
            return 'balanced'
        
        my_threat = threat_assessor.assess(self.state, self.player_id)
        
        prey_threat = 0
        if self.prey:
            prey_threat = threat_assessor.assess(self.state, self.prey.id)
        
        predator_threat = 0
        if self.predator:
            predator_threat = threat_assessor.assess(self.state, self.predator.id)
        
        # Check victory points
        vp = self.player.victory_points
        
        # Aggressive: strong position, high VP
        if my_threat > 6.0 and vp >= 1:
            return 'aggressive'
        
        # Defensive: weak position or strong predator
        if self.player.pool < 10 or predator_threat > 7.0:
            return 'defensive'
        
        # Diplomatic: balanced, help cross
        if abs(my_threat - prey_threat) < 2.0:
            return 'diplomatic'
        
        return 'balanced'


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

    def determine_game_phase(self, state: GameState, player_id: int) -> GamePhase:
        """Determine the current game phase based on turn and board state."""
        turn = state.turn_number
        alive = sum(1 for p in state.players if not p.is_ousted)
        player = state.player_by_id(player_id)

        # Final phase: only 2 players left
        if alive <= 2:
            return GamePhase.FINAL

        # Late game: turn 16+ or player has 2+ VP
        if turn >= 16 or (player and player.victory_points >= 2):
            return GamePhase.LATE

        # Mid game: turns 6-15
        if turn >= 6:
            return GamePhase.MID

        # Early game: turns 1-5
        return GamePhase.EARLY

    def get_adjusted_strategy(
        self, strategy: DeckStrategy, phase: GamePhase
    ) -> dict[str, float]:
        """Get phase-adjusted priorities and thresholds."""
        adj = strategy.get_phase_adjustments(phase)

        return {
            "bleed_priority": strategy.get_adjusted_priority(
                strategy.bleed_priority, adj.bleed_modifier
            ),
            "rush_priority": strategy.get_adjusted_priority(
                strategy.rush_priority, adj.rush_modifier
            ),
            "vote_priority": strategy.get_adjusted_priority(
                strategy.vote_priority, adj.vote_modifier
            ),

            "shroud_priority": strategy.get_adjusted_priority(
                strategy.shroud_priority, adj.shroud_modifier
            ),
            "stealth_priority": strategy.get_adjusted_priority(
                strategy.stealth_priority, adj.stealth_modifier
            ),
            "control_priority": strategy.get_adjusted_priority(
                strategy.control_priority, adj.control_modifier
            ),
            "bloat_priority": strategy.get_adjusted_priority(
                strategy.bloat_priority, adj.bloat_modifier
            ),
            "rush_threshold": max(
                0, strategy.rush_threshold + adj.rush_threshold_modifier
            ),
            "control_threshold": max(
                0, strategy.control_threshold + adj.control_threshold_modifier
            ),
            "bloat_threshold": max(
                0, strategy.bloat_threshold + adj.bloat_threshold_modifier
            ),
        }

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

        # Determine game phase and get adjusted priorities
        phase = self.determine_game_phase(state, player_id)
        adjusted = self.get_adjusted_strategy(strategy, phase)

        # Analyze game state including prey/predator/cross
        analyzer = GameStateAnalyzer(state, player_id)
        strategic_position = analyzer.get_strategic_position(self.threat_assessor)

        # Assess threats
        prey_threat = (
            self.threat_assessor.assess(state, analyzer.prey.id) if analyzer.prey else 0
        )
        predator_threat = (
            self.threat_assessor.assess(state, analyzer.predator.id) if analyzer.predator else 0
        )

        # Check own pool with phase-adjusted threshold
        own_pool_low = player.pool < adjusted["bloat_threshold"]

        # Decide action based on adjusted priorities and strategic position
        return self._decide_action(
            strategy=strategy,
            adjusted=adjusted,
            phase=phase,
            minion=minion,
            player=player,
            state=state,
            analyzer=analyzer,
            strategic_position=strategic_position,
            prey_threat=prey_threat,
            predator_threat=predator_threat,
            own_pool_low=own_pool_low,
            is_vampire=is_vampire,
            is_ally=is_ally,
        )

    def _decide_action(
        self,
        strategy: DeckStrategy,
        adjusted: dict[str, float],
        phase: GamePhase,
        minion: CardInstance,
        player: Any,
        state: GameState,
        analyzer: GameStateAnalyzer,
        strategic_position: str,
        prey_threat: float,
        predator_threat: float,
        own_pool_low: bool,
        is_vampire: bool,
        is_ally: bool,
    ) -> str:
        """Core decision logic with phase-adjusted priorities.
        
        Args:
            analyzer: GameStateAnalyzer with prey/predator/cross info
            strategic_position: 'aggressive', 'defensive', 'diplomatic', or 'balanced'
        """

        # 1. Bloat if pool is low
        if own_pool_low and adjusted["bloat_priority"] > 0:
            if self._has_bloat_card(state, player):
                return "action_card"

        # 2. Rush if ally with rush ability OR has rush card in hand
        if adjusted["rush_priority"] > 0:
            can_rush = False
            
            # Check if minion has rush ability (ally)
            if is_ally and self._has_rush_ability(minion):
                can_rush = True
            
            # Check if player has rush action card in hand
            if self._has_rush_card(state, player):
                can_rush = True
            
            if can_rush:
                # Rush high-threat targets
                if predator_threat >= adjusted["rush_threshold"]:
                    return "rush"
                if prey_threat >= adjusted["rush_threshold"]:
                    return "rush"
                
                # Rush cross player's predator if we should help cross
                if strategic_position == 'diplomatic' and analyzer.cross_players:
                    for cross in analyzer.cross_players:
                        if analyzer.should_help_cross(cross, self.threat_assessor):
                            cross_predator = analyzer.get_predator_of(cross.id)
                            if cross_predator and self._can_attack_target(state, cross_predator.id):
                                return "rush"
                
                # Random rush based on priority
                if state.random.random() < adjusted["rush_priority"] * 0.3:
                    return "rush"

        # 3. Recruit allies (especially in early game)
        if self._has_ally_card(state, player):
            # Early game: recruit cheap allies for board presence
            if phase == GamePhase.EARLY:
                if self._has_cheap_ally(state, player, max_cost=3):
                    if state.random.random() < 0.4:
                        return "action_card"
            # Mid game: recruit allies if has rush potential
            elif phase == GamePhase.MID:
                ally_count = self.count_ally_cards(state, player)
                if ally_count >= 2:  # Multiple allies = swarm potential
                    if state.random.random() < 0.3:
                        return "action_card"

        # 4. Control if threat is high
        if adjusted["control_priority"] > 0:
            max_threat = max(prey_threat, predator_threat)
            if max_threat >= adjusted["control_threshold"]:
                # Use control cards (Shroud, etc.)
                if self._has_control_card(state, player):
                    return "action_card"

        # 5. Action cards (bleed, Govern, Shroud, etc.)
        # Logic varies by phase and strategic position:
        # - Early: Prefer blood acceleration (if uncontrolled vampires)
        # - Mid/Late: Prefer bleed actions
        # - Diplomatic: Help cross by attacking their predator
        if is_vampire and self._has_action_cards(state, player):
            if phase == GamePhase.EARLY:
                # Early game: Check if we have uncontrolled vampires needing blood
                if self._has_uncontrolled_needing_blood(state, player):
                    # Use action card for blood acceleration
                    if state.random.random() < adjusted["bleed_priority"] * 0.4:
                        return "action_card"
            elif strategic_position == 'diplomatic' and analyzer.cross_players:
                # Diplomatic: Help cross by attacking their predator
                for cross in analyzer.cross_players:
                    if analyzer.should_help_cross(cross, self.threat_assessor):
                        cross_predator = analyzer.get_predator_of(cross.id)
                        if cross_predator:
                            # Use action card against cross's predator
                            if state.random.random() < 0.4:
                                return "action_card"
            else:
                # Mid/Late: Use action cards for bleed
                if state.random.random() < adjusted["bleed_priority"] * 0.3:
                    return "action_card"

        # 5. Vote if available and vampire with title
        if (
            is_vampire
            and adjusted["vote_priority"] > 0
            and player.has_title
        ):
            if self._has_political_card(state, player):
                # Higher chance to vote in mid/late game
                vote_chance = adjusted["vote_priority"] * 0.5
                # Increase if prey has high threat
                if prey_threat > 5:
                    vote_chance += 0.2
                # Decrease if early game
                if phase == GamePhase.EARLY:
                    vote_chance *= 0.6
                if state.random.random() < min(vote_chance, 0.9):
                    return "political"

        # 6. Bleed (default) - with boost from cards in hand
        # Adjust based on strategic position:
        # - Aggressive: More bleed
        # - Defensive: Less bleed, more control
        # - Diplomatic: Moderate bleed, help cross
        if adjusted["bleed_priority"] > 0:
            bleed_boost = 0.0
            
            # Strategic position adjustments
            if strategic_position == 'aggressive':
                bleed_boost += 0.2  # Press advantage
            elif strategic_position == 'defensive':
                bleed_boost -= 0.1  # Less aggressive
            elif strategic_position == 'diplomatic':
                bleed_boost += 0.1  # Moderate
            
            # Boost if has bleed action card
            if self._has_bleed_card(state, player):
                bleed_boost += 0.15
            
            # Boost if has bleed modifier
            if self._has_bleed_modifier(state, player):
                bleed_boost += 0.15
            
            # Extra boost if has multiple modifiers (powerbleed)
            modifier_count = sum(
                1 for cid in player.hand
                if state.card_by_id(cid)
                and state.card_by_id(cid).tipo.strip().lower() == 'action modifier'
            )
            if modifier_count >= 2:
                bleed_boost += 0.1
            
            # Check for stealth cards
            if adjusted["stealth_priority"] > 0:
                if self._has_stealth_card(state, player):
                    if state.random.random() < adjusted["stealth_priority"] * 0.5:
                        return "action_card"
            
            # Apply boost to bleed priority
            final_bleed_chance = adjusted["bleed_priority"] + bleed_boost
            if state.random.random() < min(final_bleed_chance, 0.9):
                return "bleed"
            
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

    def _can_attack_target(self, state: GameState, target_id: str) -> bool:
        """Check if we can attack a specific target.
        
        This checks if we have a rush ability or rush card available.
        """
        # For now, return True if we have rush capability
        # A more sophisticated version would check if target is in range
        return True

    def _has_rush_card(self, state: GameState, player: Any) -> bool:
        """Check if player has rush action cards in hand.
        
        Rush cards have 'action.rush' effect in their JSON data.
        Examples: Ambush, Big Game, Bum's Rush, Charge of the Buffalo.
        """
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                # Check abilities for action.rush effect
                abilities = getattr(card, 'abilities', None) or []
                for ab in abilities:
                    effects = getattr(ab, 'effects', None) or []
                    for eff in effects:
                        if getattr(eff, 'function', '') == 'action.rush':
                            return True
        return False

    def _has_ally_card(self, state: GameState, player: Any) -> bool:
        """Check if player has ally cards in hand that can be recruited.
        
        Ally cards have tipo='Ally' and can be recruited as action.
        Examples: Freakish Conglomeration, Raven Spy, etc.
        """
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                tipo = card.tipo.strip().lower()
                if tipo == 'ally':
                    return True
        return False

    def count_ally_cards(self, state: GameState, player: Any) -> int:
        """Count ally cards in hand."""
        count = 0
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and card.tipo.strip().lower() == 'ally':
                count += 1
        return count

    def _has_cheap_ally(self, state: GameState, player: Any, max_cost: int = 3) -> bool:
        """Check if player has low-cost ally cards in hand."""
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and card.tipo.strip().lower() == 'ally':
                cost = getattr(card, 'pool_cost', 0) or 0
                if cost <= max_cost:
                    return True
        return False

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

                        "pentex",
                        "misdirection",
                    )
                ):
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

    def _has_action_cards(self, state: GameState, player: Any) -> bool:
        """Check if player has any action cards (bleed, Govern, etc.)."""
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                t = card.tipo.strip().lower()
                if t in ('action', 'political action'):
                    return True
        return False

    def _has_bleed_card(self, state: GameState, player: Any) -> bool:
        """Check if player has action cards that bleed.
        
        These cards have 'bleed' in their text or effects.
        Examples: Govern the Unaligned, Deep Song, Computer Hacking.
        """
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card:
                # Check by text pattern
                text = (getattr(card, 'text', '') or '').lower()
                if 'bleed' in text and card.tipo.strip().lower() == 'action':
                    return True
                # Check abilities for bleed effects
                abilities = getattr(card, 'abilities', None) or []
                for ab in abilities:
                    effects = getattr(ab, 'effects', None) or []
                    for eff in effects:
                        func = getattr(eff, 'function', '')
                        if 'bleed' in func.lower():
                            return True
        return False

    def _has_bleed_modifier(self, state: GameState, player: Any) -> bool:
        """Check if player has action modifiers that increase bleed.
        
        These cards have '+X bleed' in their text.
        Examples: Conditioning, Bonding, Command of the Beast.
        """
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and card.tipo.strip().lower() == 'action modifier':
                text = (getattr(card, 'text', '') or '').lower()
                # Check for bleed increase
                if '+bleed' in text or '+1 bleed' in text or '+2 bleed' in text:
                    return True
                # Check abilities
                abilities = getattr(card, 'abilities', None) or []
                for ab in abilities:
                    effects = getattr(ab, 'effects', None) or []
                    for eff in effects:
                        func = getattr(eff, 'function', '')
                        if 'bleed' in func.lower():
                            return True
        return False

    def count_bleed_bonus(self, state: GameState, player: Any) -> int:
        """Count total bleed bonus available from modifiers in hand."""
        total = 0
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and card.tipo.strip().lower() == 'action modifier':
                # Check card's bleed value
                total += getattr(card, 'bleed', 0)
                # Check abilities for bleed bonus
                abilities = getattr(card, 'abilities', None) or []
                for ab in abilities:
                    effects = getattr(ab, 'effects', None) or []
                    for eff in effects:
                        params = getattr(eff, 'params', {})
                        if isinstance(params, dict):
                            total += params.get('bleed_bonus', 0)
        return total

    def _has_uncontrolled_needing_blood(self, state: GameState, player: Any) -> bool:
        """Check if player has uncontrolled vampires that need blood."""
        for cid in player.crypt:
            card = state.card_by_id(cid)
            if (
                card
                and card.position == CardPosition.uncontrolled
                and card.blood < card.capacity
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
