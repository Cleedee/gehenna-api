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
        'skin of the', 'toughness',
    ],
    'aggressive': [
        'damage', 'aggravated', 'press', 'strike',
        'claws', 'strength', 'immortal grapple',
        'flesh of marble', 'earth meld',
    ],
    'utility': [
        'stealth_combat', 'intercept', 'redirection',
        'quick strike', 'acrobatic leap',
    ],
}

REACTION_CATEGORIES = {
    'bounce': [
        'redirect', 'deflection', 'bounce', 'misdirection',
        'two wrongs', 'bait and switch',
    ],
    'intercept': [
        'intercept', 'awake', 'sense_vitality',
        'on the qtv', 'enhanced senses',
    ],
    'stealth_reaction': [
        'secret_passage', 'elder_visions',
        'lost in crowds', 'faceless night',
    ],
    'combat_ends_reaction': [
        'side step', 'lightning reflexes',
        'swiftness', 'blur',
    ],
}

# Bleed and stealth card categories
BLEED_STEALTH_CATEGORIES = {
    'bleed_action': [
        'bleed', 'govern', 'conditioning', 'instantaneous transformation',
        'bonding', 'rapid', 'intimidation', 'scouting',
        'lost in crowds', 'faceless night',
    ],
    'bleed_modifier': [
        '+1 bleed', '+2 bleed', '+3 bleed', '+4 bleed',
        'bleed modifier', 'additional bleed', 'bleed bonus',
    ],
    'stealth': [
        'stealth', '+1 stealth', '+2 stealth', '+3 stealth',
        'lost in crowds', 'faceless night', 'elder impersonation',
        'cloak the gathering', 'instantaneous transformation',
        'secret passage', 'elder visions',
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


@dataclass
class BleedStealthCapabilities:
    """Analysis of a player's bleed and stealth capabilities."""
    # Bleed cards
    bleed_action_count: int = 0
    bleed_modifier_count: int = 0
    total_bleed_cards: int = 0
    
    # Stealth cards
    stealth_count: int = 0
    
    # Probabilities
    bleed_probability: float = 0.0
    stealth_probability: float = 0.0
    
    # Average bleed bonus per card
    avg_bleed_bonus: float = 0.0
    
    @property
    def can_bleed(self) -> bool:
        return self.bleed_action_count > 0 or self.bleed_modifier_count > 0
    
    @property
    def can_stealth(self) -> bool:
        return self.stealth_count > 0
    
    @property
    def bleed_threat(self) -> str:
        """Assess bleed threat level."""
        if self.total_bleed_cards >= 5:
            return 'high'
        elif self.total_bleed_cards >= 3:
            return 'medium'
        return 'low'
    
    @property
    def stealth_threat(self) -> str:
        """Assess stealth threat level."""
        if self.stealth_count >= 3:
            return 'high'
        elif self.stealth_count >= 1:
            return 'medium'
        return 'low'


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
            # Get all keywords from card
            card_keywords = self._get_card_keywords(card)
            card_text = ' '.join(card_keywords)
            
            # Check for defensive cards
            for keyword in COMBAT_CATEGORIES['defensive']:
                if keyword in card_text:
                    module.defensive_score += 1.0
                    self._count_combat_card(module, keyword)
            
            # Check for aggressive cards
            for keyword in COMBAT_CATEGORIES['aggressive']:
                if keyword in card_text:
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
            # Get all keywords from card
            card_keywords = self._get_card_keywords(card)
            card_text = ' '.join(card_keywords)
            card_tipo = card.tipo.strip().lower()
            
            # Only count reaction cards
            if card_tipo != 'reaction':
                continue
            
            # Check for bounce
            for keyword in REACTION_CATEGORIES['bounce']:
                if keyword in card_text:
                    reactions.bounce_count += 1
            
            # Check for intercept
            for keyword in REACTION_CATEGORIES['intercept']:
                if keyword in card_text:
                    reactions.intercept_count += 1
            
            # Check for stealth reactions
            for keyword in REACTION_CATEGORIES['stealth_reaction']:
                if keyword in card_text:
                    reactions.stealth_reaction_count += 1
            
            # Check for combat ends
            for keyword in REACTION_CATEGORIES['combat_ends_reaction']:
                if keyword in card_text:
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
            # Get all keywords from card
            card_keywords = self._get_card_keywords(card)
            card_text = ' '.join(card_keywords)
            
            # Bounce/redirect
            for keyword in REACTION_CATEGORIES['bounce']:
                if keyword in card_text:
                    bounce_count += 1
                    redirect_count += 1
            
            # Combat ends
            for keyword in ['combat_ends', 'side_step', 'combat', 'ends']:
                if keyword in card_text:
                    combat_ends_count += 1
            
            # Prevent
            for keyword in ['prevent', 'damage_prevention', 'prevent_damage']:
                if keyword in card_text:
                    prevent_count += 1
            
            # Aggravated
            for keyword in ['aggravated', 'aggravated_damage']:
                if keyword in card_text:
                    aggravated_count += 1
            
            # Press
            for keyword in ['press', 'additional_press']:
                if keyword in card_text:
                    press_count += 1
        
        # Calculate probabilities
        probs.has_bounce = self._calculate_card_probability(bounce_count)
        probs.has_redirect = self._calculate_card_probability(redirect_count)
        probs.has_combat_ends = self._calculate_card_probability(combat_ends_count)
        probs.has_prevent = self._calculate_card_probability(prevent_count)
        probs.has_aggravated = self._calculate_card_probability(aggravated_count)
        probs.has_press = self._calculate_card_probability(press_count)
        
        return probs
    
    def analyze_bleed_stealth(self) -> BleedStealthCapabilities:
        """Analyze a player's bleed and stealth capabilities."""
        caps = BleedStealthCapabilities()
        
        if not self.player:
            return caps
        
        # Analyze all cards (hand + ash heap)
        all_cards = self._get_all_player_cards()
        
        bleed_bonus_total = 0
        
        for card in all_cards:
            # Get all keywords from card
            card_keywords = self._get_card_keywords(card)
            card_text = ' '.join(card_keywords)
            card_tipo = card.tipo.strip().lower()
            
            # Check for bleed actions (action or action_modifier)
            if card_tipo in ('action', 'action_modifier'):
                for keyword in BLEED_STEALTH_CATEGORIES['bleed_action']:
                    if keyword in card_text:
                        caps.bleed_action_count += 1
                        caps.total_bleed_cards += 1
                        break
            
            # Check for bleed modifiers
            for keyword in BLEED_STEALTH_CATEGORIES['bleed_modifier']:
                if keyword in card_text:
                    caps.bleed_modifier_count += 1
                    caps.total_bleed_cards += 1
                    
                    # Extract bleed bonus value
                    if '+1 bleed' in card_text:
                        bleed_bonus_total += 1
                    elif '+2 bleed' in card_text:
                        bleed_bonus_total += 2
                    elif '+3 bleed' in card_text:
                        bleed_bonus_total += 3
                    elif '+4 bleed' in card_text:
                        bleed_bonus_total += 4
                    break
            
            # Check for stealth
            for keyword in BLEED_STEALTH_CATEGORIES['stealth']:
                if keyword in card_text:
                    caps.stealth_count += 1
                    break
        
        # Calculate probabilities
        caps.bleed_probability = self._calculate_card_probability(
            caps.total_bleed_cards, 'action'
        )
        caps.stealth_probability = self._calculate_card_probability(
            caps.stealth_count, 'action_modifier'
        )
        
        # Calculate average bleed bonus
        if caps.bleed_modifier_count > 0:
            caps.avg_bleed_bonus = bleed_bonus_total / caps.bleed_modifier_count
        
        return caps
    
    def get_strategic_assessment(self) -> dict:
        """Get overall strategic assessment of a player."""
        combat = self.analyze_combat_module()
        reactions = self.analyze_reactions()
        probabilities = self.calculate_card_probabilities()
        bleed_stealth = self.analyze_bleed_stealth()
        
        return {
            # Combat
            'combat_module': combat.module_type,
            'defensive_strength': combat.defensive_score,
            'aggressive_strength': combat.aggressive_score,
            'total_combat_cards': combat.total_combat_cards,
            # Reactions
            'bounce_probability': reactions.bounce_probability,
            'intercept_probability': reactions.intercept_probability,
            # Bleed/Stealth
            'bleed_cards': bleed_stealth.total_bleed_cards,
            'bleed_threat': bleed_stealth.bleed_threat,
            'stealth_cards': bleed_stealth.stealth_count,
            'stealth_threat': bleed_stealth.stealth_threat,
            'avg_bleed_bonus': bleed_stealth.avg_bleed_bonus,
            # Strategic
            'can_bleed_safely': reactions.bounce_probability < 0.3,
            'can_rush_safely': probabilities.has_combat_ends < 0.4,
            'needs_stealth': reactions.intercept_probability > 0.5,
            'should_block_bleed': bleed_stealth.bleed_threat == 'high',
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
    
    def _get_card_keywords(self, card: CardInstance) -> list[str]:
        """Extract keywords from card name, text, and abilities."""
        keywords = []
        
        # Check card name
        name = card.name.lower()
        keywords.extend(name.split())
        
        # Check card text
        text = (getattr(card, 'text', '') or '').lower()
        if text:
            keywords.extend(text.split())
        else:
            # Try to load from database
            db_text = self._load_card_text_from_db(card.card_id)
            if db_text:
                keywords.extend(db_text.lower().split())
        
        # Check abilities and effects
        abilities = getattr(card, 'abilities', None) or []
        for ab in abilities:
            effects = getattr(ab, 'effects', None) or []
            for eff in effects:
                func = getattr(eff, 'function', '')
                if func:
                    keywords.extend(func.lower().split('.'))
                    keywords.extend(func.lower().split('_'))
                
                # Check effect text
                eff_text = getattr(eff, 'text', '') or ''
                keywords.extend(eff_text.lower().split())
        
        return keywords
    
    def _load_card_text_from_db(self, card_id: int) -> str:
        """Load card text from database."""
        try:
            import sqlite3
            from pathlib import Path
            
            db_path = Path(__file__).parent.parent.parent.parent / 'database.db'
            if not db_path.exists():
                return ''
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT text FROM cards WHERE code = ?', (card_id,))
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else ''
        except Exception:
            return ''
    
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
        
        Uses hypergeometric distribution:
        - Total cards in deck: ~80
        - Cards seen: in ash heap
        - Cards remaining: library + hand
        """
        if not self.player:
            return 0.0
        
        # Total cards in deck
        total_deck = len(self.player.library) + len(self.player.ash_heap) + len(self.player.hand)
        
        if total_deck == 0:
            return 0.0
        
        # Estimate total cards of this type in full deck
        # Based on typical deck composition
        estimated_total_in_deck = {
            'reaction': 15,  # ~15% of deck
            'combat': 12,    # ~12% of deck
            'any': 25,       # ~25% of deck
        }.get(card_type, 15)
        
        # If we've seen cards in ash heap, adjust estimate
        # P(having at least one in remaining cards) = 1 - P(none in remaining)
        remaining_cards = len(self.player.library) + len(self.player.hand)
        
        if remaining_cards == 0:
            return 0.0
        
        # Probability of at least one in remaining cards
        # Using complement: P(at least 1) = 1 - P(none)
        p_none = 1.0
        cards_of_type_remaining = max(0, estimated_total_in_deck - cards_seen)
        
        if cards_of_type_remaining == 0:
            return 0.0
        
        # Simple approximation: probability decreases as we see more cards
        p_has_card = min(1.0, cards_of_type_remaining / remaining_cards)
        
        return max(0.0, min(1.0, p_has_card))
