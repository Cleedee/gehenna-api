#!/usr/bin/env python3
"""Parse all cards from cardbase JSONs into individual card JSON files.

Usage:
    python scripts/parse_all_cards.py

Output: gehenna_api/data/cards/{crypt,library}/{codevdb}.json

Re-run safely: already-reviewed files (needs_review=false) are preserved.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gehenna_api.engine.cardtext.parser import parse_card_text  # noqa: E402

OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent / 'gehenna_api' / 'data' / 'cards'
)

TIPO_MAP = {
    'Vampire': 'vampire',
    'Master': 'master',
    'Action': 'action',
    'Action Modifier': 'action_modifier',
    'Political Action': 'political_action',
    'Combat': 'combat',
    'Reaction': 'reaction',
    'Equipment': 'equipment',
    'Ally': 'ally',
    'Retainer': 'retainer',
    'Event': 'event',
    'Imbued': 'imbued',
}


def _map_effect(effect) -> list[dict]:
    text = effect.effect
    condition = effect.condition

    table = {
        'equip_self': ('action.equip', {'attachment': 'self'}),
        'damage_aggravated': (
            'combat.set_damage_type',
            {'damage_type': 'aggravated'},
        ),
        'restrict_use': ('card.restrict_use', {}),
        'prevent_damage': ('combat.prevent_damage', {}),
        'unlock': ('action.unlock', {}),
    }

    if text in table:
        func, params = table[text]
        if condition:
            params = {**params, 'condition': condition}
        return [{'function': func, 'params': params, 'text': effect.text}]

    return [
        {
            'function': 'effect.raw',
            'params': {
                'effect': text,
                **({'condition': condition} if condition else {}),
            },
            'text': effect.text,
        }
    ]


def _map_strike(strike) -> list[dict]:
    results = []
    if strike.manoeuvres:
        results.append(
            {'function': 'combat.maneuver', 'params': {}, 'text': strike.text}
        )
    if strike.damage:
        results.append(
            {
                'function': 'combat.strike',
                'params': {
                    'damage': strike.damage,
                    'damage_type': strike.damage_type.value,
                },
                'text': strike.text,
            }
        )
    if strike.press:
        results.append(
            {'function': 'combat.press', 'params': {}, 'text': strike.text}
        )
    if strike.additional_strike:
        results.append(
            {
                'function': 'combat.additional_strike',
                'params': {},
                'text': strike.text,
            }
        )
    if strike.steal_blood:
        results.append(
            {
                'function': 'combat.steal_blood',
                'params': {'amount': strike.steal_blood},
                'text': strike.text,
            }
        )
    if strike.dodge:
        results.append(
            {
                'function': 'combat.dodge',
                'params': {},
                'text': strike.text,
            }
        )
    if strike.ends_combat:
        results.append(
            {
                'function': 'combat.end',
                'params': {},
                'text': strike.text,
            }
        )
    return results


def _map_modifiers(modifiers: dict) -> list[dict]:
    results = []
    for mtype, value in modifiers.items():
        results.append(
            {
                'function': f'modifier.{mtype.value}',
                'params': {'value': value},
                'text': f'{value:+d} {mtype.value}',
            }
        )
    return results


def _build_card_json(
    codevdb: str, name: str, tipo: str, text: str, source: str
) -> dict:
    parsed = parse_card_text(name, tipo, text)

    abilities_json = []
    for ab in parsed.abilities:
        effects_json = []
        effects_json.extend(_map_modifiers(ab.modifiers))
        for eff in ab.effects:
            effects_json.extend(_map_effect(eff))
        if ab.strike:
            effects_json.extend(_map_strike(ab.strike))
        abilities_json.append(
            {
                'disciplines': ab.disciplines,
                'context': ab.context,
                'effects': effects_json,
            }
        )

    modifiers_flat = (
        {k.value: v for k, v in parsed.modifiers.items()}
        if parsed.modifiers
        else {}
    )

    card_json = {
        'codevdb': int(codevdb),
        'name': name,
        'tipo': tipo,
        'source': source,
        'abilities': abilities_json,
        'modifiers': modifiers_flat,
        'default_strike': None,
        'needs_review': True,
        'notes': '',
    }

    if parsed.default_strike:
        card_json['default_strike'] = _map_strike(parsed.default_strike)

    return card_json


def _process_cards(
    input_path: str, output_subdir: str, source_name: str
) -> tuple[int, int]:
    with open(input_path) as f:
        cards = json.load(f)

    out_dir = OUTPUT_DIR / output_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for codevdb, data in cards.items():
        out_path = out_dir / f'{codevdb}.json'

        if out_path.exists():
            try:
                existing = json.loads(out_path.read_text())
                if not existing.get('needs_review', True):
                    skipped += 1
                    continue
            except (json.JSONDecodeError, KeyError):
                pass

        name = data.get('name', '')
        text = data.get('text', '')
        if output_subdir == 'crypt':
            tipo = 'vampire'
        else:
            vdb_type = data.get('type', '')
            tipo = TIPO_MAP.get(vdb_type, vdb_type.lower().replace(' ', '_'))

        card_json = _build_card_json(codevdb, name, tipo, text, source_name)
        out_path.write_text(
            json.dumps(card_json, indent=2, ensure_ascii=False) + '\n'
        )
        created += 1

    return created, skipped


def main() -> None:
    base = (
        Path(__file__).resolve().parent.parent / 'gehenna_api' / 'data'
    )

    print('Processing library cards...')
    lib_created, lib_skipped = _process_cards(
        str(base / 'cardbase_lib.json'), 'library', 'cardbase_lib.json'
    )
    print(f'  Library: {lib_created} created, {lib_skipped} skipped')

    print('Processing crypt cards...')
    crypt_created, crypt_skipped = _process_cards(
        str(base / 'cardbase_crypt.json'), 'crypt', 'cardbase_crypt.json'
    )
    print(f'  Crypt: {crypt_created} created, {crypt_skipped} skipped')

    total = lib_created + crypt_created
    skipped = lib_skipped + crypt_skipped
    print(f'\nDone: {total} created, {skipped} skipped (already reviewed)')


if __name__ == '__main__':
    main()
