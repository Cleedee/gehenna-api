#!/usr/bin/env python3
"""
Deck manager — add/remove/list cards in deck JSON files.

Usage:
    python scripts/manage_decks.py list                         # list all decks
    python scripts/manage_decks.py show 241                     # show deck contents
    python scripts/manage_decks.py add 241 100601 --qty 3       # add Earth Meld x3
    python scripts/manage_decks.py add 241 "Earth Meld" --qty 2 # add by name
    python scripts/manage_decks.py remove 241 100601            # remove Earth Meld
    python scripts/manage_decks.py search "meld"                # search for cards
    python scripts/manage_decks.py from-db 241                  # rebuild deck JSON from DB
"""

import argparse
import json
import os
import sys
import glob

DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'gehenna_api', 'data', 'decks')
CARD_LIB_DIR = os.path.join(os.path.dirname(__file__), '..', 'gehenna_api', 'data', 'cards', 'library')
CARD_CRYPT_DIR = os.path.join(os.path.dirname(__file__), '..', 'gehenna_api', 'data', 'cards', 'crypt')

# Ensure cwd is project root
os.chdir(os.path.join(os.path.dirname(__file__), '..'))


def _load_deck_json(deck_id: int) -> dict:
    path = os.path.join(DECK_DIR, f'{deck_id}.json')
    if not os.path.exists(path):
        print(f'❌ Deck #{deck_id} not found at {path}')
        sys.exit(1)
    return json.load(open(path, 'r', encoding='utf-8'))


def _save_deck_json(deck_id: int, data: dict):
    path = os.path.join(DECK_DIR, f'{deck_id}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f'  ✅  Saved {path}')


def _resolve_card_path(codevdb: int) -> str | None:
    """Find the card JSON file for a given codevdb."""
    # Try library first
    path_lib = os.path.join(CARD_LIB_DIR, f'{codevdb}.json')
    if os.path.exists(path_lib):
        return path_lib
    path_crypt = os.path.join(CARD_CRYPT_DIR, f'{codevdb}.json')
    if os.path.exists(path_crypt):
        return path_crypt
    return None


def _find_card_by_name(name: str) -> list[dict]:
    """Search for cards by name across library and crypt directories."""
    results = []
    for card_dir in [CARD_LIB_DIR, CARD_CRYPT_DIR]:
        for path in glob.glob(os.path.join(card_dir, '*.json')):
            try:
                card = json.load(open(path, 'r', encoding='utf-8'))
                if name.lower() in card.get('name', '').lower():
                    results.append(card)
            except (json.JSONDecodeError, OSError):
                continue
    return results


def cmd_list(args):
    """List all decks."""
    print(f'\n{"ID":>5}  {"Name":50} {"Cards":>5}  {"Creator"}')
    print(f'{"─"*5}  {"─"*50} {"─"*5}  {"─"*20}')
    for path in sorted(glob.glob(os.path.join(DECK_DIR, '*.json'))):
        deck = json.load(open(path, 'r', encoding='utf-8'))
        print(f'{deck["deck_id"]:>5}  {deck["name"]:50} {len(deck["cards"]):>5}  {deck.get("creator","?")}')
    print()


def cmd_show(args):
    """Show deck contents."""
    deck = _load_deck_json(args.deck_id)
    print(f'\n{"#"*60}')
    print(f'  #{deck["deck_id"]} — {deck["name"]}')
    print(f'  by {deck.get("creator","?")}  ({deck.get("date","?")})')
    print(f'  Format: {deck.get("format","?")}')
    print(f'{"#"*60}\n')

    crypt = [c for c in deck['cards'] if c['tipo'] in ('Vampire', 'Imbued')]
    library = [c for c in deck['cards'] if c['tipo'] not in ('Vampire', 'Imbued')]

    if crypt:
        print(f'=== Crypt ({len(crypt)} cards) ===')
        for c in crypt:
            status = '⚠' if c.get('needs_review') else ' '
            print(f'  {status} {c["name"]:35} x{c["quantity"]}')

    if library:
        print(f'\n=== Library ({len(library)} cards) ===')
        total = 0
        for c in library:
            status = '⚠' if c.get('needs_review') else ' '
            print(f'  {status} {c["name"]:35} [{c["tipo"]:20}] x{c["quantity"]}')
            total += c['quantity']
        print(f'  {"─"*60}')
        print(f'  Total library: {total} cards')

    print(f'\n  Description: {deck.get("description","")[:200]}')
    print()


_TIPO_MAP = {
    # JSON tipo (lowercase_underscore) → deck display tipo (Title Case with spaces)
    'action': 'Action',
    'action_modifier': 'Action Modifier',
    'action_modifier/combat': 'Action Modifier/Combat',
    'action_modifier/reaction': 'Action Modifier/Reaction',
    'ally': 'Ally',
    'combat': 'Combat',
    'combo': 'Combo',
    'equipment': 'Equipment',
    'event': 'Event',
    'master': 'Master',
    'political_action': 'Political Action',
    'reaction': 'Reaction',
    'reaction/action_modifier': 'Reaction/Action Modifier',
    'retainer': 'Retainer',
    'vampire': 'Vampire',
}


def _normalize_tipo(json_tipo: str) -> str:
    """Convert JSON tipo (e.g. 'action_modifier') to deck display tipo (e.g. 'Action Modifier')."""
    key = json_tipo.strip().lower()
    return _TIPO_MAP.get(key, json_tipo.title())


def cmd_add(args):
    """Add a card to a deck."""
    deck = _load_deck_json(args.deck_id)

    # Find the card
    if args.card.isdigit():
        codevdb = int(args.card)
        card_path = _resolve_card_path(codevdb)
        if not card_path:
            print(f'❌ Card with codevdb={codevdb} not found in card files')
            sys.exit(1)
        card_data = json.load(open(card_path, 'r', encoding='utf-8'))
        card_name = card_data['name']
    else:
        # Search by name
        results = _find_card_by_name(args.card)
        if not results:
            print(f'❌ No cards found matching "{args.card}"')
            sys.exit(1)
        if len(results) > 1:
            print(f'Found {len(results)} matches:')
            for r in results:
                print(f'  {r["codevdb"]:>6}  {r["name"]}')
            print(f'\nUse codevdb number instead of name')
            sys.exit(1)
        card_data = results[0]
        codevdb = card_data['codevdb']
        card_name = card_data['name']

    # Verify it's not a vampire for library or vice versa
    is_vampire = card_data.get('tipo', '').lower().startswith('vampire')

    # Check if card already in deck
    for existing in deck['cards']:
        if existing['codevdb'] == codevdb:
            existing['quantity'] += args.qty
            print(f'  ➕ {card_name} x{args.qty} (now {existing["quantity"]} total)')
            _save_deck_json(args.deck_id, deck)
            return

    # Display tipo for deck entry
    tipo_display = _normalize_tipo(card_data.get('tipo', 'Library'))

    # Determine card_path
    if is_vampire:
        card_path = os.path.join('gehenna_api', 'data', 'cards', 'crypt', f'{codevdb}.json')
    else:
        card_path = os.path.join('gehenna_api', 'data', 'cards', 'library', f'{codevdb}.json')

    # Add new card entry
    new_entry = {
        'codevdb': codevdb,
        'name': card_name,
        'tipo': tipo_display,
        'quantity': args.qty,
        'needs_review': False,
        'notes': '',
        'card_path': card_path,
    }
    deck['cards'].append(new_entry)
    print(f'  ➕ {card_name} x{args.qty} (new card)')
    _save_deck_json(args.deck_id, deck)


def cmd_remove(args):
    """Remove a card from a deck."""
    deck = _load_deck_json(args.deck_id)

    if args.card.isdigit():
        codevdb = int(args.card)
        matching = [c for c in deck['cards'] if c['codevdb'] == codevdb]
    else:
        matching = [c for c in deck['cards'] if args.card.lower() in c['name'].lower()]

    if not matching:
        print(f'❌ No cards found matching "{args.card}"')
        sys.exit(1)

    for card in matching:
        if args.qty and card['quantity'] > args.qty:
            card['quantity'] -= args.qty
            print(f'  ➖ {card["name"]} x{args.qty} (now {card["quantity"]} remaining)')
        else:
            deck['cards'].remove(card)
            print(f'  ✖  {card["name"]} removed entirely')

    _save_deck_json(args.deck_id, deck)


def cmd_search(args):
    """Search for cards in the card files."""
    results = []
    for card_dir in [CARD_LIB_DIR, CARD_CRYPT_DIR]:
        for path in glob.glob(os.path.join(card_dir, '*.json')):
            try:
                card = json.load(open(path, 'r', encoding='utf-8'))
                name = card.get('name', '')
                if args.query.lower() in name.lower():
                    dir_type = 'crypt' if 'crypt' in card_dir else 'library'
                    tipo = _normalize_tipo(card.get('tipo', '?'))
                    results.append((card['codevdb'], name, tipo, dir_type))
            except (json.JSONDecodeError, OSError):
                continue

    results.sort(key=lambda r: r[0])
    print(f'\nFound {len(results)} cards matching "{args.query}":')
    print(f'  {"Codevdb":>8}  {"Name":40}  {"Type":20}  {"Dir"}')
    print(f'  {"─"*8}  {"─"*40}  {"─"*20}  {"─"}')
    for codevdb, name, tipo, dir_type in results:
        print(f'  {codevdb:>8}  {name:40}  {tipo:20}  {dir_type}')
    print()


def cmd_from_db(args):
    """Rebuild deck JSON from the database (one-time conversion)."""
    print(f'  Rebuilding deck #{args.deck_id} from database...')

    # Ensure project modules are importable
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    try:
        from gehenna_api.models.deck import Deck as DeckModel
        from gehenna_api.models.slot import Slot
    except ImportError:
        print('❌ Could not import database models. Run from project root with PYTHONPATH set.')
        sys.exit(1)

    from sqlalchemy import select

    try:
        from gehenna_api.database import get_session
        session = next(get_session())
    except Exception:
        # Fallback: try sync session
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from gehenna_api.settings import Settings
        settings = Settings()
        engine = create_engine(settings.database_url)
        session = Session(engine)

    deck = session.scalar(select(DeckModel).where(DeckModel.id == args.deck_id))
    if not deck:
        print(f'❌ Deck #{args.deck_id} not found in database')
        sys.exit(1)

    slots = session.scalars(select(Slot).where(Slot.deck_id == args.deck_id)).all()

    cards = []
    for slot in slots:
        card = slot.card
        codevdb = card.codevdb or 0
        is_vampire = card.tipo.strip().lower().startswith('vampire') or card.tipo == 'Imbued'

        if is_vampire:
            card_path = f'gehenna_api/data/cards/crypt/{codevdb}.json'
        else:
            card_path = f'gehenna_api/data/cards/library/{codevdb}.json'

        entry = {
            'codevdb': codevdb,
            'name': card.name,
            'tipo': card.tipo,
            'quantity': slot.quantity,
            'needs_review': False,
            'notes': '',
            'card_path': card_path,
        }
        cards.append(entry)

    deck_data = {
        'deck_id': deck.id,
        'name': deck.name or '',
        'creator': deck.author or '',
        'date': deck.created_at.strftime('%Y-%m-%d') if deck.created_at else '',
        'format': deck.format or '',
        'description': deck.description or '',
        'all_reviewed': False,
        'cards': cards,
    }

    _save_deck_json(args.deck_id, deck_data)
    print(f'  ✅  {len(cards)} cards exported from DB')


def main():
    parser = argparse.ArgumentParser(
        description='Manage deck JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest='command')

    # list
    p = sub.add_parser('list', help='List all decks')

    # show
    p = sub.add_parser('show', help='Show deck contents')
    p.add_argument('deck_id', type=int)

    # add
    p = sub.add_parser('add', help='Add card to deck')
    p.add_argument('deck_id', type=int)
    p.add_argument('card', help='codevdb number or card name to search')
    p.add_argument('--qty', '-q', type=int, default=1)

    # remove
    p = sub.add_parser('remove', help='Remove card from deck')
    p.add_argument('deck_id', type=int)
    p.add_argument('card', help='codevdb number or card name')
    p.add_argument('--qty', '-q', type=int, default=0,
                   help='Quantity to remove (0 = remove all)')

    # search
    p = sub.add_parser('search', help='Search cards in card files')
    p.add_argument('query', help='Search term')

    # from-db
    p = sub.add_parser('from-db', help='Rebuild deck JSON from database')
    p.add_argument('deck_id', type=int)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    command_map = {
        'list': cmd_list,
        'show': cmd_show,
        'add': cmd_add,
        'remove': cmd_remove,
        'search': cmd_search,
        'from-db': cmd_from_db,
    }
    command_map[args.command](args)


if __name__ == '__main__':
    main()
