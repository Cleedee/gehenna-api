"""Discipline Analyzer for V:TES.

Analyzes and learns about discipline combinations:
- Which archetypes they form
- Strengths and weaknesses
- Effective counter-strategies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Discipline codes
DISCIPLINE_CODES = {
    'CEL': 'Celerity',
    'FOR': 'Fortitude',
    'PRO': 'Protean',
    'POT': 'Potence',
    'PRE': 'Presence',
    'DOM': 'Dominate',
    'OBF': 'Obfuscate',
    'AUS': 'Auspex',
    'TEM': 'Thaumaturgy',
    'DAI': 'Daimoinon',
    'Qui': 'Quietus',
    'Nec': 'Necromancy',
    'Serp': 'Serpentis',
    'Visc': 'Visceratika',
    'Spir': 'Spiritus',
    'Myt': 'Mytherceria',
    'Val': 'Valeren',
    'Obl': 'Obtenebration',
    'Chim': 'Chimerstry',
    'Fib': 'Fischer',
    'Ani': 'Animalism',
    'Abom': 'Abombwe',
    'Bio': 'Biotech',
    'Dement': 'Dementation',
    'Duo': 'Duo',
    'Mela': 'Melancholy',
    'Temp': 'Temporal',
    'Than': 'Thanatosis',
    'Vic': 'Vicissitude',
}

# Discipline → Archetype tendencies
DISCIPLINE_ARCHETYPES: dict[str, list[str]] = {
    'DOM': ['bleed', 'vote'],        # Dominate: bleed/vote
    'OBF': ['stealth', 'bleed'],     # Obfuscate: stealth/bleed
    'PRE': ['vote', 'bleed'],        # Presence: vote/bleed
    'CEL': ['combat', 'rush'],       # Celerity: combat
    'FOR': ['combat', 'rush'],       # Fortitude: combat
    'PRO': ['combat', 'rush'],       # Protean: combat
    'POT': ['combat', 'rush'],       # Potence: combat
    'AUS': ['toolbox', 'bleed'],     # Auspex: toolbox
    'TEM': ['toolbox', 'combat'],    # Thaumaturgy: toolbox
    'DAI': ['combat', 'infernal'],   # Daimoinon: combat/infernal
    'Qui': ['combat', 'rush'],       # Quietus: combat
    'Nec': ['vote', 'bloat'],        # Necromancy: vote
    'Serp': ['stealth', 'bleed'],    # Serpentis: stealth
    'Visc': ['toolbox', 'combat'],   # Visceratika: toolbox
    'Spir': ['toolbox', 'combat'],   # Spiritus: toolbox
    'Myt': ['toolbox', 'combat'],    # Mytherceria: toolbox
    'Val': ['vote', 'bloat'],        # Valeren: vote
    'Obl': ['bleed', 'stealth'],     # Obtenebration: bleed
    'Chim': ['combat', 'rush'],      # Chimerstry: combat
    'Ani': ['toolbox', 'combat'],    # Animalism: toolbox
}

# Discipline combinations → Specialized archetypes
DISCIPLINE_COMBOS: dict[frozenset, dict] = {
    frozenset(['DOM', 'PRE']): {
        'archetype': 'vote',
        'description': 'Classic vote deck (Dominate + Presence)',
        'strengths': ['strong votes', 'bleed acceleration'],
        'weaknesses': ['slow start', 'vulnerable to rush'],
    },
    frozenset(['CEL', 'POT']): {
        'archetype': 'rush',
        'description': 'Aggressive rush (Celerity + Potence)',
        'strengths': ['fast damage', 'multiple strikes'],
        'weaknesses': ['no stealth', 'vulnerable to combat ends'],
    },
    frozenset(['CEL', 'FOR']): {
        'archetype': 'combat',
        'description': 'Defensive combat (Celerity + Fortitude)',
        'strengths': ['durability', 'maneuvers'],
        'weaknesses': ['low damage', 'slow kills'],
    },
    frozenset(['PRO', 'POT']): {
        'archetype': 'rush',
        'description': 'Animal rush (Protean + Potence)',
        'strengths': ['aggravated damage', 'stealth rush'],
        'weaknesses': ['blood hunger', 'predictable'],
    },
    frozenset(['OBF', 'PRE']): {
        'archetype': 'stealth',
        'description': 'Stealth bleed (Obfuscate + Presence)',
        'strengths': ['hard to block', 'efficient bleeds'],
        'weaknesses': ['weak in combat', 'vulnerable to intercept'],
    },
    frozenset(['DOM', 'OBF']): {
        'archetype': 'bleed',
        'description': 'Stealth bleed (Dominate + Obfuscate)',
        'strengths': ['fast bleeds', 'hard to block'],
        'weaknesses': ['no combat', 'vulnerable to bounce'],
    },
    frozenset(['TEM', 'FOR']): {
        'archetype': 'toolbox',
        'description': 'Thaumaturgy toolbox (Thaumaturgy + Fortitude)',
        'strengths': ['versatile', 'pool manipulation'],
        'weaknesses': ['slow', 'complex decisions'],
    },
    frozenset(['CEL', 'DAI']): {
        'archetype': 'combat',
        'description': 'Infernal combat (Celerity + Daimoinon)',
        'strengths': ['aggravated', 'fear'],
        'weaknesses': ['infernal penalty', 'table talk'],
    },
}


@dataclass
class DisciplineProfile:
    """Profile of a player's discipline capabilities."""
    disciplines: list[str] = field(default_factory=list)
    superior_disciplines: list[str] = field(default_factory=list)
    inferior_disciplines: list[str] = field(default_factory=list)
    
    # Archetype tendency
    primary_archetype: str = 'toolbox'
    secondary_archetype: str = 'bleed'
    
    # Strengths and weaknesses
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    
    # Combat capability
    has_combat: bool = False
    has_stealth: bool = False
    has_burst: bool = False
    
    @property
    def discipline_set(self) -> frozenset:
        return frozenset(self.disciplines)
    
    @property
    def is_aggressive(self) -> bool:
        return self.primary_archetype in ('rush', 'combat', 'bleed')
    
    @property
    def is_defensive(self) -> bool:
        return self.primary_archetype in ('toolbox', 'bloat')
    
    @property
    def combat_rating(self) -> float:
        """Rate combat capability (0-10)."""
        combat_discs = {'CEL', 'FOR', 'PRO', 'POT', 'DAI', 'Qui', 'Chim'}
        count = len(set(self.disciplines) & combat_discs)
        return min(10.0, count * 2.5)


class DisciplineAnalyzer:
    """Analyzes discipline combinations and learns patterns."""
    
    def __init__(self):
        # Learned patterns
        self.patterns: dict[frozenset, dict] = {}
        
        # Game outcomes by discipline combination
        self.outcomes: dict[frozenset, list[dict]] = {}
        
        # Discipline effectiveness tracking
        self.effectiveness: dict[str, dict] = {}
    
    def analyze_disciplines(self, disciplines: list[str]) -> DisciplineProfile:
        """Analyze a set of disciplines and create a profile."""
        profile = DisciplineProfile()
        profile.disciplines = list(set(disciplines))
        
        # Check for known combinations
        disc_set = frozenset(disciplines)
        
        # Find matching combo
        for combo, info in DISCIPLINE_COMBOS.items():
            if combo.issubset(disc_set):
                profile.primary_archetype = info['archetype']
                profile.strengths.extend(info['strengths'])
                profile.weaknesses.extend(info['weaknesses'])
                break
        
        # If no combo found, use individual discipline tendencies
        if profile.primary_archetype == 'toolbox':
            archetype_counts: dict[str, int] = {}
            for disc in disciplines:
                archetypes = DISCIPLINE_ARCHETYPES.get(disc, ['toolbox'])
                for arch in archetypes:
                    archetype_counts[arch] = archetype_counts.get(arch, 0) + 1
            
            if archetype_counts:
                sorted_archs = sorted(archetype_counts.items(), key=lambda x: -x[1])
                profile.primary_archetype = sorted_archs[0][0]
                if len(sorted_archs) > 1:
                    profile.secondary_archetype = sorted_archs[1][0]
        
        # Determine capabilities
        combat_discs = {'CEL', 'FOR', 'PRO', 'POT', 'DAI', 'Qui', 'Chim'}
        stealth_discs = {'OBF', 'Serp', 'Obl'}
        
        profile.has_combat = bool(set(disciplines) & combat_discs)
        profile.has_stealth = bool(set(disciplines) & stealth_discs)
        profile.has_burst = 'CEL' in disciplines and 'POT' in disciplines
        
        # Add generic strengths/weaknesses
        if profile.has_combat:
            profile.strengths.append('can fight in combat')
        if profile.has_stealth:
            profile.strengths.append('can play stealth cards')
        if not profile.has_combat:
            profile.weaknesses.append('vulnerable to rush')
        if not profile.has_stealth:
            profile.weaknesses.append('actions can be blocked')
        
        return profile
    
    def record_game_outcome(
        self,
        disciplines: list[str],
        outcome: str,  # 'win', 'loss', 'draw'
        position: int,  # 1-4
        vp: int,  # victory points
    ) -> None:
        """Record game outcome for a discipline combination."""
        disc_set = frozenset(disciplines)
        
        if disc_set not in self.outcomes:
            self.outcomes[disc_set] = []
        
        self.outcomes[disc_set].append({
            'outcome': outcome,
            'position': position,
            'vp': vp,
        })
    
    def get_effectiveness(self, disciplines: list[str]) -> dict:
        """Get effectiveness stats for a discipline combination."""
        disc_set = frozenset(disciplines)
        
        if disc_set not in self.outcomes:
            return {
                'games': 0,
                'wins': 0,
                'win_rate': 0.0,
                'avg_vp': 0.0,
            }
        
        outcomes = self.outcomes[disc_set]
        games = len(outcomes)
        wins = sum(1 for o in outcomes if o['outcome'] == 'win')
        total_vp = sum(o['vp'] for o in outcomes)
        
        return {
            'games': games,
            'wins': wins,
            'win_rate': wins / games if games > 0 else 0.0,
            'avg_vp': total_vp / games if games > 0 else 0.0,
        }
    
    def get_counter_strategy(self, disciplines: list[str]) -> str:
        """Get counter strategy against a discipline combination."""
        profile = self.analyze_disciplines(disciplines)
        
        # Counter based on archetype
        counters = {
            'bleed': 'rush',      # Rush to kill bleeders
            'rush': 'combat',     # Combat to counter rush
            'combat': 'bleed',    # Bleed to bypass combat
            'vote': 'stealth',    # Stealth to avoid votes
            'stealth': 'bleed',   # Bleed to oust quickly
            'toolbox': 'bleed',   # Bleed to pressure
            'bloat': 'bleed',     # Bleed to pressure
            'infernal': 'rush',   # Rush to kill infernal
        }
        
        return counters.get(profile.primary_archetype, 'bleed')
    
    def get_discipline_synergy(self, disc1: str, disc2: str) -> float:
        """Calculate synergy between two disciplines (0-1)."""
        combo = frozenset([disc1, disc2])
        
        if combo in DISCIPLINE_COMBOS:
            return 0.9  # Known strong combo
        
        # Check if both have same archetype tendency
        arch1 = set(DISCIPLINE_ARCHETYPES.get(disc1, []))
        arch2 = set(DISCIPLINE_ARCHETYPES.get(disc2, []))
        
        common = arch1 & arch2
        if common:
            return 0.6  # Moderate synergy
        
        return 0.3  # Low synergy
    
    def suggest_disciplines(self, desired_archetype: str) -> list[str]:
        """Suggest disciplines for a desired archetype."""
        suggestions: dict[str, list[str]] = {
            'bleed': ['DOM', 'OBF', 'PRE'],
            'rush': ['CEL', 'POT', 'PRO'],
            'combat': ['CEL', 'FOR', 'POT'],
            'vote': ['DOM', 'PRE', 'TEM'],
            'stealth': ['OBF', 'Serp', 'Obl'],
            'toolbox': ['AUS', 'TEM', 'FOR'],
            'bloat': ['PRE', 'Nec', 'Val'],
        }
        
        return suggestions.get(desired_archetype, ['AUS', 'DOM'])
    
    def save_learning(self) -> dict:
        """Save learned patterns."""
        return {
            'outcomes': {
                str(k): v for k, v in self.outcomes.items()
            },
        }
    
    def load_learning(self, data: dict) -> None:
        """Load learned patterns."""
        for k_str, v in data.get('outcomes', {}).items():
            try:
                k = frozenset(eval(k_str))
                self.outcomes[k] = v
            except Exception:
                continue
