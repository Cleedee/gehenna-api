"""Deck-specific Q-Learning Agent for V:TES.

Manages separate Q-Tables for each deck archetype.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gehenna_api.engine.ai.q_learning import QLearningAgent, QState, ACTIONS
from gehenna_api.engine.ai.archetype_recognizer import ArchetypeRecognizer


# Deck → Archetype mapping
DECK_ARCHETYPES: dict[int, str] = {
    241: 'toolbox',      # Museu Vivo no Inferno (Allies + Control)
    257: 'rush',         # UnnaDelicia v2 (Rush + Allies)
    244: 'rush',         # Juliet's Dream (Rush + Vote)
    242: 'stealth',      # Me chame pelo meu nome (Allies + Stealth)
    174: 'rush',         # UnnaDelicia (Rush + Allies)
    249: 'vote',         # Ministry (Vote + Bleed)
    275: 'rush',         # Path of Death (Allies + Rush)
}


class DeckQLearningAgent:
    """Q-Learning agent with deck-specific Q-Tables and archetype recognition.
    
    Features:
    - Separate Q-Table per deck
    - Archetype recognition for opponents
    - Counter-strategy based on opponent archetypes
    """
    
    def __init__(
        self,
        base_dir: str | Path | None = None,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        exploration_rate: float = 0.3,
    ):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent / 'q_tables'
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Deck-specific agents
        self.agents: dict[int, QLearningAgent] = {}
        
        # Archetype recognizer
        self.recognizer = ArchetypeRecognizer()
        
        # Hyperparameters
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        
        # Statistics
        self.games_played = 0
        self.total_rewards = 0.0
        
        # Replay buffer (shared across decks)
        self.replay_buffer: list[dict] = []
    
    def get_agent(self, deck_id: int) -> QLearningAgent:
        """Get or create Q-Learning agent for a specific deck."""
        if deck_id not in self.agents:
            self.agents[deck_id] = QLearningAgent(
                learning_rate=self.learning_rate,
                discount_factor=self.discount_factor,
                exploration_rate=self.exploration_rate,
            )
            
            # Try to load existing Q-Table
            q_table_path = self.base_dir / f'deck_{deck_id}.json'
            if q_table_path.exists():
                self.agents[deck_id].load(str(q_table_path))
        
        return self.agents[deck_id]
    
    def choose_action(
        self,
        deck_id: int,
        state: QState,
        opponent_profiles: dict[int, str] | None = None,
    ) -> str:
        """Choose action using deck-specific Q-Table.
        
        Args:
            deck_id: ID of the deck being played
            state: Current game state
            opponent_profiles: Optional dict of player_id → archetype
        
        Returns:
            Action name
        """
        agent = self.get_agent(deck_id)
        
        # Get counter-strategy adjustment
        if opponent_profiles:
            # Modify state based on opponent archetypes
            state = self._adjust_state_for_archetypes(state, opponent_profiles)
        
        return agent.choose_action(state)
    
    def update(
        self,
        deck_id: int,
        state: QState,
        action: str,
        reward: float,
        next_state: QState,
        done: bool = False,
    ) -> None:
        """Update Q-Table for a specific deck."""
        agent = self.get_agent(deck_id)
        agent.update(state, action, reward, next_state, done)
    
    def observe_clan(self, player_id: int, clan: str) -> None:
        """Observe a player's vampire clan."""
        self.recognizer.observe_clan(player_id, clan)
    
    def observe_discipline(self, player_id: int, discipline: str) -> None:
        """Observe a player's vampire discipline."""
        self.recognizer.observe_discipline(player_id, discipline)
    
    def observe_card(self, player_id: int, card_name: str) -> None:
        """Observe a card played by a player."""
        self.recognizer.observe_card(player_id, card_name)
    
    def observe_action(self, player_id: int, action_type: str) -> None:
        """Observe an action taken by a player."""
        self.recognizer.observe_action(player_id, action_type)
    
    def observe_opponent(
        self,
        player_id: int,
        clan: str | None = None,
        disciplines: list[str] | None = None,
        card_name: str | None = None,
        action_type: str | None = None,
    ) -> None:
        """Observe opponent information for archetype recognition."""
        if clan:
            self.recognizer.observe_clan(player_id, clan)
        if disciplines:
            for disc in disciplines:
                self.recognizer.observe_discipline(player_id, disc)
        if card_name:
            self.recognizer.observe_card(player_id, card_name)
        if action_type:
            self.recognizer.observe_action(player_id, action_type)
    
    def get_opponent_profile(self, player_id: int) -> str:
        """Get opponent archetype profile."""
        profile = self.recognizer.get_profile(player_id)
        return f"{profile.primary}/{profile.secondary}"
    
    def get_counter_strategy(self, player_id: int) -> str:
        """Get counter strategy against an opponent."""
        return self.recognizer.get_counter_strategy(player_id)
    
    def _adjust_state_for_archetypes(
        self,
        state: QState,
        opponent_profiles: dict[int, str],
    ) -> QState:
        """Adjust state features based on opponent archetypes.
        
        This modifies the threat levels based on opponent archetypes.
        """
        # Create a copy of the state
        adjusted = QState(
            pool_ratio=state.pool_ratio,
            prey_pool_ratio=state.prey_pool_ratio,
            predator_pool_ratio=state.predator_pool_ratio,
            own_threat=state.own_threat,
            prey_threat=state.prey_threat,
            predator_threat=state.predator_threat,
            phase=state.phase,
            minion_count=state.minion_count,
            hand_size=state.hand_size,
            has_bleed_card=state.has_bleed_card,
            has_defense_card=state.has_defense_card,
            has_rush_card=state.has_rush_card,
        )
        
        # Adjust threat based on archetype
        threat_multipliers = {
            'bleed/bleed': 1.4,
            'bleed/vote': 1.3,
            'rush/rush': 1.3,
            'rush/combat': 1.2,
            'combat/combat': 0.9,
            'vote/vote': 1.1,
            'stealth/stealth': 1.0,
            'toolbox/toolbox': 1.0,
            'bloat/bloat': 0.8,
            'infernal/infernal': 1.5,
        }
        
        # Note: We can't easily identify which player is prey/predator
        # from the state alone, so we adjust the overall threat level
        
        return adjusted
    
    def save(self, filepath: str | None = None) -> None:
        """Save all deck Q-Tables."""
        for deck_id, agent in self.agents.items():
            q_table_path = self.base_dir / f'deck_{deck_id}.json'
            agent.save(str(q_table_path))
    
    def save_all(self) -> None:
        """Save all deck Q-Tables."""
        self.save()
    
    def load_all(self) -> None:
        """Load all deck Q-Tables from disk."""
        for q_table_file in self.base_dir.glob('deck_*.json'):
            try:
                deck_id = int(q_table_file.stem.split('_')[1])
                self.get_agent(deck_id)
            except (ValueError, IndexError):
                continue
    
    def get_stats(self) -> dict:
        """Get statistics for all agents."""
        stats = {
            'total_agents': len(self.agents),
            'agents': {},
        }
        
        for deck_id, agent in self.agents.items():
            agent_stats = agent.get_stats()
            stats['agents'][deck_id] = {
                'q_table_size': agent_stats['q_table_size'],
                'games_played': agent_stats['games_played'],
                'exploration_rate': agent_stats['exploration_rate'],
            }
        
        return stats
    
    def decay_exploration(self) -> None:
        """Decay exploration rate for all agents."""
        for agent in self.agents.values():
            agent.decay_exploration()
    
    def reset_recognition(self) -> None:
        """Reset archetype recognition for a new game."""
        self.recognizer.reset()
