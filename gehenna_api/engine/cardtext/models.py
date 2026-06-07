from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ModifierType(str, Enum):
    bleed = 'bleed'
    strength = 'strength'
    stealth = 'stealth'
    intercept = 'intercept'
    capacity = 'capacity'
    damage = 'damage'
    life = 'life'
    hand_size = 'hand_size'
    transfers = 'transfers'
    vote = 'vote'


class DamageType(str, Enum):
    normal = 'normal'
    aggravated = 'aggravated'
    ranged = 'ranged'
    unpreventable = 'unpreventable'


class CostType(str, Enum):
    blood = 'blood'
    pool = 'pool'
    conviction = 'conviction'
    life = 'life'
    burn_card = 'burn_card'
    lock = 'lock'


class TriggerType(str, Enum):
    on_action = 'on_action'
    on_combat = 'on_combat'
    on_bleed = 'on_bleed'
    on_hunt = 'on_hunt'
    on_block = 'on_block'
    on_damage = 'on_damage'
    on_draw = 'on_draw'
    on_phase = 'on_phase'
    on_enter_play = 'on_enter_play'
    on_leave_play = 'on_leave_play'
    once_per_turn = 'once_per_turn'
    once_per_combat = 'once_per_combat'
    passive = 'passive'


class ActionType(str, Enum):
    bleed = 'bleed'
    hunt = 'hunt'
    recruit = 'recruit'
    equip = 'equip'
    influence = 'influence'
    combat = 'combat'
    diablerie = 'diablerie'
    rescue = 'rescue'
    special = 'special'
    political = 'political'


class Timing(str, Enum):
    before_range = 'before_range'
    after_range = 'after_range'
    before_strikes = 'before_strikes'
    after_strikes = 'after_strikes'
    end_of_round = 'end_of_round'
    during_combat = 'during_combat'
    during_action = 'during_action'
    during_master = 'during_master'
    during_minion = 'during_minion'
    during_influence = 'during_influence'
    during_discard = 'during_discard'


class CardEffect(BaseModel):
    trigger: TriggerType
    condition: str = ''
    cost: list[tuple[CostType, int]] = Field(default_factory=list)
    effect: str = ''
    modifiers: dict[ModifierType, int] = Field(default_factory=dict)
    timing: Optional[Timing] = None
    text: str = ''


class Ability(BaseModel):
    disciplines: list[str] = Field(default_factory=list)
    context: str = ''
    effects: list[CardEffect] = Field(default_factory=list)
    modifiers: dict[ModifierType, int] = Field(default_factory=dict)
    strike: Optional[StrikeEffect] = None
    text: str = ''


class StrikeEffect(BaseModel):
    damage: int = 0
    damage_type: DamageType = DamageType.normal
    steal_blood: int = 0
    manoeuvres: int = 0
    press: int = 0
    additional_strike: bool = False
    dodge: bool = False
    ends_combat: bool = False
    text: str = ''


class ParsedCard(BaseModel):
    name: str
    tipo: str
    sect: str = ''
    title: str = ''
    keywords: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)

    is_unique: bool = False
    is_weapon: bool = False
    is_gun: bool = False
    is_melee: bool = False
    is_ammo: bool = False
    is_electronic: bool = False
    is_event: bool = False
    is_master: bool = False
    is_action: bool = False
    is_reaction: bool = False
    is_combat: bool = False
    is_modifier: bool = False
    is_political: bool = False
    is_ally: bool = False
    is_retainer: bool = False
    is_equipment: bool = False

    cost_blood: int = 0
    cost_pool: int = 0
    cost_conviction: int = 0
    burn_value: str = ''

    default_strike: Optional[StrikeEffect] = None
    optional_manoeuvres: int = 0

    effects: list[CardEffect] = Field(default_factory=list)
    modifiers: dict[ModifierType, int] = Field(default_factory=dict)
    abilities: list[Ability] = Field(default_factory=list)

    raw_text: str = ''
