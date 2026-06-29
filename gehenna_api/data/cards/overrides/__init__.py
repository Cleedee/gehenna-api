"""
Card override loader.

Overrides are stored in data/cards/overrides/ directory.
Each override is a JSON file named {codevdb}.json.

Example:
    data/cards/overrides/102121.json
    {
        "is_unique": true,
        "master_type": "attached",
        "abilities": [...]
    }

To create an override, create a new file in the overrides directory.
Only include fields that override the base card data.
"""

from __future__ import annotations

import json
from pathlib import Path

OVERRIDES_DIR = Path(__file__).resolve().parent


def load_override(codevdb: int) -> dict | None:
    """Load override for a card by codevdb. Returns None if no override exists."""
    override_path = OVERRIDES_DIR / f'{codevdb}.json'
    if not override_path.exists():
        return None
    try:
        with open(override_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_override(codevdb: int, data: dict) -> None:
    """Save an override file for a card."""
    OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)
    override_path = OVERRIDES_DIR / f'{codevdb}.json'
    with open(override_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_all_override_ids() -> list[int]:
    """Get list of all card IDs that have overrides."""
    if not OVERRIDES_DIR.exists():
        return []
    ids = []
    for fname in sorted(OVERRIDES_DIR.glob('*.json')):
        try:
            ids.append(int(fname.stem))
        except ValueError:
            continue
    return ids
