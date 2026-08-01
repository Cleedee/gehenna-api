"""State encoder for V:TES Q-Learning.

Converts game state to feature vector for the Q-Learning agent.
"""

from __future__ import annotations

from gehenna_api.engine.ai.q_learning import QState
from gehenna_api.engine.ai.capability_analyzer import CapabilityAnalyzer
from gehenna_api.engine.card_instance import CardPosition
from gehenna_api.engine.state import GameState


class StateEncoder:
    """Encodes game state into features for Q-Learning."""
    
    def __init__(self, state: GameState, player_id: int):
        self.state = state
        self.player_id = player_id
        self.player = state.player_by_id(player_id)
    
    def encode(self) -> QState:
        """Encode current game state into QState features."""
        if not self.player:
            return self._default_state()
        
        # Get prey and predator
        prey = self.state.prey_of(self.player_id)
        predator = self.state.predator_of(self.player_id)
        
        # Calculate basic features
        pool_ratio = self.player.pool / 30.0
        prey_pool_ratio = (prey.pool / 30.0) if prey else 0.5
        predator_pool_ratio = (predator.pool / 30.0) if predator else 0.5
        
        # Calculate threat levels
        own_threat = self._calculate_threat(self.player_id)
        prey_threat = self._calculate_threat(prey.id) if prey else 0.0
        predator_threat = self._calculate_threat(predator.id) if predator else 0.0
        
        # Game phase (0-1)
        phase = self._calculate_phase()
        
        # Minion count
        minion_count = self._count_ready_minions()
        
        # Hand size
        hand_size = len(self.player.hand)
        
        # Card availability
        has_bleed_card = 1 if self._has_card_type('bleed') else 0
        has_defense_card = 1 if self._has_card_type('defense') else 0
        has_rush_card = 1 if self._has_card_type('rush') else 0
        
        # New features: Analyze prey and predator capabilities
        prey_combat_module = 0  # 0=balanced, 1=defensive, 2=aggressive
        predator_combat_module = 0
        prey_bounce_prob = 0.0
        predator_bounce_prob = 0.0
        prey_intercept_prob = 0.0
        predator_intercept_prob = 0.0
        prey_combat_ends_prob = 0.0
        predator_combat_ends_prob = 0.0
        prey_aggravated_prob = 0.0
        predator_aggravated_prob = 0.0
        
        if prey:
            prey_analyzer = CapabilityAnalyzer(self.state, prey.id)
            prey_combat = prey_analyzer.analyze_combat_module()
            prey_reactions = prey_analyzer.analyze_reactions()
            prey_probs = prey_analyzer.calculate_card_probabilities()
            
            prey_combat_module = 1 if prey_combat.is_defensive else (2 if prey_combat.is_aggressive else 0)
            prey_bounce_prob = prey_reactions.bounce_probability
            prey_intercept_prob = prey_reactions.intercept_probability
            prey_combat_ends_prob = prey_probs.has_combat_ends
            prey_aggravated_prob = prey_probs.has_aggravated
        
        if predator:
            pred_analyzer = CapabilityAnalyzer(self.state, predator.id)
            pred_combat = pred_analyzer.analyze_combat_module()
            pred_reactions = pred_analyzer.analyze_reactions()
            pred_probs = pred_analyzer.calculate_card_probabilities()
            
            predator_combat_module = 1 if pred_combat.is_defensive else (2 if pred_combat.is_aggressive else 0)
            predator_bounce_prob = pred_reactions.bounce_probability
            predator_intercept_prob = pred_reactions.intercept_probability
            predator_combat_ends_prob = pred_probs.has_combat_ends
            predator_aggravated_prob = pred_probs.has_aggravated
        
        return QState(
            pool_ratio=pool_ratio,
            prey_pool_ratio=prey_pool_ratio,
            predator_pool_ratio=predator_pool_ratio,
            own_threat=own_threat,
            prey_threat=prey_threat,
            predator_threat=predator_threat,
            phase=phase,
            minion_count=minion_count,
            hand_size=hand_size,
            has_bleed_card=has_bleed_card,
            has_defense_card=has_defense_card,
            has_rush_card=has_rush_card,
            prey_combat_module=prey_combat_module,
            predator_combat_module=predator_combat_module,
            prey_bounce_prob=prey_bounce_prob,
            predator_bounce_prob=predator_bounce_prob,
            prey_intercept_prob=prey_intercept_prob,
            predator_intercept_prob=predator_intercept_prob,
            prey_combat_ends_prob=prey_combat_ends_prob,
            predator_combat_ends_prob=predator_combat_ends_prob,
            prey_aggravated_prob=prey_aggravated_prob,
            predator_aggravated_prob=predator_aggravated_prob,
        )
    
    def _default_state(self) -> QState:
        """Return default state when player not found."""
        return QState(
            pool_ratio=0.5,
            prey_pool_ratio=0.5,
            predator_pool_ratio=0.5,
            own_threat=0.0,
            prey_threat=0.0,
            predator_threat=0.0,
            phase=0.5,
            minion_count=0,
            hand_size=0,
            has_bleed_card=0,
            has_defense_card=0,
            has_rush_card=0,
            prey_combat_module=0,
            predator_combat_module=0,
            prey_bounce_prob=0.0,
            predator_bounce_prob=0.0,
            prey_intercept_prob=0.0,
            predator_intercept_prob=0.0,
            prey_combat_ends_prob=0.0,
            predator_combat_ends_prob=0.0,
            prey_aggravated_prob=0.0,
            predator_aggravated_prob=0.0,
        )
    
    def _calculate_threat(self, player_id: int) -> float:
        """Calculate threat level for a player (0-10)."""
        player = self.state.player_by_id(player_id)
        if not player:
            return 0.0
        
        score = 0.0
        
        # Pool threat
        if player.pool >= 20:
            score += 3.0
        elif player.pool >= 15:
            score += 1.5
        
        # Minion count
        ready_minions = self._count_player_minions(player_id)
        if ready_minions >= 3:
            score += 2.0
        elif ready_minions >= 2:
            score += 1.0
        
        # Victory points
        score += player.victory_points * 1.5
        
        return min(score, 10.0)
    
    def _count_player_minions(self, player_id: int) -> int:
        """Count ready minions for a player."""
        player = self.state.player_by_id(player_id)
        if not player:
            return 0
        
        count = 0
        for cid in player.crypt:
            card = self.state.card_by_id(cid)
            if (
                card
                and card.position == CardPosition.ready
                and card.tipo.strip().lower() in ('vampire', 'ally', 'imbued')
            ):
                count += 1
        return count
    
    def _count_ready_minions(self) -> int:
        """Count our ready minions."""
        return self._count_player_minions(self.player_id)
    
    def _calculate_phase(self) -> float:
        """Calculate game phase (0=early, 1=final)."""
        turn = self.state.turn_number
        alive = sum(1 for p in self.state.players if not p.is_ousted)
        
        # Early game (turns 1-5)
        if turn <= 5:
            return 0.0
        
        # Mid game (turns 6-15)
        if turn <= 15:
            return 0.5
        
        # Late game (turns 16+)
        if alive > 2:
            return 0.8
        
        # Final (2 players)
        return 1.0
    
    def _has_card_type(self, card_type: str) -> bool:
        """Check if we have a card of the specified type."""
        if not self.player:
            return False
        
        for cid in self.player.hand:
            card = self.state.card_by_id(cid)
            if not card:
                continue
            
            name_lower = card.name.lower()
            tipo_lower = card.tipo.strip().lower()
            
            if card_type == 'bleed':
                # Check for bleed cards
                if tipo_lower == 'action' and 'bleed' in name_lower:
                    return True
                # Check abilities for bleed effect
                abilities = getattr(card, 'abilities', None) or []
                for ab in abilities:
                    effects = getattr(ab, 'effects', None) or []
                    for eff in effects:
                        if 'bleed' in getattr(eff, 'function', ''):
                            return True
            
            elif card_type == 'defense':
                # Check for redirect/defense cards
                if tipo_lower == 'reaction':
                    abilities = getattr(card, 'abilities', None) or []
                    for ab in abilities:
                        effects = getattr(ab, 'effects', None) or []
                        for eff in effects:
                            if 'redirect' in getattr(eff, 'function', ''):
                                return True
            
            elif card_type == 'rush':
                # Check for rush cards
                abilities = getattr(card, 'abilities', None) or []
                for ab in abilities:
                    effects = getattr(ab, 'effects', None) or []
                    for eff in effects:
                        if 'rush' in getattr(eff, 'function', ''):
                            return True
        
        return False
