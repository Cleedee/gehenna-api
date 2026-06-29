"""Registry for card playability in game windows (impulse system).

Maps card names to their playable windows and effects.
Also maps effect names to their handler methods.

This is the canonical source of truth for which cards can be played
in which impulse windows during action resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CardPlayability:
    """Defines in which game windows a card can be played and its effect."""

    windows: list[str]
    """Game windows where this card can be played, e.g. ['as_announced', 'before_resolution']."""

    conditions: dict[str, Any] = field(default_factory=dict)
    """Additional conditions for playability, e.g. {'action_type': 'bleed'}.

    Supported condition keys:
    - 'action_type': str or tuple of str — required action type(s)
    - 'is_directed': bool — whether action must be directed or undirected
    - 'minion_has_discipline': str — discipline the acting minion must have
    """

    effect: str = ''
    """Name of the effect to execute when played. Matches WINDOW_EFFECTS_REGISTRY."""

    cost_type: str = 'pool'
    """Type of cost: 'pool' (paid by Methuselah) or 'blood' (paid by minion)."""

    cost_amount: int = 1
    """Amount of pool or blood to pay when playing the card."""


@dataclass
class WindowEffect:
    """Defines a handler for a window effect."""

    handler: str
    """Name of the method on PhaseManager that handles this effect."""

    description: str = ''
    """Human-readable description of what the effect does."""


# =============================================================================
# CARD PLAYABILITY REGISTRY
# =============================================================================
# Maps card name -> CardPlayability
# Cards not in this registry use heuristic rules based on tipo/master_type.

CARD_PLAYABILITY_REGISTRY: dict[str, CardPlayability] = {
    'Direct Intervention': CardPlayability(
        windows=['as_announced', 'before_resolution'],
        conditions={'action_type': ('political', 'action_card')},
        effect='cancel_action',
        cost_type='pool',
        cost_amount=1,
    ),
    'Deflection': CardPlayability(
        windows=['before_resolution'],
        conditions={},
        effect='redirect_bleed',
        cost_type='blood',
        cost_amount=1,
    ),
    'Delaying Tactics': CardPlayability(
        windows=['before_resolution'],
        conditions={'action_type': 'political'},
        effect='cancel_political',
        cost_type='blood',
        cost_amount=1,
    ),
    'On the Qui Vive': CardPlayability(
        windows=['block_attempt'],
        conditions={},
        effect='wake_minion',
    ),
    'Wake with Evening\'s Freshness': CardPlayability(
        windows=['block_attempt'],
        conditions={},
        effect='wake_minion',
    ),
}
#     conditions={'minion_has_discipline': 'ser'},
#     effect='bleed_modifier',
# ),

# =============================================================================
# WINDOW EFFECTS REGISTRY
# =============================================================================
# Maps effect name -> WindowEffect
# These are the handler methods on PhaseManager that execute card effects.

WINDOW_EFFECTS_REGISTRY: dict[str, WindowEffect] = {
    'cancel_action': WindowEffect(
        handler='_apply_cancel_action',
        description='Cancel the current action. Card goes to bottom of library.',
    ),
    'stealth_modifier': WindowEffect(
        handler='_apply_stealth_modifier',
        description='Add stealth to the acting minion.',
    ),
    'intercept_reaction': WindowEffect(
        handler='_apply_intercept_reaction',
        description='Add intercept to the blocking minion.',
    ),
    'bleed_modifier': WindowEffect(
        handler='_apply_bleed_modifier',
        description='Add bleed to the acting minion.',
    ),
    'redirect_bleed': WindowEffect(
        handler='_apply_redirect_bleed',
        description='Redirect a bleed to another Methuselah.',
    ),
    'cancel_political': WindowEffect(
        handler='_apply_cancel_political',
        description='Cancel a political action/referendum.',
    ),
    'wake_minion': WindowEffect(
        handler='_apply_wake_minion',
        description='Wake a minion so it can block or play reactions.',
    ),
    'grant_intercept': WindowEffect(
        handler='_apply_grant_intercept',
        description='Grant intercept to a minion attempting to block.',
    ),
}


def get_card_playability(card_name: str) -> CardPlayability | None:
    """Look up a card's playability in the registry."""
    return CARD_PLAYABILITY_REGISTRY.get(card_name)


def get_window_effect(effect_name: str) -> WindowEffect | None:
    """Look up a window effect handler."""
    return WINDOW_EFFECTS_REGISTRY.get(effect_name)
