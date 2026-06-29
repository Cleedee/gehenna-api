"""
Card loader — loads card data from JSON files with override support.

Architecture:
  - Each card has a JSON file in data/cards/{crypt,library}/<codevdb>.json
  - Overrides are stored in data/cards/overrides/{codevdb}.json
  - This module merges: JSON file data → override file → final CardData
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional

from gehenna_api.data.cards.overrides import load_override


DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CARDS_DIR = os.path.join(DATA_DIR, 'cards')
DECKS_DIR = os.path.join(DATA_DIR, 'decks')


@dataclass
class CardEffect:
    """A single effect within an ability."""
    function: str = ''
    params: dict = field(default_factory=dict)
    text: str = ''


@dataclass
class CardAbility:
    """An ability with discipline requirement, context, and effects."""
    disciplines: list[str] = field(default_factory=list)
    context: str = ''
    effects: list[CardEffect] = field(default_factory=list)


@dataclass
class StrikeData:
    """A strike definition (combat cards)."""
    function: str = ''
    params: dict = field(default_factory=dict)
    text: str = ''


@dataclass
class CardData:
    """Complete card data loaded from JSON + overrides."""
    codevdb: int = 0
    name: str = ''
    tipo: str = ''
    cost: str = ''
    text: str = ''
    abilities: list[CardAbility] = field(default_factory=list)
    modifiers: dict[str, int] = field(default_factory=dict)
    default_strike: list[StrikeData] = field(default_factory=list)
    disciplines: list[str] = field(default_factory=list)
    special_effects: list[str] = field(default_factory=list)
    is_unique: bool = False
    is_infernal: bool = False
    master_type: str | None = None
    effects: list = field(default_factory=list)
    needs_review: bool = False
    notes: str = ''


def _load_json(path: str) -> Optional[dict]:
    """Load and return a JSON file, or None if not found."""
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _is_vampire_type(tipo: str) -> bool:
    """Check if card type is a vampire (crypt card)."""
    if not tipo:
        return False
    tipo_lower = tipo.lower().strip()
    return tipo_lower in ('vampire', 'imbued') or 'vampire' in tipo_lower


# Non-unique vampires (can have multiple copies in play)
NON_UNIQUE_VAMPIRES = {
    'Horde, The',
    'Skeleton, The',
    'Shade, The',
    'Wraith, The',
    'Carrion Crow',
    'Rock Cat',
}


def _is_non_unique_vampire(name: str) -> bool:
    """Check if vampire is non-unique (can have multiple copies)."""
    if not name:
        return False
    return name in NON_UNIQUE_VAMPIRES or 'Horde' in name


def _is_infernal(text: str) -> bool:
    """Check if card has the Infernal trait."""
    if not text:
        return False
    return 'infernal' in text.lower()


def _parse_abilities(raw: list) -> list[CardAbility]:
    """Parse raw abilities array from JSON into CardAbility objects."""
    result = []
    for ab in raw or []:
        effects = []
        for eff in ab.get('effects', []):
            effects.append(CardEffect(
                function=eff.get('function', ''),
                params=eff.get('params', {}),
                text=eff.get('text', ''),
            ))
        result.append(CardAbility(
            disciplines=ab.get('disciplines', []),
            context=ab.get('context', ''),
            effects=effects,
        ))
    return result


def _parse_strikes(raw) -> list[StrikeData]:
    """Parse default_strike from JSON into StrikeData objects."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [StrikeData(
            function=s.get('function', ''),
            params=s.get('params', {}),
            text=s.get('text', ''),
        ) for s in raw]
    return []


def load_card(codevdb: int) -> Optional[CardData]:
    """Load a card by its codevdb ID from JSON file + manual overrides."""
    # Try library first, then crypt
    for subdir in ('library', 'crypt'):
        path = os.path.join(CARDS_DIR, subdir, f'{codevdb}.json')
        raw = _load_json(path)
        if raw is not None:
            break
    else:
        return None

    # Parse from JSON
    is_unique = raw.get('is_unique', False)
    
    # Vampires are unique by default (game rule: each crypt card is unique)
    # unless explicitly marked as non-unique (e.g., The Horde)
    tipo = raw.get('tipo', '')
    name = raw.get('name', '')
    if not is_unique and _is_vampire_type(tipo):
        # Check if this is a known non-unique vampire
        is_unique = not _is_non_unique_vampire(name)
    
    card = CardData(
        codevdb=raw.get('codevdb', codevdb),
        name=raw.get('name', ''),
        tipo=tipo,
        cost=raw.get('cost', ''),
        text=raw.get('text', ''),
        abilities=_parse_abilities(raw.get('abilities', [])),
        modifiers=dict(raw.get('modifiers', {})),
        default_strike=_parse_strikes(raw.get('default_strike')),
        disciplines=raw.get('disciplines', []),
        special_effects=list(raw.get('special_effects', [])),
        is_unique=is_unique,
        is_infernal=_is_infernal(raw.get('text', '')),
        master_type=raw.get('master_type', None),
        needs_review=raw.get('needs_review', False),
        notes=raw.get('notes', ''),
    )

    # Apply overrides from file (if any)
    override = load_override(codevdb)
    if override:
        if 'modifiers' in override:
            card.modifiers.update(override['modifiers'])
        if 'abilities' in override:
            card.abilities = _parse_abilities(override['abilities'])
        if 'default_strike' in override:
            card.default_strike = _parse_strikes(override['default_strike'])
        if 'tipo' in override:
            card.tipo = override['tipo']
        if 'disciplines' in override:
            card.disciplines = override['disciplines']
        if 'special_effects' in override:
            card.special_effects = override['special_effects']
        if 'master_type' in override:
            card.master_type = override['master_type']
        if 'effects' in override:
            card.effects = override['effects']
        if 'is_unique' in override:
            card.is_unique = override['is_unique']
        if 'is_infernal' in override:
            card.is_infernal = override['is_infernal']
        if 'text' in override:
            card.text = override['text']

    return card


def load_deck(deck_id: int) -> Optional[dict]:
    """Load a deck JSON file by deck_id."""
    path = os.path.join(DECKS_DIR, f'{deck_id}.json')
    raw = _load_json(path)
    if raw is None:
        return None
    return raw


def load_deck_cards(deck_id: int) -> list[tuple[CardData, int]]:
    """Load all cards for a deck. Returns list of (CardData, quantity)."""
    deck = load_deck(deck_id)
    if not deck:
        return []

    result = []
    for entry in deck.get('cards', []):
        codevdb = entry.get('codevdb')
        if not codevdb:
            continue
        card_data = load_card(codevdb)
        if card_data is None:
            continue
        result.append((card_data, entry.get('quantity', 1)))
    return result


def get_all_deck_ids() -> list[int]:
    """Return list of all deck IDs available."""
    import re
    ids = []
    if not os.path.isdir(DECKS_DIR):
        return ids
    for fname in sorted(os.listdir(DECKS_DIR)):
        m = re.match(r'(\d+)\.json$', fname)
        if m:
            ids.append(int(m.group(1)))
    return ids


def validate_card_data(codevdb: int) -> dict:
    """Validate card data completeness. Returns report dict."""
    card = load_card(codevdb)
    if card is None:
        return {'codevdb': codevdb, 'status': 'missing', 'issues': ['card file not found']}

    issues = []
    warnings = []

    if card.needs_review:
        warnings.append('needs_review flagged')

    if card.tipo in ('combat',) or any(
        'strike' in str(s).lower() for s in card.default_strike
    ):
        if not card.default_strike:
            warnings.append('combat card without default_strike')

    tipo_lower = card.tipo.lower()

    if tipo_lower in ('action', 'action modifier', 'political action', 'master',
                      'equipment', 'retainer', 'ally', 'reaction'):
        if not card.abilities and not card.modifiers:
            if tipo_lower not in ('master', 'equipment', 'event'):
                warnings.append(f'{tipo_lower} with no abilities or modifiers')

    if card.name == '':
        issues.append('empty name')

    return {
        'codevdb': codevdb,
        'name': card.name,
        'tipo': card.tipo,
        'status': 'ok' if not issues else 'issues',
        'issues': issues,
        'warnings': warnings,
        'abilities_count': len(card.abilities),
        'modifiers_count': len(card.modifiers),
        'has_default_strike': len(card.default_strike) > 0,
        'needs_review': card.needs_review,
    }


def validate_deck(deck_id: int) -> dict:
    """Validate all cards in a deck. Returns summary."""
    deck = load_deck(deck_id)
    if deck is None:
        return {'deck_id': deck_id, 'status': 'missing'}

    cards_data = load_deck_cards(deck_id)
    reports = []
    for card_data, qty in cards_data:
        report = validate_card_data(card_data.codevdb)
        report['quantity'] = qty
        reports.append(report)

    ok_count = sum(1 for r in reports if r['status'] == 'ok')
    issue_count = sum(1 for r in reports if r['status'] != 'ok')
    warning_count = sum(len(r.get('warnings', [])) for r in reports)

    return {
        'deck_id': deck_id,
        'name': deck.get('name', ''),
        'total_cards': len(reports),
        'ok': ok_count,
        'with_issues': issue_count,
        'total_warnings': warning_count,
        'cards': reports,
    }


def validate_all_decks() -> list[dict]:
    """Validate all available decks."""
    return [validate_deck(did) for did in get_all_deck_ids()]
