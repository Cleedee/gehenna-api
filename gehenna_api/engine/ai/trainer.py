"""Trainer for V:TES Q-Learning agent.

Runs games to collect experience and train the Q-Learning agent.
"""

from __future__ import annotations

import random as rng_random
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from gehenna_api.engine.ai.q_learning import QLearningAgent, QState
from gehenna_api.engine.ai.state_encoder import StateEncoder
from gehenna_api.engine.ai.reward import RewardCalculator
from gehenna_api.engine.ai.deck_q_agent import DeckQLearningAgent
from gehenna_api.engine.engine import GameEngine
from gehenna_api.engine.state import GameState, PlayerState
from gehenna_api.engine.ai.random_bot import RandomBot
from gehenna_api.engine.deck_loader import (
    list_available_decks,
    create_game_with_json_decks,
)


class QLearningBot:
    """Bot that uses Q-Learning for decision making."""
    
    def __init__(self, agent: DeckQLearningAgent, deck_id: int):
        self.agent = agent
        self.deck_id = deck_id
        self.current_state: QState | None = None
        self.last_action: str | None = None
        
        # Use StrategyBot with Q-Learning enabled
        from gehenna_api.engine.ai.strategy_bot import StrategyBot
        self.strategy_bot = StrategyBot(
            deck_id=deck_id,
            use_rl=True,
            rl_agent=agent,
        )
    
    def choose_action_type(self, state: GameState, player_id: int, minion_id: str) -> str:
        """Choose action using StrategyBot with Q-Learning."""
        self.current_state = StateEncoder(state, player_id).encode()
        self.last_action = self.strategy_bot.choose_action_type(state, player_id, minion_id)
        return self.last_action
    
    def choose_action(self, state: GameState, player_id: int) -> str:
        """Choose which card to play from hand."""
        return self.strategy_bot.choose_action(state, player_id)
    
    def choose_block(self, state: GameState, player_id: int, action_id: str) -> bool:
        """Choose whether to block."""
        return self.strategy_bot.choose_block(state, player_id, action_id)
    
    def choose_strike(self, state: GameState, combatant_id: str) -> str:
        """Choose strike type."""
        return self.strategy_bot.choose_strike(state, combatant_id)
    
    def choose_discard(self, state: GameState, player_id: int, hand: list[str]) -> str:
        """Choose which card to discard."""
        return self.strategy_bot.choose_discard(state, player_id, hand)
    
    def record_action_outcome(
        self,
        state: GameState,
        player_id: int,
        action_type: str,
        outcome: str,
        card_name: str | None = None,
    ) -> None:
        """Record action outcome for learning."""
        self.strategy_bot.record_action_outcome(
            state, player_id, action_type, outcome, card_name
        )
    
    def record_outcome(self, state: GameState, player_id: int, reward: float) -> None:
        """Record outcome and update Q-values."""
        if self.current_state is None or self.last_action is None:
            return
        
        encoder = StateEncoder(state, player_id)
        next_state = encoder.encode()
        
        # Check if game is done
        done = state.is_finished
        
        # Update Q-values
        self.agent.update(self.deck_id, self.current_state, self.last_action, reward, next_state, done)
        
        # Reset for next action
        self.current_state = None
        self.last_action = None


class Trainer:
    """Trains Q-Learning agent through self-play."""
    
    def __init__(
        self,
        agent: QLearningAgent,
        num_games: int = 100,
        save_interval: int = 10,
        verbose: bool = True,
    ):
        self.agent = agent
        self.num_games = num_games
        self.save_interval = save_interval
        self.verbose = verbose
        
        # Statistics
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.total_rewards = 0.0
    
    def train(self, save_path: str | None = None) -> dict:
        """Run training."""
        if self.verbose:
            print(f"Starting training for {self.num_games} games...")
        
        for game_num in range(self.num_games):
            # Run one game
            result = self._run_game(game_num)
            
            # Update statistics
            if result['winner'] == 'rl_bot':
                self.wins += 1
            elif result['winner'] is None:
                self.draws += 1
            else:
                self.losses += 1
            
            self.total_rewards += result['total_reward']
            
            # Decay exploration
            self.agent.decay_exploration()
            self.agent.games_played += 1
            
            # Train on replay buffer
            if len(self.agent.replay_buffer) >= 32:
                loss = self.agent.train_on_buffer(batch_size=32)
            
            # Print progress
            if self.verbose and (game_num + 1) % 10 == 0:
                win_rate = self.wins / (game_num + 1) * 100
                print(f"Game {game_num + 1}/{self.num_games}: "
                      f"Wins={self.wins} ({win_rate:.1f}%), "
                      f"Draws={self.draws}, Losses={self.losses}")
            
            # Save periodically
            if save_path and (game_num + 1) % self.save_interval == 0:
                self.agent.save(save_path)
        
        # Final save
        if save_path:
            self.agent.save(save_path)
        
        return self._get_stats()
    
    def _run_game(self, game_num: int) -> dict:
        """Run a single game and collect experience."""
        # Get available decks
        available = list_available_decks()
        if len(available) < 4:
            # Fallback to simple decks
            return self._run_simple_game(game_num)
        
        # Randomly select 4 decks
        selected = rng_random.sample(available, 4)
        deck_ids = [d['deck_id'] for d in selected]
        
        # Create game with real decks
        state, _ = create_game_with_json_decks(
            deck_ids=deck_ids,
            seed=game_num,
        )
        
        # Create bots - RL bot as Player 1, Random bots for others
        bots = {}
        rl_bot = QLearningBot(self.agent, deck_ids[0])
        bots[1] = rl_bot
        for i in range(2, 5):  # Players 2-4
            bots[i] = RandomBot()
        
        # Run game
        engine = GameEngine(state, bots=bots)
        engine.start()
        
        total_reward = 0.0
        
        for turn in range(30):
            # Track pool before turn
            p1 = state.player_by_id(1)
            prev_pool = p1.pool if p1 else 30
            
            # Run turn
            engine.run_turn()
            
            if state.is_finished:
                break
            
            # Calculate reward based on pool change
            p1 = state.player_by_id(1)
            current_pool = p1.pool if p1 else 30
            pool_delta = current_pool - prev_pool
            
            if rl_bot.current_state:
                reward = 0.0
                if pool_delta > 0:
                    reward = 0.2 * pool_delta  # Gained pool
                elif pool_delta < 0:
                    reward = -0.1 * abs(pool_delta)  # Lost pool
                
                # Record outcome
                if rl_bot.current_state and rl_bot.last_action:
                    encoder = StateEncoder(state, 1)
                    next_state = encoder.encode()
                    
                    # Map action to Q-Learning action
                    action_map = {
                        'bleed': 'bleed',
                        'rush': 'rush',
                        'control': 'control',
                        'action_card': 'bloat',  # Map action_card to bloat
                        'stealth': 'stealth',
                        'recruit': 'recruit',
                        'vote': 'control',
                    }
                    rl_action = action_map.get(rl_bot.last_action, 'bleed')
                    
                    self.agent.update(
                        rl_bot.deck_id,
                        rl_bot.current_state,
                        rl_action,
                        reward,
                        next_state,
                        done=False,
                    )
                total_reward += reward
        
        # Final reward based on game outcome
        winner_id = engine.get_winner()
        if winner_id and winner_id == 1:
            final_reward = 1.0  # Win
            winner_name = 'rl_bot'
        elif winner_id:
            final_reward = -0.5  # Loss
            winner_name = 'other'
        else:
            final_reward = 0.0  # Draw
            winner_name = None
        
        total_reward += final_reward
        
        # Record final outcome
        if rl_bot.current_state and rl_bot.last_action:
            encoder = StateEncoder(state, 1)
            next_state = encoder.encode()
            
            # Map action to Q-Learning action
            action_map = {
                'bleed': 'bleed',
                'rush': 'rush',
                'control': 'control',
                'action_card': 'bloat',
                'stealth': 'stealth',
                'recruit': 'recruit',
                'vote': 'control',
            }
            rl_action = action_map.get(rl_bot.last_action, 'bleed')
            
            self.agent.update(
                rl_bot.deck_id,
                rl_bot.current_state,
                rl_action,
                final_reward,
                next_state,
                done=True,
            )
        
        return {
            'winner': winner_name,
            'total_reward': total_reward,
            'turns': state.turn_number,
        }
    
    def _run_simple_game(self, game_num: int) -> dict:
        """Run a simple game with basic decks (fallback)."""
        state = GameState(game_id=f'train_simple_{game_num}', seed=game_num)
        
        num_players = 4
        for i in range(1, num_players + 1):
            ps = PlayerState(
                id=i,
                username=f'Player {i}',
                pool=30,
                hand=[],
                crypt=[],
                library=[],
                ash_heap=[],
                has_edge=False,
                transfers=0,
                victory_points=0,
            )
            state.players.append(ps)
        
        bots = {}
        rl_bot = QLearningBot(self.agent)
        bots[1] = rl_bot
        for i in range(2, num_players + 1):
            bots[i] = RandomBot()
        
        engine = GameEngine(state, bots=bots)
        engine.start()
        
        total_reward = 0.0
        
        for turn in range(30):
            engine.run_turn()
            if state.is_finished:
                break
        
        winner_id = engine.get_winner()
        if winner_id and winner_id == 1:
            final_reward = 1.0
            winner_name = 'rl_bot'
        elif winner_id:
            final_reward = -0.5
            winner_name = 'other'
        else:
            final_reward = 0.0
            winner_name = None
        
        return {
            'winner': winner_name,
            'total_reward': final_reward,
            'turns': state.turn_number,
        }
    
    def _get_stats(self) -> dict:
        """Get training statistics."""
        return {
            'games_played': self.num_games,
            'wins': self.wins,
            'draws': self.draws,
            'losses': self.losses,
            'win_rate': self.wins / self.num_games * 100,
            'total_rewards': self.total_rewards,
            'avg_reward': self.total_rewards / self.num_games,
            'agent_stats': self.agent.get_stats(),
        }


def train_agent(
    num_games: int = 100,
    save_path: str | None = None,
    verbose: bool = True,
) -> DeckQLearningAgent:
    """Convenience function to train an agent."""
    agent = DeckQLearningAgent()
    agent.load_all()
    
    trainer = Trainer(
        agent=agent,
        num_games=num_games,
        save_interval=10,
        verbose=verbose,
    )
    
    stats = trainer.train(save_path)
    
    if verbose:
        print("\nTraining complete!")
        print(f"Win rate: {stats['win_rate']:.1f}%")
        deck_stats = stats.get('agent_stats', {}).get('agents', {})
        for deck_id, ds in deck_stats.items():
            print(f"  Deck {deck_id}: {ds['q_table_size']} entries")
    
    return agent


if __name__ == '__main__':
    # Run training when executed directly
    agent = train_agent(
        num_games=100,
        save_path='q_table.json',
        verbose=True,
    )
