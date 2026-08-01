"""Trainer for V:TES Q-Learning agent.

Runs games to collect experience and train the Q-Learning agent.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from gehenna_api.engine.ai.q_learning import QLearningAgent, QState
from gehenna_api.engine.ai.state_encoder import StateEncoder
from gehenna_api.engine.ai.reward import RewardCalculator
from gehenna_api.engine.engine import GameEngine
from gehenna_api.engine.state import GameState, PlayerState
from gehenna_api.engine.ai.random_bot import RandomBot


class QLearningBot:
    """Bot that uses Q-Learning for decision making."""
    
    def __init__(self, agent: QLearningAgent):
        self.agent = agent
        self.current_state: QState | None = None
        self.last_action: str | None = None
    
    def choose_action_type(self, state: GameState, player_id: int, minion_id: str) -> str:
        """Choose action using Q-Learning."""
        encoder = StateEncoder(state, player_id)
        self.current_state = encoder.encode()
        self.last_action = self.agent.choose_action(self.current_state)
        return self.last_action
    
    def choose_action(self, state: GameState, player_id: int) -> str:
        """Choose which card to play from hand."""
        # For now, return empty to use default behavior
        return ''
    
    def choose_block(self, state: GameState, player_id: int, action_id: str) -> bool:
        """Choose whether to block."""
        # Don't block to keep it simple
        return False
    
    def choose_strike(self, state: GameState, combatant_id: str) -> str:
        """Choose strike type."""
        return 'handstrike'
    
    def choose_discard(self, state: GameState, player_id: int, hand: list[str]) -> str:
        """Choose which card to discard."""
        return hand[-1] if hand else ''
    
    def record_outcome(self, state: GameState, player_id: int, reward: float) -> None:
        """Record outcome and update Q-values."""
        if self.current_state is None or self.last_action is None:
            return
        
        encoder = StateEncoder(state, player_id)
        next_state = encoder.encode()
        
        # Check if game is done
        done = state.is_finished
        
        # Update Q-values
        self.agent.update(self.current_state, self.last_action, reward, next_state, done)
        
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
        # Create game state
        state = GameState(game_id=f'train_{game_num}', seed=game_num)
        rng = state.random
        
        # Create players with simple crypt/library
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
            
            # Add a simple vampire for each player
            from gehenna_api.engine.card_instance import CardInstance, CardPosition
            v = CardInstance(
                id=f'p{i}_vamp_1',
                card_id=1000 + i,
                name=f'Vampire {i}',
                tipo='vampire',
                capacity=5,
                blood=5,
                pool_cost=5,
                position=CardPosition.uncontrolled,
                strength=1,
                stealth=0,
                intercept=0,
                bleed=0,
                disciplines='|dom|DOM|',
            )
            state.cards[v.id] = v
            ps.crypt = [v.id]
        
        # Create bots - RL bot as Player 1, Random bots for others
        bots = {}
        rl_bot = QLearningBot(self.agent)
        bots[1] = rl_bot
        for i in range(2, num_players + 1):
            bots[i] = RandomBot()
        
        # Run game
        engine = GameEngine(state, bots=bots)
        engine.start()
        
        total_reward = 0.0
        reward_calc = RewardCalculator(state, 1)
        
        for turn in range(30):
            # Track pool before turn
            prev_pool = state.player_by_id(1).pool if state.player_by_id(1) else 30
            
            # Run turn
            engine.run_turn()
            
            if state.is_finished:
                break
            
            # Calculate reward based on pool change
            current_pool = state.player_by_id(1).pool if state.player_by_id(1) else 30
            pool_delta = current_pool - prev_pool
            
            if rl_bot.current_state:
                reward = 0.0
                if pool_delta > 0:
                    reward = 0.2 * pool_delta  # Gained pool
                elif pool_delta < 0:
                    reward = -0.1 * abs(pool_delta)  # Lost pool
                
                # Record outcome
                rl_bot.record_outcome(state, 1, reward)
                total_reward += reward
        
        # Final reward based on game outcome
        winner = engine.get_winner()
        if winner and winner.id == 1:
            final_reward = 1.0  # Win
            winner_name = 'rl_bot'
        elif winner:
            final_reward = -0.5  # Loss
            winner_name = 'other'
        else:
            final_reward = 0.0  # Draw
            winner_name = None
        
        total_reward += final_reward
        
        # Record final outcome
        if rl_bot.current_state:
            rl_bot.record_outcome(state, 1, final_reward)
        
        return {
            'winner': winner_name,
            'total_reward': total_reward,
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
) -> QLearningAgent:
    """Convenience function to train an agent."""
    agent = QLearningAgent()
    
    if save_path and Path(save_path).exists():
        agent.load(save_path)
        if verbose:
            print(f"Loaded existing agent with {agent.games_played} games played")
    
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
        print(f"Q-table size: {stats['agent_stats']['q_table_size']}")
    
    return agent


if __name__ == '__main__':
    # Run training when executed directly
    agent = train_agent(
        num_games=100,
        save_path='q_table.json',
        verbose=True,
    )
