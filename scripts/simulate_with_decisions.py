#!/usr/bin/env python3
"""Simulate game with decision logging.

Usage:
    python scripts/simulate_with_decisions.py [--turns N] [--deck DECK_ID]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gehenna_api.engine.deck_loader import create_game_with_json_decks
from gehenna_api.engine.engine import GameEngine
from gehenna_api.engine.ai.strategy_bot import StrategyBot
from gehenna_api.engine.ai.deck_q_agent import DeckQLearningAgent
from gehenna_api.engine.card_instance import CardPosition


class VerboseStrategyBot(StrategyBot):
    """StrategyBot with verbose decision logging."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decisions = []
    
    def choose_action_type(self, state, player_id, minion_id):
        """Log action type decision."""
        # Get prey info
        prey = state.prey_of(player_id)
        prey_profile = None
        if prey and self.rl_agent:
            prey_profile = self.rl_agent.get_discipline_profile(prey.id)
        
        # Make decision
        action = super().choose_action_type(state, player_id, minion_id)
        
        # Log decision
        decision = {
            'turn': state.turn_number,
            'player': player_id,
            'action': action,
            'prey': prey.username if prey else None,
            'prey_archetype': prey_profile.primary_archetype if prey_profile else None,
            'prey_weaknesses': prey_profile.weaknesses if prey_profile else [],
        }
        self.decisions.append(decision)
        
        return action
    
    def choose_block(self, state, player_id, action_id):
        """Log block decision."""
        block = super().choose_block(state, player_id, action_id)
        
        action_card = state.card_by_id(action_id)
        if action_card and player_id == 1:
            # Only log player 1's block decisions
            pass
        
        return block


def simulate_with_decisions(deck_ids: list[int], num_turns: int = 20, seed: int = 42, observe_player: int = 1):
    """Run simulation with decision logging."""
    print("=" * 60)
    print("SIMULAÇÃO COM DECISÕES DO BOT")
    print("=" * 60)
    
    # Create game
    state, deck_ids = create_game_with_json_decks(
        deck_ids=deck_ids,
        seed=seed,
    )
    
    print(f"\nDecks: {deck_ids}")
    print(f"Turnos: {num_turns}")
    print(f"Observando: Jogador {observe_player}")
    
    # Create bots
    rl_agent = DeckQLearningAgent()
    bots = {}
    
    for i, deck_id in enumerate(deck_ids):
        player_id = i + 1
        if player_id == observe_player:
            # Observed player is verbose
            bots[player_id] = VerboseStrategyBot(
                deck_id=deck_id,
                use_rl=True,
                rl_agent=rl_agent,
            )
        else:
            bots[player_id] = StrategyBot(
                deck_id=deck_id,
                use_rl=True,
                rl_agent=rl_agent,
            )
    
    # Create engine
    engine = GameEngine(state, bots=bots)
    engine.start()
    
    print("\n" + "=" * 60)
    print("INÍCIO DA PARTIDA")
    print("=" * 60)
    
    # Show initial state
    print("\nEstado inicial:")
    for player in state.players:
        print(f"  {player.username}: {player.pool} pool, {len(player.crypt)} vampiros, {len(player.library)} library")
    
    # Run game
    print("\n" + "=" * 60)
    print("DECISÕES DO BOT (Jogador 1)")
    print("=" * 60)
    
    for turn in range(num_turns):
        if state.is_finished:
            print(f"\nJogo terminou no turno {state.turn_number}!")
            break
        
        print(f"\n--- Turno {state.turn_number + 1} ---")
        
        # Show player states before turn
        print("\nEstado dos jogadores:")
        for player in state.players:
            if not player.is_ousted:
                print(f"  {player.username}: {player.pool} pool, {len(player.hand)} cartas na mão")
        
        # Run turn
        engine.run_turn()
        
        # Show what happened
        print(f"\nAções realizadas:")
        for player in state.players:
            if not player.is_ousted:
                # Count actions from hand size change
                print(f"  {player.username}: {player.pool} pool")
    
    # Show final state
    print("\n" + "=" * 60)
    print("ESTADO FINAL")
    print("=" * 60)
    
    for player in state.players:
        status = "ELIMINADO" if player.is_ousted else "VIVO"
        print(f"  {player.username}: {status}, {player.pool} pool, {player.victory_points} VP")
    
    # Show winner
    winner = engine.get_winner()
    if winner:
        winner_player = state.player_by_id(winner)
        print(f"\nVencedor: {winner_player.username if winner_player else 'Empate'}")
    else:
        print(f"\nEmpate!")
    
    # Show bot's decisions
    verbose_bot = bots[observe_player]
    if isinstance(verbose_bot, VerboseStrategyBot):
        print("\n" + "=" * 60)
        print("RESUMO DAS DECISÕES DO BOT")
        print("=" * 60)
        
        print(f"\nTotal de decisões: {len(verbose_bot.decisions)}")
        
        # Count action types
        action_counts = {}
        for d in verbose_bot.decisions:
            action = d['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        print("\nDistribuição de ações:")
        for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
            print(f"  {action}: {count}")
        
        # Show archetype awareness
        print("\nArquétipos identificados:")
        seen = set()
        for d in verbose_bot.decisions:
            key = f"{d['prey']}_{d['prey_archetype']}"
            if d['prey_archetype'] and key not in seen:
                print(f"  {d['prey']} → {d['prey_archetype']}")
                print(f"    Fraquezas: {d['prey_weaknesses']}")
                seen.add(key)
        
        # Show decision reasoning
        print("\nRaciocínio do bot:")
        print("  1. Observa vampiros em controle")
        print("  2. Extrai clã e disciplinas")
        print("  3. Calcula score de arquétipo")
        print("  4. Determina contra-estratégia")
        print("  5. Seleciona ação baseado na fraqueza")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulate with decision logging')
    parser.add_argument('--turns', type=int, default=20, help='Number of turns')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--deck', type=int, nargs='+', default=[275, 241, 244, 242], help='Deck IDs')
    parser.add_argument('--player', type=int, default=1, help='Player to observe (1-4)')
    
    args = parser.parse_args()
    
    simulate_with_decisions(
        deck_ids=args.deck,
        num_turns=args.turns,
        seed=args.seed,
        observe_player=args.player,
    )


if __name__ == '__main__':
    main()
