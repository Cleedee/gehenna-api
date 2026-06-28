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


def _get_db_session():
    """Get a database session, with fallback."""
    try:
        from gehenna_api.database import get_session
        return next(get_session())
    except Exception:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from gehenna_api.settings import Settings
        settings = Settings()
        engine = create_engine(settings.database_url)
        return Session(engine)


def _ensure_card_json(card, session=None) -> str:
    """
    Ensure the card's JSON file exists. If missing, generate it from DB data.
    Returns the relative card_path.
    """
    codevdb = card.codevdb or 0
    is_vampire = card.tipo.strip().lower().startswith('vampire') or card.tipo == 'Imbued'

    if is_vampire:
        card_dir = os.path.join(os.path.dirname(__file__), '..', 'gehenna_api', 'data', 'cards', 'crypt')
        card_path = f'gehenna_api/data/cards/crypt/{codevdb}.json'
    else:
        card_dir = os.path.join(os.path.dirname(__file__), '..', 'gehenna_api', 'data', 'cards', 'library')
        card_path = f'gehenna_api/data/cards/library/{codevdb}.json'

    abs_path = os.path.join(os.path.dirname(__file__), '..', card_path)
    if os.path.exists(abs_path):
        return card_path  # already exists

    # Generate card JSON from DB data
    os.makedirs(card_dir, exist_ok=True)

    # Try to parse modifiers from card text
    modifiers = {}
    bleed_val = 0
    stealth_val = 0
    intercept_val = 0
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from gehenna_api.engine.cardtext import parse_card_text
        parsed = parse_card_text(
            name=card.name or '',
            tipo=card.tipo or '',
            text=card.text or '',
            disciplines=card.disciplines or '',
        )
        modifiers = dict(parsed.modifiers)
        bleed_val = modifiers.get('bleed', 0)
        stealth_val = modifiers.get('stealth', 0)
        intercept_val = modifiers.get('intercept', 0)
    except Exception:
        pass

    if bleed_val:
        modifiers['bleed'] = bleed_val
    if stealth_val:
        modifiers['stealth'] = stealth_val
    if intercept_val:
        modifiers['intercept'] = intercept_val

    card_json = {
        'codevdb': codevdb,
        'name': card.name or '',
        'tipo': card.tipo or '',
        'source': 'DB export',
        'abilities': [],
        'modifiers': modifiers,
        'default_strike': None,
        'needs_review': True,
        'notes': 'Auto-generated from DB — check abilities/modifiers',
    }

    with open(abs_path, 'w', encoding='utf-8') as f:
        json.dump(card_json, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f'    📝  Generated card JSON: {card_path}')
    return card_path


def cmd_list_db(args):
    """List all decks in the database."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from gehenna_api.models.deck import Deck as DeckModel
    from gehenna_api.models.slot import Slot
    from sqlalchemy import select, func

    session = _get_db_session()
    decks = session.scalars(select(DeckModel).order_by(DeckModel.id)).all()

    print(f'\n{"ID":>5}  {"Name":50} {"Cards":>5}  {"Author":20}  {"Exists"}')
    print(f'{"─"*5}  {"─"*50} {"─"*5}  {"─"*20}  {"─"*6}')

    for deck in decks:
        # Count slots (total quantity of cards in deck)
        slots = session.scalars(
            select(Slot).where(Slot.deck_id == deck.id)
        ).all()
        total_cards = sum(s.quantity for s in slots) if slots else 0

        deck_path = os.path.join(DECK_DIR, f'{deck.id}.json')
        exists = '✅' if os.path.exists(deck_path) else '—'

        print(f'{deck.id:>5}  {deck.name or "(no name)":50} {total_cards:>5}  '
              f'{deck.creator or "?":20}  {exists}')

    session.close()
    print()


def cmd_from_db(args):
    """Export (or re-export) a deck from database to deck JSON + card JSONs."""
    print(f'  Exporting deck #{args.deck_id} from database...')

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    try:
        from gehenna_api.models.deck import Deck as DeckModel
        from gehenna_api.models.slot import Slot
    except ImportError:
        print('❌ Could not import database models. Run from project root with PYTHONPATH set.')
        sys.exit(1)

    from sqlalchemy import select

    session = _get_db_session()

    deck = session.scalar(select(DeckModel).where(DeckModel.id == args.deck_id))
    if not deck:
        print(f'❌ Deck #{args.deck_id} not found in database')
        session.close()
        sys.exit(1)

    slots = session.scalars(select(Slot).where(Slot.deck_id == args.deck_id)).all()

    if not slots:
        print(f'⚠️  Deck #{args.deck_id} has no cards (slots)')

    cards = []
    missing_card_jsons = 0
    for slot in slots:
        card = slot.card
        codevdb = card.codevdb or 0

        # Generate card JSON if missing
        card_path = _ensure_card_json(card, session)

        # Check if card JSON exists after ensuring
        abs_card_path = os.path.join(os.path.dirname(__file__), '..', card_path)
        if not os.path.exists(abs_card_path):
            missing_card_jsons += 1

        entry = {
            'codevdb': codevdb,
            'name': card.name,
            'tipo': _normalize_tipo(card.tipo),
            'quantity': slot.quantity,
            'needs_review': False,
            'notes': '',
            'card_path': card_path,
        }
        cards.append(entry)

    deck_data = {
        'deck_id': deck.id,
        'name': deck.name or '',
        'creator': deck.creator or '',
        'date': deck.created.strftime('%Y-%m-%d') if deck.created else '',
        'format': deck.tipo or '',
        'description': deck.description or '',
        'all_reviewed': False,
        'cards': cards,
    }

    path = os.path.join(DECK_DIR, f'{args.deck_id}.json')
    if os.path.exists(path):
        print(f'  ⚠️  Overwriting existing {path}')

    _save_deck_json(args.deck_id, deck_data)

    notes = []
    if missing_card_jsons:
        notes.append(f'{missing_card_jsons} cards with missing JSON files')
    if any(c.get('needs_review') for c in cards):
        notes.append('some cards need review')

    print(f'  ✅  Exported {len(cards)} cards to {path}')
    if notes:
        print(f'  ℹ️  {", ".join(notes)}. Run validate_cards.py to check.')

    session.close()


def main():
    parser = argparse.ArgumentParser(
        description='Manage deck JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest='command')

    # list
    p = sub.add_parser('list', help='List all decks from JSON files')
    p = sub.add_parser('list-db', help='List all decks from database')

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
        'list-db': cmd_list_db,
        'show': cmd_show,
        'add': cmd_add,
        'remove': cmd_remove,
        'search': cmd_search,
        'from-db': cmd_from_db,
    }
    command_map[args.command](args)


if __name__ == '__main__':
    main()
