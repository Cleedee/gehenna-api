#!/usr/bin/env python3
"""Show how the bot analyzes opponent archetypes.

Usage:
    python scripts/show_archetype_analysis.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gehenna_api.engine.deck_loader import create_game_with_json_decks
from gehenna_api.engine.ai.strategy_bot import StrategyBot
from gehenna_api.engine.ai.deck_q_agent import DeckQLearningAgent
from gehenna_api.engine.card_instance import CardPosition


def analyze_archetypes(deck_ids: list[int], seed: int = 42):
    """Analyze archetypes for a game setup."""
    print("=" * 60)
    print("ANÁLISE DE RECONHECIMENTO DE ARQUÉTIPO")
    print("=" * 60)
    
    # Create game
    state, deck_ids = create_game_with_json_decks(
        deck_ids=deck_ids,
        seed=seed,
    )
    
    # Create bot for player 1
    rl_agent = DeckQLearningAgent()
    bot = StrategyBot(deck_id=deck_ids[0], use_rl=True, rl_agent=rl_agent)
    
    print(f"\nDecks na partida: {deck_ids}")
    print(f"Bot analisando: Deck {deck_ids[0]}")
    
    # Move some vampires to ready position
    print("\n1. SIMULANDO VAMPIROS EM CONTROLE")
    print("-" * 40)
    for player in state.players[1:4]:  # Players 2-4
        if player.crypt:
            vampire = state.card_by_id(player.crypt[0])
            if vampire:
                vampire.position = CardPosition.ready
                print(f"   Jogador {player.id}: {vampire.name}")
                print(f"     Clan: {vampire.clan}")
                print(f"     Disciplinas: {vampire.disciplines}")
    
    # Observe game state
    print("\n2. OBSERVANDO ESTADO DO JOGO")
    print("-" * 40)
    bot.observe_game_state(state)
    
    # Show observations
    print("\n3. OBSERVAÇÕES REALIZADAS")
    print("-" * 40)
    for player_id in [2, 3, 4]:
        player = state.player_by_id(player_id)
        if not player or player.is_ousted:
            continue
        
        print(f"\n   Jogador {player_id} ({player.username}):")
        
        # Show observed vampires
        vampires = bot.observed_vampires.get(player_id, set())
        print(f"     Vampiros observados: {len(vampires)}")
        
        # Show observed clans
        clans = rl_agent.recognizer.observed_clans.get(player_id, [])
        print(f"     Clãs: {clans}")
        
        # Show observed disciplines
        discs = rl_agent.recognizer.observed_disciplines.get(player_id, [])
        print(f"     Disciplinas: {discs}")
    
    # Analyze archetypes
    print("\n4. ANÁLISE DE ARQUÉTIPO")
    print("-" * 40)
    for player_id in [2, 3, 4]:
        player = state.player_by_id(player_id)
        if not player or player.is_ousted:
            continue
        
        print(f"\n   Jogador {player_id} ({player.username}):")
        
        # Get discipline profile
        profile = rl_agent.get_discipline_profile(player_id)
        if profile:
            print(f"     Arquétipo primário: {profile.primary_archetype}")
            print(f"     Arquétipo secundário: {profile.secondary_archetype}")
            print(f"     Rating de combate: {profile.combat_rating:.1f}")
            print(f"     Tem combate: {profile.has_combat}")
            print(f"     Tem stealth: {profile.has_stealth}")
            print(f"     Forças: {profile.strengths}")
            print(f"     Fraquezas: {profile.weaknesses}")
        
        # Get archetype profile
        archetype = rl_agent.recognizer.get_profile(player_id)
        print(f"     Arquétipo final: {archetype}")
        
        # Get counter strategy
        counter = rl_agent.get_counter_strategy_for_disciplines(player_id)
        print(f"     Contra-estratégia: {counter}")
    
    # Show how probabilities are calculated
    print("\n5. CÁLCULO DE PROBABILIDADES")
    print("-" * 40)
    print("\n   O bot usa as seguintes evidências:")
    print("   1. Clã do vampiro (peso: 0.3)")
    print("   2. Disciplinas individuais (peso: 0.2)")
    print("   3. Combinação de disciplinas (peso: 0.4-0.5)")
    print("   4. Cartas observadas (peso: 0.4)")
    print("   5. Ações observadas (peso: 0.15)")
    
    print("\n   Exemplo de mapeamento:")
    print("   - Dominate + Presence → Vote (peso: 0.5)")
    print("   - Celerity + Potence → Rush (peso: 0.5)")
    print("   - Obfuscate + Presence → Stealth (peso: 0.5)")
    
    # Show decision process
    print("\n6. PROCESSO DE DECISÃO")
    print("-" * 40)
    print("\n   Para cada oponente, o bot:")
    print("   1. Soma os scores de cada arquétipo")
    print("   2. Escolhe o arquétipo com maior score")
    print("   3. Calcula a contra-estratégia")
    print("   4. Ajusta sua ação baseado na fraqueza do oponente")
    
    print("\n   Exemplo:")
    print("   - Se presa tem CEL+POT (rush) → bot evita combate")
    print("   - Se presa tem DOM+PRE (vote) → bot usa stealth")
    print("   - Se presa tem OBF+PRE (bleed) → bot é agressivo")


def main():
    # Use decks with different archetypes
    deck_ids = [275, 241, 244, 242]  # toolbox, toolbox, rush, stealth
    
    analyze_archetypes(deck_ids, seed=42)


if __name__ == '__main__':
    main()
