"""Archetype recognizer for V:TES opponents.

Identifies opponent archetypes based on:
- Clans
- Disciplines
- Observed cards
- Play patterns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Clan → Archetype mapping
CLAN_ARCHETYPES: dict[str, list[str]] = {
    'Tremere': ['combat', 'toolbox'],
    'Toreador': ['bleed', 'vote'],
    'Ventrue': ['vote', 'bleed'],
    'Malkavian': ['bleed', 'stealth'],
    'Nosferatu': ['combat', 'rush'],
    'Gangrel': ['rush', 'combat'],
    'Brujah': ['rush', 'combat'],
    'Lasombra': ['bleed', 'vote'],
    'Tzimisce': ['toolbox', 'combat'],
    'Baali': ['infernal', 'combat'],
    'Assamite': ['stealth', 'bleed'],
    'Followers of Set': ['bleed', 'vote'],
    'Harbingers of Skulls': ['bleed', 'stealth'],
    'Ishtarri': ['vote', 'bloat'],
    'Samedi': ['bleed', 'stealth'],
    'Daughters of Cacophony': ['vote', 'bloat'],
    'Gargoyle': ['combat', 'rush'],
    'Kiasyd': ['stealth', 'bleed'],
    'Malkavian Antitribu': ['bleed', 'stealth'],
    'Nosferatu Antitribu': ['combat', 'rush'],
    'Toreador Antitribu': ['bleed', 'vote'],
    'Tremere Antitribu': ['combat', 'toolbox'],
    'Ventrue Antitribu': ['vote', 'bleed'],
    'Abomination': ['combat', 'rush'],
    ' Caitiff': ['toolbox'],
    'Giovanni': ['vote', 'bloat'],
    'Ravnos': ['toolbox', 'combat'],
    'Salubri': ['toolbox', 'bloat'],
    'Gangrel Antitribu': ['rush', 'combat'],
    'Brujah Antitribu': ['rush', 'combat'],
    'Lasombra Antitribu': ['bleed', 'vote'],
    'Tzimisce Antitribu': ['toolbox', 'combat'],
}

# Discipline → Archetype mapping
DISCIPLINE_ARCHETYPES: dict[str, list[str]] = {
    'DOM': ['bleed', 'vote'],        # Dominate: bleed/vote
    'OBF': ['stealth', 'bleed'],     # Obfuscate: stealth/bleed
    'PRE': ['vote', 'bleed'],        # Presence: vote/bleed
    'CEL': ['combat', 'rush'],       # Celerity: combat
    'FOR': ['combat', 'rush'],       # Fortitude: combat
    'PRO': ['combat', 'rush'],       # Protean: combat
    'DEM': ['bleed', 'vote'],        # Demence: bleed
    'TEM': ['combat', 'rush'],       # Temporis: combat
    'QUI': ['combat', 'rush'],       # Quietus: combat
    'THA': ['combat', 'toolbox'],    # Thaumaturgy: toolbox
    'AUS': ['toolbox', 'bleed'],     # Auspex: toolbox
    'CHI': ['combat', 'rush'],       # Chimerstry: combat
    'DAM': ['vote', 'bloat'],        # Dementation: vote
    'DOM': ['bleed', 'vote'],        # Dominate: bleed/vote
    'FIB': ['combat', 'rush'],       # Fibers: combat
    'MYT': ['toolbox', 'combat'],    # Mytherceria: toolbox
    'Nec': ['vote', 'bloat'],        # Necromancy: vote
    'OBL': ['bleed', 'stealth'],     # Obtenebration: bleed
    'PIE': ['combat', 'rush'],       # Potence: combat
    'POT': ['combat', 'rush'],       # Potence: combat
    'PRE': ['vote', 'bleed'],        # Presence: vote/bleed
    'PRO': ['combat', 'rush'],       # Protean: combat
    'QUI': ['combat', 'rush'],       # Quietus: combat
    'SER': ['stealth', 'bleed'],     # Serpentis: stealth
    'SPI': ['toolbox', 'combat'],    # Spiritus: toolbox
    'TEM': ['combat', 'rush'],       # Temporis: combat
    'THA': ['toolbox', 'combat'],    # Thaumaturgy: toolbox
    'VAL': ['vote', 'bleed'],        # Valeren: vote
    'VEN': ['toolbox', 'combat'],    # Visceratika: toolbox
    'VIS': ['toolbox', 'combat'],    # Visceratika: toolbox
}

# Card names → Archetype mapping
CARD_ARCHETYPES: dict[str, list[str]] = {
    'govern the all': ['bleed', 'vote'],
    'govern the': ['bleed', 'vote'],
    'misdirection': ['bleed'],
    'bonding': ['bleed'],
    'rapid': ['bleed'],
    'intimidation': ['bleed'],
    'scouting': ['rush'],
    'hellhound': ['rush'],
    'war ghouls': ['rush'],
    'war': ['rush'],
    'canine horde': ['rush'],
    'sengir': ['rush'],
    'trench': ['rush'],
    'bowl of pomegranate': ['rush'],
    'lionheart': ['rush'],
    'coven': ['vote'],
    'parliaments of': ['vote'],
    'kine': ['vote'],
    'anchorage': ['vote'],
    'consortium': ['vote'],
    'alastor': ['combat'],
    'shield of': ['combat'],
    'armor of': ['combat'],
    'death of': ['combat'],
    'flames': ['combat'],
    'torn sign of': ['combat'],
    'claws': ['combat'],
    'murder of crows': ['toolbox'],
    'earth meld': ['toolbox'],
    'raven': ['toolbox'],
    'shroud': ['toolbox'],
    'veil': ['toolbox'],
    'unholy': ['toolbox'],
}

# Full archetype list
ARCHETYPES = [
    'bleed',      # Direct pool damage
    'rush',       # Aggressive combat
    'combat',     # Defensive/redirect combat
    'vote',       # Political actions
    'stealth',    # Stealth-based actions
    'toolbox',    # Versatile/reactive
    'bloat',      # Pool gain
    'infernal',   # Infernal/corruption
]


@dataclass
class ArchetypeEvidence:
    """Evidence for an archetype."""
    archetype: str
    score: float
    source: str  # 'clan', 'discipline', 'card', 'behavior'


@dataclass
class ArchetypeProfile:
    """Profile of a player's archetype."""
    primary: str
    secondary: str
    confidence: float
    evidence: list[ArchetypeEvidence] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.primary}/{self.secondary} ({self.confidence:.0%})"


class ArchetypeRecognizer:
    """Recognizes opponent archetypes based on available information."""
    
    def __init__(self):
        # Observed information per player
        self.observed_clans: dict[int, list[str]] = {}
        self.observed_disciplines: dict[int, list[str]] = {}
        self.observed_cards: dict[int, list[str]] = {}
        self.observed_actions: dict[int, list[str]] = {}
        
        # Final profiles
        self.profiles: dict[int, ArchetypeProfile] = {}
    
    def observe_clan(self, player_id: int, clan: str) -> None:
        """Record observed clan for a player."""
        if player_id not in self.observed_clans:
            self.observed_clans[player_id] = []
        if clan not in self.observed_clans[player_id]:
            self.observed_clans[player_id].append(clan)
    
    def observe_discipline(self, player_id: int, discipline: str) -> None:
        """Record observed discipline for a player."""
        if player_id not in self.observed_disciplines:
            self.observed_disciplines[player_id] = []
        # Normalize discipline (remove superior/inferior markers)
        disc = discipline.upper().replace('|', '').strip()
        if disc and disc not in self.observed_disciplines[player_id]:
            self.observed_disciplines[player_id].append(disc)
    
    def observe_card(self, player_id: int, card_name: str) -> None:
        """Record observed card for a player."""
        if player_id not in self.observed_cards:
            self.observed_cards[player_id] = []
        if card_name.lower() not in self.observed_cards[player_id]:
            self.observed_cards[player_id].append(card_name.lower())
    
    def observe_action(self, player_id: int, action_type: str) -> None:
        """Record observed action type for a player."""
        if player_id not in self.observed_actions:
            self.observed_actions[player_id] = []
        if action_type not in self.observed_actions[player_id]:
            self.observed_actions[player_id].append(action_type)
    
    def get_profile(self, player_id: int) -> ArchetypeProfile:
        """Get archetype profile for a player."""
        if player_id in self.profiles:
            return self.profiles[player_id]
        
        # Calculate scores for each archetype
        scores: dict[str, float] = {a: 0.0 for a in ARCHETYPES}
        evidence: dict[str, list[ArchetypeEvidence]] = {a: [] for a in ARCHETYPES}
        
        # 1. Clan evidence
        for clan in self.observed_clans.get(player_id, []):
            archetypes = CLAN_ARCHETYPES.get(clan, ['toolbox'])
            for arch in archetypes:
                scores[arch] += 0.3
                evidence[arch].append(ArchetypeEvidence(
                    archetype=arch,
                    score=0.3,
                    source=f'clan:{clan}',
                ))
        
        # 2. Discipline evidence
        for disc in self.observed_disciplines.get(player_id, []):
            archetypes = DISCIPLINE_ARCHETYPES.get(disc, ['toolbox'])
            for arch in archetypes:
                scores[arch] += 0.2
                evidence[arch].append(ArchetypeEvidence(
                    archetype=arch,
                    score=0.2,
                    source=f'discipline:{disc}',
                ))
        
        # 3. Card evidence
        for card_name in self.observed_cards.get(player_id, []):
            for card_pattern, archetypes in CARD_ARCHETYPES.items():
                if card_pattern in card_name:
                    for arch in archetypes:
                        scores[arch] += 0.4
                        evidence[arch].append(ArchetypeEvidence(
                            archetype=arch,
                            score=0.4,
                            source=f'card:{card_name}',
                        ))
        
        # 4. Action behavior evidence
        for action in self.observed_actions.get(player_id, []):
            if action == 'bleed':
                scores['bleed'] += 0.15
                evidence['bleed'].append(ArchetypeEvidence(
                    archetype='bleed',
                    score=0.15,
                    source='behavior:bleed_action',
                ))
            elif action == 'rush':
                scores['rush'] += 0.15
                scores['combat'] += 0.1
                evidence['rush'].append(ArchetypeEvidence(
                    archetype='rush',
                    score=0.15,
                    source='behavior:rush_action',
                ))
            elif action == 'vote':
                scores['vote'] += 0.15
                evidence['vote'].append(ArchetypeEvidence(
                    archetype='vote',
                    score=0.15,
                    source='behavior:vote_action',
                ))
            elif action == 'stealth':
                scores['stealth'] += 0.15
                evidence['stealth'].append(ArchetypeEvidence(
                    archetype='stealth',
                    score=0.15,
                    source='behavior:stealth_action',
                ))
            elif action == 'control':
                scores['toolbox'] += 0.1
                evidence['toolbox'].append(ArchetypeEvidence(
                    archetype='toolbox',
                    score=0.1,
                    source='behavior:control_action',
                ))
        
        # Find top 2 archetypes
        sorted_archetypes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_archetypes[0][1] == 0:
            # No evidence, default to toolbox
            profile = ArchetypeProfile(
                primary='toolbox',
                secondary='bleed',
                confidence=0.0,
                evidence=[],
            )
        else:
            total = sum(scores.values())
            profile = ArchetypeProfile(
                primary=sorted_archetypes[0][0],
                secondary=sorted_archetypes[1][0] if len(sorted_archetypes) > 1 else 'toolbox',
                confidence=sorted_archetypes[0][1] / total if total > 0 else 0.0,
                evidence=evidence[sorted_archetypes[0][0]],
            )
        
        self.profiles[player_id] = profile
        return profile
    
    def get_threat_adjustment(self, player_id: int) -> float:
        """Get threat adjustment based on archetype."""
        profile = self.get_profile(player_id)
        
        # Archetypes that are more threatening
        threat_multipliers = {
            'bleed': 1.3,      # Bleed is dangerous
            'rush': 1.2,       # Rush is aggressive
            'combat': 0.9,     # Combat is defensive
            'vote': 1.1,       # Vote is moderate
            'stealth': 1.0,    # Stealth is neutral
            'toolbox': 1.0,    # Toolbox is neutral
            'bloat': 0.8,      # Bloat is less threatening
            'infernal': 1.4,   # Infernal is very dangerous
        }
        
        return threat_multipliers.get(profile.primary, 1.0)
    
    def get_counter_strategy(self, player_id: int) -> str:
        """Get counter strategy against a player's archetype."""
        profile = self.get_profile(player_id)
        
        # Counter strategies
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
        
        return counters.get(profile.primary, 'bleed')
    
    def reset(self) -> None:
        """Reset all observed data."""
        self.observed_clans.clear()
        self.observed_disciplines.clear()
        self.observed_cards.clear()
        self.observed_actions.clear()
        self.profiles.clear()
