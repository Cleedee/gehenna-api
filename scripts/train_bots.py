#!/usr/bin/env python3
"""Training script for V:TES bots.

Usage:
    python scripts/train_bots.py [--games N] [--deck DECK_ID] [--verbose]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gehenna_api.engine.ai.trainer import train_agent
from gehenna_api.engine.ai.deck_q_agent import DeckQLearningAgent


def train(
    num_games: int = 100,
    deck_id: int | None = None,
    verbose: bool = True,
) -> DeckQLearningAgent:
    """Train bots with Q-Learning."""
    print(f"=== Training {num_games} games ===")
    
    agent = train_agent(
        num_games=num_games,
        save_path='/tmp/q_table.json',
        verbose=verbose,
    )
    
    # Print stats
    stats = agent.get_stats()
    print(f"\nFinal stats:")
    print(f"  Total agents: {stats['total_agents']}")
    for did, ds in stats['agents'].items():
        print(f"  Deck {did}: {ds['q_table_size']} entries, {ds['games_played']} games")
    
    return agent


def main():
    parser = argparse.ArgumentParser(description='Train V:TES bots')
    parser.add_argument('--games', type=int, default=100, help='Number of games')
    parser.add_argument('--deck', type=int, help='Specific deck ID to train')
    parser.add_argument('--verbose', action='store_true', default=True)
    
    args = parser.parse_args()
    
    train(
        num_games=args.games,
        deck_id=args.deck,
        verbose=args.verbose,
    )


if __name__ == '__main__':
    main()
