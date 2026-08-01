"""Load decks from gehenna_api/data/decks/ directory."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.card_loader import load_card


DECKS_DIR = Path(__file__).parent.parent / "data" / "decks"


def list_available_decks() -> list[dict[str, Any]]:
    """List all available decks in the data/decks directory."""
    decks = []
    for f in DECKS_DIR.glob("*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
            deck_id = data.get("deck_id", 0)
            name = data.get("name", "Unknown")
            cards = data.get("cards", [])
            total = sum(c.get("quantity", 1) for c in cards)
            decks.append({
                "deck_id": deck_id,
                "name": name,
                "total_cards": total,
                "file": str(f),
            })
        except Exception:
            continue
    return decks


def _get_card_capacity(codevdb: int, card_name: str, card_type: str) -> int:
    """Get card capacity from database."""
    import sqlite3
    conn = sqlite3.connect(str(Path(__file__).parent.parent.parent / "database.db"))
    cursor = conn.cursor()
    
    # Try by code first
    cursor.execute("SELECT capacity FROM cards WHERE code = ?", (codevdb,))
    row = cursor.fetchone()
    
    # If not found, try by name
    if not row and card_name:
        cursor.execute("SELECT capacity FROM cards WHERE name = ?", (card_name,))
        row = cursor.fetchone()
    
    conn.close()
    
    if row and row[0]:
        try:
            return int(row[0])
        except (ValueError, TypeError):
            pass
    return 0


def load_deck_from_json(
    deck_id: int,
    player_id: int,
    rng: Any = None,
) -> tuple[list[CardInstance], list[CardInstance]]:
    """Load a deck from the data/decks directory.
    
    Returns:
        (crypt_cards, library_cards)
    """
    deck_file = DECKS_DIR / f"{deck_id}.json"
    if not deck_file.exists():
        raise FileNotFoundError(f"Deck {deck_id} not found in {DECKS_DIR}")
    
    with open(deck_file) as f:
        data = json.load(f)
    
    cards_data = data.get("cards", [])
    
    crypt = []
    library = []
    
    for card_data in cards_data:
        codevdb = card_data.get("codevdb", 0)
        quantity = card_data.get("quantity", 1)
        card_type = card_data.get("tipo", "")
        
        # Load full card data from JSON
        card_info = load_card(codevdb)
        
        # Get capacity from database
        capacity = _get_card_capacity(codevdb, card_data.get("name", ""), card_type)
        
        for i in range(quantity):
            # Create card instance
            card_id = f"p{player_id}_c{codevdb}_{i}"
            
            if card_info:
                # Use loaded card data
                # Convert modifiers dict to list of strings
                mod_list = []
                for k, v in card_info.modifiers.items():
                    if v:
                        mod_list.append(f"{k}:{v}")
                
                instance = CardInstance(
                    id=card_id,
                    card_id=codevdb,
                    name=card_info.name,
                    position=CardPosition.library,
                    blood=capacity if card_type.lower() == "vampire" else 0,
                    capacity=capacity,
                    life=card_info.life,
                    strength=card_info.strength,
                    stealth=card_info.modifiers.get("stealth", 0),
                    intercept=card_info.modifiers.get("intercept", 0),
                    bleed=card_info.modifiers.get("bleed", 0),
                    tipo=card_info.tipo,
                    is_infernal=card_info.is_infernal,
                    abilities=card_info.abilities,
                    modifiers=mod_list,
                )
            else:
                # Fallback: use data from deck file
                instance = CardInstance(
                    id=card_id,
                    card_id=codevdb,
                    name=card_data.get("name", f"Card {codevdb}"),
                    position=CardPosition.library,
                    tipo=card_type,
                    capacity=capacity,
                    blood=capacity if card_type.lower() == "vampire" else 0,
                )
            
            # Separate crypt and library
            if card_type.lower() in ("vampire", "imbued"):
                instance.position = CardPosition.crypt
                crypt.append(instance)
            else:
                library.append(instance)
    
    # Shuffle if rng provided
    if rng:
        rng.shuffle(crypt)
        rng.shuffle(library)
    
    return crypt, library


def create_game_with_json_decks(
    deck_ids: list[int],
    player_names: list[str] | None = None,
    seed: int | None = None,
) -> tuple[Any, list[int]]:
    """Create a game using decks from data/decks directory.
    
    Returns:
        (GameState, list of deck_ids used)
    """
    from gehenna_api.engine.state import GameState, PlayerState
    
    if player_names is None:
        player_names = [f"P{i+1}" for i in range(len(deck_ids))]
    
    state = GameState(
        game_id=f"json_deck_{seed or 0}",
        seed=seed,
    )
    rng = state.random
    
    for i, (deck_id, name) in enumerate(zip(deck_ids, player_names)):
        pid = i + 1
        
        try:
            crypt, library = load_deck_from_json(deck_id, pid, rng)
        except FileNotFoundError:
            # Fallback to database deck
            from gehenna_api.engine.server import _load_deck, _build_pool
            from gehenna_api.engine.card_instance import CardPosition
            
            crypt_data, library_data = _load_deck(deck_id)
            crypt = _build_pool(crypt_data, f"p{pid}_crypt", rng)
            library = _build_pool(library_data, f"p{pid}_lib", rng)
            
            for c in crypt:
                c.id = f"p{pid}_{c.id}"
                state.cards[c.id] = c
            for c in library:
                c.id = f"p{pid}_{c.id}"
                state.cards[c.id] = c
        
        # Add cards to state
        for c in crypt:
            state.cards[c.id] = c
        for c in library:
            state.cards[c.id] = c
        
        # Create player
        ps = PlayerState(
            id=pid,
            username=name,
            pool=30,
            hand=[],
            crypt=[c.id for c in crypt],
            library=[c.id for c in library],
            ash_heap=[],
            has_edge=False,
            transfers=0,
            victory_points=0,
        )
        state.players.append(ps)
    
    return state, deck_ids
