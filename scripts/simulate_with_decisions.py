#!/usr/bin/env python3
"""Simulate game with detailed decision logging.

Usage:
    python scripts/simulate_with_decisions.py [--turns N] [--player N] [--deck DECK_ID]
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
        self.action_log = []
        self.verbose = True
        self.current_minion = None
    
    def _log(self, msg: str, indent: int = 0):
        """Print log message with indent."""
        if self.verbose:
            prefix = "    " * indent
            print(f"{prefix}{msg}")
    
    def choose_action_type(self, state, player_id, minion_id):
        """Log action type decision."""
        # Get minion info
        minion = state.card_by_id(minion_id)
        self.current_minion = minion
        
        # Get prey info
        prey = state.prey_of(player_id)
        prey_profile = None
        if prey and self.rl_agent:
            prey_profile = self.rl_agent.get_discipline_profile(prey.id)
        
        # Make decision
        action = super().choose_action_type(state, player_id, minion_id)
        
        # Log decision with details
        if minion:
            print(f"\n    🧛 {minion.name} ({minion.clan}) [{minion.disciplines}]")
            print(f"      💰 Blood: {minion.blood}")
        
        print(f"      🎯 Ação escolhida: {action.upper()}")
        
        if prey:
            print(f"      🎯 Presa: {prey.username}")
        if prey_profile:
            print(f"      📊 Arquétipo da presa: {prey_profile.primary_archetype}")
            if prey_profile.weaknesses:
                print(f"      ⚠️  Fraquezas: {', '.join(prey_profile.weaknesses[:2])}")
        
        # Log decision
        decision = {
            'turn': state.turn_number,
            'player': player_id,
            'minion': minion.name if minion else "Unknown",
            'minion_clan': minion.clan if minion else "",
            'minion_disc': minion.disciplines if minion else "",
            'action': action,
            'prey': prey.username if prey else None,
            'prey_archetype': prey_profile.primary_archetype if prey_profile else None,
            'prey_weaknesses': prey_profile.weaknesses if prey_profile else [],
        }
        self.decisions.append(decision)
        
        return action
    
    def choose_action(self, state, player_id) -> str:
        """Choose which card to play for action."""
        card_id = super().choose_action(state, player_id)
        
        if card_id:
            card = state.card_by_id(card_id)
            if card:
                print(f"      🃏 Carta selecionada: {card.name}")
                if hasattr(card, 'bleed') and card.bleed > 0:
                    print(f"        → Bleed: {card.bleed}")
                if hasattr(card, 'stealth') and card.stealth > 0:
                    print(f"        → Stealth: {card.stealth}")
                if hasattr(card, 'text') and card.text:
                    text_preview = card.text[:100] + "..." if len(card.text) > 100 else card.text
                    print(f"        → Texto: {text_preview}")
        
        return card_id
    
    def choose_block(self, state, player_id, action_id: str) -> bool:
        """Choose whether to block."""
        # Get action info
        action_card = state.card_by_id(action_id)
        
        block = super().choose_block(state, player_id, action_id)
        
        if action_card:
            status = "🚫 BLOQUEIA" if block else "✓ não bloqueia"
            print(f"      🛡️  {status} {action_card.name}")
        
        return block
    
    def log_action_result(self, state, player_id: int, action_type: str, 
                          success: bool, details: str = ""):
        """Log the result of an action."""
        if success:
            print(f"      ✅ Ação executada com sucesso!")
        else:
            print(f"      ❌ Ação falhou")
        if details:
            print(f"         {details}")
    
    def choose_discard(self, state, player_id, hand) -> str:
        """Choose which card to discard."""
        card_id = super().choose_discard(state, player_id, hand)
        
        if card_id:
            card = state.card_by_id(card_id)
            if card:
                print(f"      🗑️  Descarta: {card.name}")
        
        return card_id


def simulate_with_decisions(deck_ids: list[int], num_turns: int = 20, 
                            seed: int = 42, observe_player: int = 1):
    """Run simulation with detailed decision logging."""
    print("=" * 70)
    print("SIMULAÇÃO COM DECISÕES DETALHADAS DO BOT")
    print("=" * 70)
    
    # Create game
    state, deck_ids = create_game_with_json_decks(
        deck_ids=deck_ids,
        seed=seed,
    )
    
    print(f"\n📋 Decks: {deck_ids}")
    print(f"🔄 Turnos: {num_turns}")
    print(f"👁️  Observando: Jogador {observe_player}")
    
    # Create bots
    rl_agent = DeckQLearningAgent()
    bots = {}
    
    for i, deck_id in enumerate(deck_ids):
        player_id = i + 1
        if player_id == observe_player:
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
    
    print("\n" + "=" * 70)
    print("INÍCIO DA PARTIDA")
    print("=" * 70)
    
    # Show initial state
    print("\n📊 Estado inicial:")
    for player in state.players:
        print(f"  {player.username}: {player.pool} pool, "
              f"{len(player.crypt)} vampiros, {len(player.library)} library")
    
    # Show player's crypt
    obs_player = state.player_by_id(observe_player)
    if obs_player:
        print(f"\n🃏 Crypt do Jogador {observe_player}:")
        for cid in obs_player.crypt:
            card = state.card_by_id(cid)
            if card:
                print(f"  • {card.name} ({card.clan}) [{card.disciplines}]")
    
    # Run game
    print("\n" + "=" * 70)
    print(f"DECISÕES DO JOGADOR {observe_player}")
    print("=" * 70)
    
    for turn in range(num_turns):
        if state.is_finished:
            print(f"\n🏆 Jogo terminou no turno {state.turn_number}!")
            break
        
        print(f"\n{'─' * 70}")
        print(f"🔄 TURNO {state.turn_number + 1}")
        print(f"{'─' * 70}")
        
        # Run turn
        engine.run_turn()
        
        # Show player states AFTER turn (more accurate)
        print("\n📊 Estado dos jogadores:")
        for player in state.players:
            if player.is_ousted:
                print(f"  {player.username}: ❌ ELIMINADO")
            else:
                # Count ready minions
                prefix = f'p{player.id}_'
                ready = sum(1 for c in state.cards.values()
                          if c.id.startswith(prefix)
                          and c.is_ready
                          and c.tipo.strip() in {'Vampire', 'vampire', 'Imbued', 'Ally'})
                hand = len(player.hand)
                print(f"  {player.username}: 💚 {player.pool} pool | {ready} vampiros prontos | {hand} cartas")
    
    # Show final state
    print("\n" + "=" * 70)
    print("ESTADO FINAL")
    print("=" * 70)
    
    for player in state.players:
        status = "❌ ELIMINADO" if player.is_ousted else "VIVO"
        vps = player.victory_points if hasattr(player, 'victory_points') else 0
        print(f"  {player.username}: {status} | {player.pool} pool | {vps} VP")
    
    # Show winner
    winner = engine.get_winner()
    if winner:
        winner_player = state.player_by_id(winner)
        print(f"\n🏆 Vencedor: {winner_player.username if winner_player else 'Empate'}")
    else:
        print(f"\n🤝 Empate!")
    
    # Show bot's decisions
    verbose_bot = bots[observe_player]
    if isinstance(verbose_bot, VerboseStrategyBot) and verbose_bot.decisions:
        print("\n" + "=" * 70)
        print(f"RESUMO DAS DECISÕES DO JOGADOR {observe_player}")
        print("=" * 70)
        
        print(f"\n📈 Total de decisões: {len(verbose_bot.decisions)}")
        
        # Count action types
        action_counts = {}
        for d in verbose_bot.decisions:
            action = d['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        print("\n📊 Distribuição de ações:")
        for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {action:15} {bar} ({count})")
        
        # Show archetype awareness
        print("\n🎯 Arquétipos identificados:")
        seen = set()
        for d in verbose_bot.decisions:
            key = f"{d['prey']}_{d['prey_archetype']}"
            if d['prey_archetype'] and key not in seen:
                print(f"  • {d['prey']} → {d['prey_archetype']}")
                if d['prey_weaknesses']:
                    print(f"    Fraquezas: {', '.join(d['prey_weaknesses'][:3])}")
                seen.add(key)
        
        # Show decision reasoning
        print("\n🧠 Raciocínio do bot:")
        print("  1. Observa vampiros em controle (clã + disciplinas)")
        print("  2. Calcula score de arquétipo para cada oponente")
        print("  3. Determina arquétipo primário (maior score)")
        print("  4. Calcula contra-estratégia baseado na fraqueza")
        print("  5. Seleciona ação que explora essa fraqueza")
        
        # Show sample decisions
        print("\n📋 Últimas 5 decisões:")
        for d in verbose_bot.decisions[-5:]:
            print(f"  Turno {d['turn']}: {d['minion']} → {d['action']}")
            if d['prey']:
                print(f"    Presa: {d['prey']}")
            if d['prey_archetype']:
                print(f"    Arquétipo: {d['prey_archetype']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulate with detailed decision logging')
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
