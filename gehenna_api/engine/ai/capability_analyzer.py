"""Player Capability Analyzer for V:TES.

Analyzes player capabilities based on:
- Combat module (defensive vs aggressive)
- Reaction capabilities
- Card probabilities based on ash heap
- Discipline-based card access
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gehenna_api.engine.state import GameState
from gehenna_api.engine.card_instance import CardInstance, CardPosition


# Card categories for analysis
COMBAT_CATEGORIES = {
    'defensive': [
        'maneuver', 'dodge', 'prevent', 'combat_ends',
        'armor', 'shield', 'fortitude',
    ],
    'aggressive': [
        'damage', 'aggravated', 'press', 'strike',
        'claws', 'strength',
    ],
    'utility': [
        'stealth_combat', 'intercept', 'redirection',
    ],
}

REACTION_CATEGORIES = {
    'bounce': [
        'redirect', 'deflection', 'bounce', 'misdirection',
    ],
    'intercept': [
        'intercept', 'awake', 'sense_vitality',
    ],
    'stealth_reaction': [
        'secret_passage', 'elder_visions',
    ],
    'combat_ends_reaction': [
        'side_step', 'lightning_reflexes',
    ],
}

# Discipline → Card access mapping
DISCIPLINE_CARDS = {
    'CEL': {  # Celerity
        'aggressive': ['extra_strike', 'quick_strike'],
        'defensive': ['dodge'],
    },
    'FOR': {  # Fortitude
        'defensive': ['prevent', 'damage_prevention', 'toughness'],
        'utility': ['unflinching'],
    },
    'PRO': {  # Protean
        'aggressive': ['claws', 'aggravated', 'earth_meld'],
        'defensive': ['skin_of_the_chameleon'],
    },
    'POT': {  # Potence
        'aggressive': ['strength', 'immortal_grapple', 'claws'],
        'utility': ['force'],
    },
    'PRE': {  # Presence
        'utility': ['awe', 'invoke恐惧'],
    },
    'DOM': {  # Dominate
        'utility': ['govern', 'conditioning'],
    },
    'OBF': {  # Obfuscate
        'stealth': ['hide', 'shadow_cloak'],
    },
    'AUS': {  # Auspex
        'intercept': ['awake', 'telepathic_tracking'],
    },
    'TEM': {  # Thaumaturgy
        'aggravated': ['blood_golem', 'flames'],
        'utility': ['path_of_death'],
    },
    'Qui': {  # Quietus
        'aggravated': ['silence', 'acrobatic_leap'],
    },
}

# Standard deck sizes for probability calculations
STANDARD_DECK_SIZE = 60  # Library size
STANDARD_HAND_SIZE = 7   # Maximum hand size


@dataclass
class CombatModule:
    """Analysis of a player's combat capabilities."""
    defensive_score: float = 0.0
    aggressive_score: float = 0.0
    utility_score: float = 0.0
    
    # Specific counts
    maneuver_count: int = 0
    dodge_count: int = 0
    prevent_count: int = 0
    combat_ends_count: int = 0
    press_count: int = 0
    aggravated_count: int = 0
    
    # Disciplines
    combat_disciplines: list[str] = field(default_factory=list)
    
    @property
    def is_defensive(self) -> bool:
        return self.defensive_score > self.aggressive_score * 1.5
    
    @property
    def is_aggressive(self) -> bool:
        return self.aggressive_score > self.defensive_score * 1.5
    
    @property
    def module_type(self) -> str:
        if self.is_defensive:
            return 'defensive'
        elif self.is_aggressive:
            return 'aggressive'
        return 'balanced'
    
    @property
    def total_combat_cards(self) -> int:
        return (
            self.maneuver_count + self.dodge_count +
            self.prevent_count + self.combat_ends_count +
            self.press_count + self.aggravated_count
        )


@dataclass
class ReactionCapabilities:
    """Analysis of a player's reaction capabilities."""
    bounce_count: int = 0
    intercept_count: int = 0
    stealth_reaction_count: int = 0
    combat_ends_count: int = 0
    
    # Probability of having bounce in hand
    bounce_probability: float = 0.0
    intercept_probability: float = 0.0
    
    @property
    def total_reactions(self) -> int:
        return (
            self.bounce_count + self.intercept_count +
            self.stealth_reaction_count + self.combat_ends_count
        )


@dataclass
class CardProbabilities:
    """Probabilities of player having certain cards."""
    has_bounce: float = 0.0
    has_redirect: float = 0.0
    has_combat_ends: float = 0.0
    has_prevent: float = 0.0
    has_aggravated: float = 0.0
    has_press: float = 0.0


class CapabilityAnalyzer:
    """Analyzes player capabilities for strategic decisions."""
    
    def __init__(self, state: GameState, player_id: int):
        self.state = state
        self.player_id = player_id
        self.player = state.player_by_id(player_id)
    
    def analyze_combat_module(self) -> CombatModule:
        """Analyze a player's combat module based on cards and disciplines."""
        module = CombatModule()
        
        if not self.player:
            return module
        
        # Analyze all cards (hand + ash heap)
        all_cards = self._get_all_player_cards()
        
        for card in all_cards:
            card_name = card.name.lower()
            card_text = (getattr(card, 'text', '') or '').lower()
            
            # Check for defensive cards
            for keyword in COMBAT_CATEGORIES['defensive']:
                if keyword in card_name or keyword in card_text:
                    module.defensive_score += 1.0
                    self._count_combat_card(module, keyword)
            
            # Check for aggressive cards
            for keyword in COMBAT_CATEGORIES['aggressive']:
                if keyword in card_name or keyword in card_text:
                    module.aggressive_score += 1.0
                    self._count_combat_card(module, keyword)
        
        # Analyze disciplines
        module.combat_disciplines = self._get_combat_disciplines()
        
        # Adjust scores based on disciplines
        for disc in module.combat_disciplines:
            disc_cards = DISCIPLINE_CARDS.get(disc, {})
            for category, cards in disc_cards.items():
                if category == 'defensive':
                    module.defensive_score += 0.5
                elif category == 'aggressive':
                    module.aggressive_score += 0.5
        
        return module
    
    def analyze_reactions(self) -> ReactionCapabilities:
        """Analyze a player's reaction capabilities."""
        reactions = ReactionCapabilities()
        
        if not self.player:
            return reactions
        
        # Count cards in hand and ash heap
        all_cards = self._get_all_player_cards()
        
        for card in all_cards:
            card_name = card.name.lower()
            card_text = (getattr(card, 'text', '') or '').lower()
            card_tipo = card.tipo.strip().lower()
            
            # Only count reaction cards
            if card_tipo != 'reaction':
                continue
            
            # Check for bounce
            for keyword in REACTION_CATEGORIES['bounce']:
                if keyword in card_name or keyword in card_text:
                    reactions.bounce_count += 1
            
            # Check for intercept
            for keyword in REACTION_CATEGORIES['intercept']:
                if keyword in card_name or keyword in card_text:
                    reactions.intercept_count += 1
            
            # Check for stealth reactions
            for keyword in REACTION_CATEGORIES['stealth_reaction']:
                if keyword in card_name or keyword in card_text:
                    reactions.stealth_reaction_count += 1
            
            # Check for combat ends
            for keyword in REACTION_CATEGORIES['combat_ends_reaction']:
                if keyword in card_name or keyword in card_text:
                    reactions.combat_ends_count += 1
        
        # Calculate probabilities
        reactions.bounce_probability = self._calculate_card_probability(
            reactions.bounce_count, 'reaction'
        )
        reactions.intercept_probability = self._calculate_card_probability(
            reactions.intercept_count, 'reaction'
        )
        
        return reactions
    
    def calculate_card_probabilities(self) -> CardProbabilities:
        """Calculate probabilities of player having certain cards."""
        probs = CardProbabilities()
        
        if not self.player:
            return probs
        
        # Count cards by category in hand + ash heap
        all_cards = self._get_all_player_cards()
        
        bounce_count = 0
        redirect_count = 0
        combat_ends_count = 0
        prevent_count = 0
        aggravated_count = 0
        press_count = 0
        
        for card in all_cards:
            card_name = card.name.lower()
            card_text = (getattr(card, 'text', '') or '').lower()
            
            # Bounce/redirect
            for keyword in REACTION_CATEGORIES['bounce']:
                if keyword in card_name or keyword in card_text:
                    bounce_count += 1
                    redirect_count += 1
            
            # Combat ends
            for keyword in ['combat_ends', 'side_step']:
                if keyword in card_name or keyword in card_text:
                    combat_ends_count += 1
            
            # Prevent
            for keyword in ['prevent', 'damage_prevention']:
                if keyword in card_name or keyword in card_text:
                    prevent_count += 1
            
            # Aggravated
            for keyword in ['aggravated', 'aggravated_damage']:
                if keyword in card_name or keyword in card_text:
                    aggravated_count += 1
            
            # Press
            for keyword in ['press', 'additional_press']:
                if keyword in card_name or keyword in card_text:
                    press_count += 1
        
        # Calculate probabilities
        probs.has_bounce = self._calculate_card_probability(bounce_count)
        probs.has_redirect = self._calculate_card_probability(redirect_count)
        probs.has_combat_ends = self._calculate_card_probability(combat_ends_count)
        probs.has_prevent = self._calculate_card_probability(prevent_count)
        probs.has_aggravated = self._calculate_card_probability(aggravated_count)
        probs.has_press = self._calculate_card_probability(press_count)
        
        return probs
    
    def get_strategic_assessment(self) -> dict:
        """Get overall strategic assessment of a player."""
        combat = self.analyze_combat_module()
        reactions = self.analyze_reactions()
        probabilities = self.calculate_card_probabilities()
        
        return {
            'combat_module': combat.module_type,
            'defensive_strength': combat.defensive_score,
            'aggressive_strength': combat.aggressive_score,
            'total_combat_cards': combat.total_combat_cards,
            'bounce_probability': reactions.bounce_probability,
            'intercept_probability': reactions.intercept_probability,
            'can_bleed_safely': probabilities.has_bounce < 0.3,
            'can_rush_safely': probabilities.has_combat_ends < 0.4,
            'needs_stealth': probabilities.has_intercept > 0.5,
        }
    
    def _get_all_player_cards(self) -> list[CardInstance]:
        """Get all cards associated with a player."""
        cards = []
        
        if not self.player:
            return cards
        
        # Cards in hand
        for cid in self.player.hand:
            card = self.state.card_by_id(cid)
            if card:
                cards.append(card)
        
        # Cards in ash heap
        for cid in self.player.ash_heap:
            card = self.state.card_by_id(cid)
            if card:
                cards.append(card)
        
        # Cards in play (crypt + library in play)
        for cid in self.player.crypt:
            card = self.state.card_by_id(cid)
            if card:
                cards.append(card)
        
        return cards
    
    def _get_combat_disciplines(self) -> list[str]:
        """Get combat-related disciplines for a player."""
        disciplines = []
        
        if not self.player:
            return disciplines
        
        for cid in self.player.crypt:
            card = self.state.card_by_id(cid)
            if not card:
                continue
            
            disc_str = getattr(card, 'disciplines', '') or ''
            # Parse discipline string
            for i in range(0, len(disc_str) - 2, 3):
                if i + 2 < len(disc_str):
                    disc = disc_str[i:i+2].upper()
                    if disc in DISCIPLINE_CARDS and disc not in disciplines:
                        disciplines.append(disc)
        
        return disciplines
    
    def _count_combat_card(self, module: CombatModule, keyword: str) -> None:
        """Count specific combat card types."""
        if keyword == 'maneuver':
            module.maneuver_count += 1
        elif keyword == 'dodge':
            module.dodge_count += 1
        elif keyword in ('prevent', 'damage_prevention'):
            module.prevent_count += 1
        elif keyword == 'combat_ends':
            module.combat_ends_count += 1
        elif keyword == 'press':
            module.press_count += 1
        elif keyword in ('aggravated', 'aggravated_damage'):
            module.aggravated_count += 1
    
    def _calculate_card_probability(
        self,
        cards_seen: int,
        card_type: str = 'any',
    ) -> float:
        """Calculate probability of player having a card type.
        
        Uses hypergeometric distribution approximation:
        - Total cards in deck: ~60
        - Cards in hand: up to 7
        - Cards seen: in ash heap
        """
        if not self.player:
            return 0.0
        
        # Estimate total cards of this type in deck
        # Typical deck has ~10-15 reactions, ~8-12 combat cards
        estimated_total = {
            'reaction': 12,
            'combat': 10,
            'any': 20,
        }.get(card_type, 10)
        
        # Cards remaining in library
        library_size = len(self.player.library)
        total_remaining = library_size + len(self.player.hand)
        
        if total_remaining == 0:
            return 0.0
        
        # Probability of having at least one in hand
        # P(at least 1) = 1 - P(none in hand)
        hand_size = len(self.player.hand)
        
        if hand_size == 0 or estimated_total == 0:
            return 0.0
        
        # Simple approximation
        p_none = 1.0
        for i in range(hand_size):
            p_none *= (1 - (estimated_total / (total_remaining - i)))
        
        return max(0.0, min(1.0, 1.0 - p_none))
