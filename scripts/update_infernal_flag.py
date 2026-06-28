#!/usr/bin/env python3
"""Update card JSON files with is_infernal flag based on card text.

Usage:
    python scripts/update_infernal_flag.py [--use-krcg]

This script reads each card's text and sets is_infernal=true if it contains
the word "Infernal" (case-insensitive).

Options:
  --use-krcg  Fetch card text from KRCG API if not available locally
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CARDS_DIR = Path(__file__).resolve().parent.parent / 'gehenna_api' / 'data' / 'cards'
KRCG_API = 'https://static.krcg.org/data/vtes.json'

COUNT_UPDATE = 0
COUNT_SKIP = 0
COUNT_ERRORS = 0


def fetch_krcg_texts() -> dict[int, str]:
    """Fetch all card texts from KRCG API."""
    import httpx

    print('Fetching card texts from KRCG API...')
    try:
        resp = httpx.get(KRCG_API, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        texts = {}
        for card in data:
            codevdb = card.get('id')
            text = card.get('card_text', '')
            if codevdb and text:
                texts[codevdb] = text
        print(f'  Fetched {len(texts)} card texts')
        return texts
    except Exception as e:
        print(f'  Error fetching from KRCG: {e}')
        return {}


def has_infernal(text: str) -> bool:
    """Check if card text contains the Infernal trait."""
    if not text:
        return False
    return 'infernal' in text.lower()


def update_card_json(card_path: Path, krcg_texts: dict[int, str] | None = None) -> bool:
    """Update a single card JSON file. Returns True if updated."""
    global COUNT_UPDATE, COUNT_SKIP, COUNT_ERRORS

    try:
        data = json.loads(card_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f'  Error reading {card_path.name}: {e}')
        COUNT_ERRORS += 1
        return False

    codevdb = data.get('codevdb', 0) or int(card_path.stem)
    name = data.get('name', f'#{codevdb}')
    text = data.get('text', '') or ''

    # If no text locally, try KRCG API
    if not text and krcg_texts and codevdb in krcg_texts:
        text = krcg_texts[codevdb]
        data['text'] = text

    # Check if card has Infernal trait
    is_infernal = has_infernal(text)

    # Update if changed
    if data.get('is_infernal', False) != is_infernal:
        data['is_infernal'] = is_infernal
        card_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        COUNT_UPDATE += 1
        status = 'INFERNAL' if is_infernal else 'normal'
        print(f'  Updated {name}: {status}')
        return True

    COUNT_SKIP += 1
    return False


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description='Update card JSONs with is_infernal flag')
    parser.add_argument('--use-krcg', action='store_true', help='Fetch text from KRCG API')
    args = parser.parse_args()

    print('Updating card JSON files with is_infernal flag...\n')

    krcg_texts = None
    if args.use_krcg:
        krcg_texts = fetch_krcg_texts()
        print()

    for subdir in ['crypt', 'library']:
        cards_dir = CARDS_DIR / subdir
        if not cards_dir.exists():
            print(f'  Directory not found: {cards_dir}')
            continue

        print(f'Processing {subdir} cards...')
        for card_path in sorted(cards_dir.glob('*.json')):
            update_card_json(card_path, krcg_texts)
            # Small delay to be nice to the API
            if krcg_texts is None:
                time.sleep(0)

    print(f'\nDone: {COUNT_UPDATE} updated, {COUNT_SKIP} skipped, {COUNT_ERRORS} errors')


if __name__ == '__main__':
    main()
