"""Strategy Bot - Uses StrategyEngine for intelligent decisions."""

from __future__ import annotations

import os
from pathlib import Path

from gehenna_api.engine.ai.base import Bot
from gehenna_api.engine.ai.strategy import (
    CardKnowledge,
    CardTiming,
    ComboSystem,
    GameStateAnalyzer,
    LearningSystem,
    DeckStrategy,
    StrategyEngine,
    DEFAULT_STRATEGIES,
)
from gehenna_api.engine.ai.deck_q_agent import DeckQLearningAgent
from gehenna_api.engine.ai.state_encoder import StateEncoder
from gehenna_api.engine.card_instance import CardInstance, CardPosition
from gehenna_api.engine.state import GameState


class StrategyBot(Bot):
    """Bot that uses strategy configurations for decision making."""

    def __init__(
        self,
        deck_id: int = 0,
        strategies_dir: str | None = None,
        use_rl: bool = False,
        rl_agent: DeckQLearningAgent | None = None,
    ):
        self.deck_id = deck_id
        self.engine = StrategyEngine(strategies_dir)
        self.strategy = self.engine.get_strategy(deck_id)

        # Track game state for adaptation
        self.cards_played: list[str] = []
        self.cards_seen: dict[int, list[str]] = {}  # player_id -> cards
        self.turns_played: int = 0
        
        # New systems
        self.learning = LearningSystem()
        self.combo_system: ComboSystem | None = None
        
        # Q-Learning (optional)
        self.use_rl = use_rl
        self.rl_agent = rl_agent
        self.rl_state_encoder: StateEncoder | None = None
        
        # Track observed vampires (clan + disciplines)
        self.observed_vampires: dict[int, set[str]] = {}  # player_id -> set of vampire_ids

    def choose_action(
        self, state: GameState, player_id: int
    ) -> str:
        """Choose which action card to play from hand.
        
        This is called when the engine needs to select a specific card.
        Returns card ID to play.
        """
        player = state.player_by_id(player_id)
        if not player or not player.hand:
            return ""
        
        # Use CardKnowledge for intelligent card selection
        knowledge = CardKnowledge(state, player_id)
        timing = CardTiming(state, player_id)
        
        # Get prioritized cards for bleed action (default)
        prioritized = knowledge.prioritize_cards_for_situation('bleed')
        
        # Return highest priority card that should be played
        for card, priority in prioritized:
            # Check if we should hold this card
            if knowledge.should_hold_card(card) and priority < 80:
                continue
            
            # Check by effect (from JSON)
            abilities = getattr(card, 'abilities', None) or []
            for ab in abilities:
                effects = getattr(ab, 'effects', None) or []
                for eff in effects:
                    func = getattr(eff, 'function', '')
                    
                    # Redirect bleed - don't play proactively
                    if func == 'reaction.redirect_bleed':
                        continue
            
            # Check by category
            category = knowledge.get_card_category(card)
            
            # Skip defensive cards
            if category == 'defense':
                continue
            
            # Skip stealth unless needed
            if category == 'stealth' and not timing.should_play_stealth('bleed'):
                continue
            
            # Play action cards
            if card.tipo.strip().lower() == 'action':
                return card.id
        
        # If no good card found, return first action card
        for cid in player.hand:
            card = state.card_by_id(cid)
            if card and card.tipo.strip().lower() == 'action':
                return card.id
        
        return ""

    def choose_action_type(
        self,
        state: GameState,
        player_id: int,
        minion_id: str,
    ) -> str:
        """Choose action type based on strategy."""
        self.turns_played = state.turn_number
        
        # Observe game state for archetype recognition (once per turn)
        if self.use_rl and self.rl_agent:
            self.observe_game_state(state)
        
        # Initialize combo system if needed
        if self.combo_system is None:
            self.combo_system = ComboSystem(state, player_id)
        
        # Get strategic position for learning
        analyzer = GameStateAnalyzer(state, player_id)
        strategic_position = analyzer.get_strategic_position(self.engine.threat_assessor)
        
        # Get game phase
        phase = self.engine.determine_game_phase(state, player_id)
        
        # Try Q-Learning if enabled
        if self.use_rl and self.rl_agent:
            rl_action = self._try_rl_action(state, player_id, phase)
            if rl_action:
                self.cards_played.append(rl_action)
                self.learning.record_action(
                    rl_action, None, strategic_position, 'pending',
                    phase=phase.value
                )
                return rl_action
        
        # Check if we should adapt based on learning
        if self.learning.should_adapt_strategy():
            adaptation = self.learning.get_adaptation_suggestion()
            # Apply adaptation to strategy (simplified for now)
        
        # Check for available combos
        combos = self.combo_system.detect_available_combos()
        if combos:
            # Prioritize combo plays
            best_combo = max(combos, key=lambda x: x['priority'])
            if best_combo['priority'] > 80:
                # Play combo cards
                action = self._get_combo_action(best_combo, state, player_id)
                if action:
                    self.cards_played.append(action)
                    # Record for learning
                    self.learning.record_action(
                        action, None, strategic_position, 'pending',
                        phase=phase.value
                    )
                    return action

        # Use strategy engine
        action = self.engine.choose_action_type(
            state=state,
            player_id=player_id,
            minion_id=minion_id,
            deck_id=self.deck_id,
        )

        # Track for adaptation
        self.cards_played.append(action)
        
        # Record for learning
        self.learning.record_action(
            action, None, strategic_position, 'pending',
            phase=phase.value
        )

        return action
    
    def _try_rl_action(
        self,
        state: GameState,
        player_id: int,
        phase: str,
    ) -> str | None:
        """Try to get action from Q-Learning agent."""
        try:
            # Encode state
            encoder = StateEncoder(state, player_id)
            q_state = encoder.encode()
            
            # Get opponent profiles for archetype recognition
            opponent_profiles = {}
            for p in state.players:
                if p.id != player_id and not p.is_ousted:
                    profile = self.rl_agent.get_opponent_profile(p.id)
                    opponent_profiles[p.id] = profile
            
            # Get action from Q-Learning
            action = self.rl_agent.choose_action(
                self.deck_id,
                q_state,
                opponent_profiles,
            )
            
            # Map Q-Learning action to strategy action
            action_map = {
                'bleed': 'bleed',
                'rush': 'rush',
                'control': 'control',
                'bloat': 'action_card',  # Use Govern for bloat
                'stealth': 'action_card',  # Play stealth card
                'recruit': 'action_card',  # Recruit ally
                'pass': 'bleed',  # Default to bleed
            }
            
            return action_map.get(action, 'bleed')
        except Exception:
            return None
    
    def _get_combo_action(
        self, combo: dict, state: GameState, player_id: int
    ) -> str | None:
        """Get action type for a combo."""
        benefit = combo.get('benefit', '')
        
        if benefit == 'acceleration':
            return 'action_card'  # Use Govern for acceleration
        elif benefit == '5_damage':
            return 'rush'  # Rush with Freakish
        elif benefit == 'guaranteed_bleed':
            return 'bleed'  # Bleed with stealth
        
        return None

    def choose_block(
        self,
        state: GameState,
        player_id: int,
        action_id: str,
    ) -> bool:
        """Choose whether to block."""
        player = state.player_by_id(player_id)
        if not player:
            return False

        # Get the action card
        action_card = state.card_by_id(action_id)
        if not action_card:
            return False

        # Check if action is bleed
        text = (getattr(action_card, "text", "") or "").lower()
        is_bleed = "bleed" in text or action_card.bleed > 0
        is_high_bleed = action_card.bleed > 2

        # Block high-threat bleeds against us
        if is_bleed and is_high_bleed:
            return True

        # Don't waste resources on small actions
        return False

    def choose_strike(
        self,
        state: GameState,
        combatant_id: str,
    ) -> str:
        """Choose strike type."""
        combatant = state.card_by_id(combatant_id)
        if not combatant:
            return "handstrike"

        # Use best available strike
        # Prioritize: Steal Blood > Aggravated > Hand Strike
        if combatant.has_steal_blood:
            return "steal_blood"

        # Check for aggravated damage cards
        for cid in combatant.hand:
            card = state.card_by_id(cid)
            if card and getattr(card, "is_aggravated", False):
                return card.id

        # Default to hand strike
        return "handstrike"

    def choose_discard(
        self,
        state: GameState,
        player_id: int,
        hand: list[str],
    ) -> str:
        """Choose which card to discard."""
        player = state.player_by_id(player_id)
        if not player or not hand:
            return ""

        # Strategy-based discard
        strategy = self.strategy

        # Keep preferred cards
        for cid in hand:
            card = state.card_by_id(cid)
            if card and card.name in strategy.preferred_cards:
                continue  # Don't discard preferred

        # Discard avoided cards first
        for cid in hand:
            card = state.card_by_id(cid)
            if card and card.name in strategy.avoided_cards:
                return cid

        # Discard lowest priority card
        # Simple: discard last card
        return hand[-1] if hand else ""

    def choose_vampire_to_burn_blood(
        self,
        state: GameState,
        player_id: int,
        amount: int,
    ) -> str | None:
        """Choose vampire to burn blood from (e.g., for Villein)."""
        player = state.player_by_id(player_id)
        if not player:
            return None

        # Find vampire with most blood
        best = None
        best_blood = 0

        for cid in player.ready:
            card = state.card_by_id(cid)
            if (
                card
                and card.tipo.strip().lower() == "vampire"
                and card.blood > best_blood
            ):
                best = card
                best_blood = card.blood

        return best.id if best else None

    def record_action_outcome(
        self,
        state: GameState,
        player_id: int,
        action_type: str,
        outcome: str,
        card_name: str | None = None,
    ):
        """Record the outcome of an action for learning.
        
        Args:
            state: Current game state
            player_id: ID of the player
            action_type: Type of action taken
            outcome: 'success', 'fail', 'blocked', or 'cancelled'
            card_name: Name of card used (if any)
        """
        # Get strategic position
        analyzer = GameStateAnalyzer(state, player_id)
        strategic_position = analyzer.get_strategic_position(self.engine.threat_assessor)
        
        # Get game phase
        phase = self.engine.determine_game_phase(state, player_id)
        
        # Record the outcome
        self.learning.record_action(
            action_type=action_type,
            card_name=card_name,
            situation=strategic_position,
            outcome=outcome,
            phase=phase.value,
        )
        
        # Record for Q-Learning if enabled
        if self.use_rl and self.rl_agent:
            self._record_rl_outcome(state, player_id, action_type, outcome)
    
    def _record_rl_outcome(
        self,
        state: GameState,
        player_id: int,
        action_type: str,
        outcome: str,
    ) -> None:
        """Record outcome for Q-Learning agent."""
        try:
            # Calculate reward based on outcome
            reward_map = {
                'success': 0.3,
                'blocked': -0.1,
                'fail': -0.05,
                'cancelled': -0.05,
            }
            base_reward = reward_map.get(outcome, 0.0)
            
            # Adjust reward based on action type
            if action_type == 'bleed' and outcome == 'success':
                base_reward = 0.4  # Higher reward for successful bleed
            elif action_type == 'rush' and outcome == 'success':
                base_reward = 0.3
            elif action_type == 'oust' and outcome == 'success':
                base_reward = 1.0  # Maximum reward for ousting
            
            # Record the outcome
            encoder = StateEncoder(state, player_id)
            q_state = encoder.encode()
            
            self.rl_agent.update(
                self.deck_id,
                q_state,
                action_type,
                base_reward,
                q_state,  # Same state for now
                done=state.is_finished,
            )
        except Exception:
            pass

    def choose_card_to_play(
        self,
        state: GameState,
        player_id: int,
        action_type: str = 'bleed',
    ) -> str | None:
        """Choose which card to play from hand based on timing and knowledge.
        
        Args:
            state: Current game state
            player_id: ID of the player
            action_type: Type of action being attempted ('bleed', 'rush', etc.)
        
        Returns:
            Card ID to play, or None if no card should be played
        """
        player = state.player_by_id(player_id)
        if not player or not player.hand:
            return None
        
        # Use CardKnowledge for intelligent card selection
        knowledge = CardKnowledge(state, player_id)
        timing = CardTiming(state, player_id)
        
        # Get prioritized cards for this situation
        prioritized = knowledge.prioritize_cards_for_situation(action_type)
        
        # Return highest priority card that should be played
        for card, priority in prioritized:
            # Check if we should hold this card
            if knowledge.should_hold_card(card) and priority < 80:
                continue
            
            # Check by effect (from JSON)
            abilities = getattr(card, 'abilities', None) or []
            for ab in abilities:
                effects = getattr(ab, 'effects', None) or []
                for eff in effects:
                    func = getattr(eff, 'function', '')
                    
                    # Redirect bleed - only play against big bleeds
                    if func == 'reaction.redirect_bleed':
                        if player.pool <= 10:
                            return card.id
                        continue
            
            # Check by category (fallback)
            category = knowledge.get_card_category(card)
            
            if category == 'defense':
                if player.pool <= 10:
                    return card.id
                continue
            
            if category == 'stealth':
                if timing.should_play_stealth(action_type):
                    return card.id
                continue
            
            if category == 'modifier':
                if timing.should_play_modifier():
                    return card.id
                continue
            
            # Action cards - play based on action type
            tipo = card.tipo.strip().lower()
            if tipo == 'action':
                if action_type == 'bleed' and category == 'bleed':
                    return card.id
                if action_type == 'rush' and category == 'rush':
                    return card.id
                continue
            
            # Political actions
            if tipo == 'political action':
                return card.id
        
        return None

    def should_play_card(
        self,
        state: GameState,
        player_id: int,
        card_id: str,
        context: dict,
    ) -> bool:
        """Decide whether to play a specific card.
        
        Args:
            state: Current game state
            player_id: ID of the player
            card_id: ID of the card to play
            context: Additional context (e.g., {'bleed_amount': 3})
        
        Returns:
            True if card should be played
        """
        card = state.card_by_id(card_id)
        if not card:
            return False
        
        timing = CardTiming(state, player_id)
        knowledge = CardKnowledge(state, player_id)
        player = state.player_by_id(player_id)
        if not player:
            return False
        
        # Check by effect (from JSON)
        abilities = getattr(card, 'abilities', None) or []
        for ab in abilities:
            effects = getattr(ab, 'effects', None) or []
            for eff in effects:
                func = getattr(eff, 'function', '')
                
                # Redirect bleed
                if func == 'reaction.redirect_bleed':
                    bleed_amount = context.get('bleed_amount', 0)
                    return timing.should_play_redirect(bleed_amount)
        
        # Check by category (fallback)
        category = knowledge.get_card_category(card)
        
        if category == 'defense':
            bleed_amount = context.get('bleed_amount', 0)
            return timing.should_play_redirect(bleed_amount)
        
        if category == 'stealth':
            action_type = context.get('action_type', 'bleed')
            return timing.should_play_stealth(action_type)
        
        if category == 'modifier':
            return timing.should_play_modifier()
        
        # Default: play the card
        return True
    
    def observe_game_state(self, state: GameState) -> None:
        """Observe all players' vampires and cards for archetype recognition.
        
        This should be called at the start of each turn to observe:
        - Vampires in play (clans + disciplines)
        - Cards in ash heap
        - Actions taken by opponents
        """
        if not self.rl_agent:
            return
        
        for player in state.players:
            if player.id == self.deck_id or player.is_ousted:
                continue
            
            # Observe vampires in play
            if player.id not in self.observed_vampires:
                self.observed_vampires[player.id] = set()
            
            for vampire_id in player.crypt:
                if vampire_id in self.observed_vampires[player.id]:
                    continue
                
                vampire = state.card_by_id(vampire_id)
                if not vampire:
                    continue
                
                # Check if vampire is in play (ready or torpor)
                from gehenna_api.engine.card_instance import CardPosition
                if vampire.position not in (CardPosition.ready, CardPosition.torpor):
                    continue
                
                # Observe clan
                clan = getattr(vampire, 'clan', '') or ''
                if clan:
                    self.rl_agent.observe_clan(player.id, clan)
                
                # Observe disciplines
                disc_str = getattr(vampire, 'disciplines', '') or ''
                # Parse discipline string (e.g., '|dom|DOM|'
                discs = []
                for i in range(0, len(disc_str) - 1, 3):
                    if i + 1 < len(disc_str):
                        disc = disc_str[i:i+2].upper()
                        if disc.isalpha():
                            discs.append(disc)
                if discs:
                    self.rl_agent.observe_discipline(player.id, discs[0])
                
                self.observed_vampires[player.id].add(vampire_id)
    
    def observe_card_played(
        self,
        state: GameState,
        player_id: int,
        card_id: str,
    ) -> None:
        """Observe a card played by an opponent."""
        if not self.rl_agent or player_id == self.deck_id:
            return
        
        card = state.card_by_id(card_id)
        if card:
            self.rl_agent.observe_card(player_id, card.name)
    
    def observe_action_taken(
        self,
        state: GameState,
        player_id: int,
        action_type: str,
    ) -> None:
        """Observe an action taken by an opponent."""
        if not self.rl_agent or player_id == self.deck_id:
            return
        
        self.rl_agent.observe_action(player_id, action_type)


def create_strategy_bot(
    deck_id: int,
    strategies_dir: str | None = None,
) -> StrategyBot:
    """Create a strategy bot for a specific deck."""
    if strategies_dir is None:
        strategies_dir = str(
            Path(__file__).parent / "strategies"
        )
    return StrategyBot(deck_id=deck_id, strategies_dir=strategies_dir)
