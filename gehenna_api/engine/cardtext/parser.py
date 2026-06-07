from __future__ import annotations

import re
from typing import Optional

from gehenna_api.engine.cardtext.models import (
    Ability,
    CardEffect,
    DamageType,
    ModifierType,
    ParsedCard,
    StrikeEffect,
    Timing,
    TriggerType,
)

KNOWN_CONTEXTS = frozenset({
    'COMBAT', 'ACTION', 'ACTION MODIFIER', 'REACTION',
    'MASTER', 'POLITICAL ACTION',
})

ABILITY_RE = re.compile(
    r'\[([^\]]+)\](?:\[([^\]]+)\])?\s*'
    r'(?:\[(COMBAT|ACTION|ACTION MODIFIER|REACTION|MASTER|POLITICAL ACTION)\]\s*)?'
    r'(.+)',
    re.IGNORECASE,
)


def _parse_modifiers(text: str) -> dict[ModifierType, int]:
    mods = {}
    patterns = [
        (r'\+(\d+)\s*bleed', ModifierType.bleed),
        (r'bleed\s+for\s+(\d+)', ModifierType.bleed),
        (r'\+(\d+)\s*strength', ModifierType.strength),
        (r'\+(\d+)\s*stealth', ModifierType.stealth),
        (r'\+(\d+)\s*intercept', ModifierType.intercept),
        (r'-(\d+)\s*stealth', ModifierType.stealth),
        (r'-(\d+)\s*intercept', ModifierType.intercept),
    ]
    for pattern, mtype in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            if '-' in pattern and '+' not in pattern:
                val = -val
            mods[mtype] = mods.get(mtype, 0) + val
    return mods


def _parse_strike(text: str) -> Optional[StrikeEffect]:
    strike = StrikeEffect()

    # Pattern: "Strike: XR damage" or "XR damage each strike"
    m = re.search(r'(\d+)\s*R?\s*damage', text, re.IGNORECASE)
    if m:
        # Skip if "prevent" precedes the digit
        before = text[: m.start()]
        if not re.search(r'prevent\s*$', before, re.IGNORECASE):
            strike.damage = int(m.group(1))
            if 'aggravated' in text.lower():
                strike.damage_type = DamageType.aggravated
            if 'R' in m.group(0) or 'ranged' in text.lower():
                strike.damage_type = DamageType.ranged

    # Pattern: "strength+N damage"
    m = re.search(r'strength\+(\d+)\s*damage', text, re.IGNORECASE)
    if m:
        strike.damage = int(m.group(1))
        if 'aggravated' in text.lower() or 'agg' in text.lower():
            strike.damage_type = DamageType.aggravated

    # Pattern: "optional maneuver each combat" or standalone "Maneuver."
    if re.search(r'(optional\s+)?maneuver', text, re.IGNORECASE):
        strike.manoeuvres = 1

    # Pattern: "optional additional strike"
    if 'optional additional strike' in text.lower():
        strike.additional_strike = True

    # Pattern: "steals X blood" or "steal X blood"
    m = re.search(r'steal[s]?\s*(\d+)\s*blood', text, re.IGNORECASE)
    if m:
        strike.steal_blood = int(m.group(1))

    # Pattern: "dodge"
    if re.search(r'\bdodge\b', text, re.IGNORECASE):
        strike.dodge = True

    # Pattern: "combat ends"
    if re.search(r'combat ends', text, re.IGNORECASE):
        strike.ends_combat = True

    if (
        strike.damage > 0
        or strike.steal_blood > 0
        or strike.manoeuvres > 0
        or strike.press > 0
        or strike.additional_strike
        or strike.dodge
        or strike.ends_combat
    ):
        strike.text = text
        return strike
    return None


def _parse_timing(text: str) -> Optional[Timing]:
    mapping = [
        (r'before range is determined', Timing.before_range),
        (r'after range is determined', Timing.after_range),
        (r'before strikes', Timing.before_strikes),
        (r'end of (the\s+)?round', Timing.end_of_round),
        (r'during your master phase', Timing.during_master),
        (r'during your minion phase', Timing.during_minion),
        (r'during your influence phase', Timing.during_influence),
        (r'during your discard phase', Timing.during_discard),
        (r'during.*action', Timing.during_action),
        (r'during.*combat', Timing.during_combat),
    ]
    for pattern, timing in mapping:
        if re.search(pattern, text, re.IGNORECASE):
            return timing
    return None


def _parse_sect_title(text: str) -> tuple[str, str]:
    sect_map = {
        'Camarilla': 'Camarilla',
        'Sabbat': 'Sabbat',
        'Independent': 'Independent',
        'Laibon': 'Laibon',
        'Anarch': 'Anarch',
    }
    title_map = {
        'primogen': 'primogen',
        'prince': 'prince',
        'justicar': 'justicar',
        'inner circle': 'inner_circle',
        'archbishop': 'archbishop',
        'bishop': 'bishop',
        'cardinal': 'cardinal',
        'baron': 'baron',
    }

    sect_found = ''
    title_found = ''

    for sname, sval in sect_map.items():
        if text.startswith(sname + ':') or text.startswith(sname + ' '):
            sect_found = sval
            break

    if not sect_found:
        for sname, sval in sect_map.items():
            if sname in text:
                sect_found = sval
                break

    for tname, tval in title_map.items():
        pattern = rf'\b{re.escape(tname)}\b'
        if re.search(pattern, text, re.IGNORECASE):
            title_found = tval
            break

    return sect_found, title_found


def _parse_traits(text: str) -> list[str]:
    known_traits = [
        'Unique',
        'Sterile',
        'Scarce',
        'Red List',
        'Black Hand',
        'Blood Cursed',
        'Flight',
        'Infernal',
        'Slave',
    ]
    found = []
    for trait in known_traits:
        pattern = rf'(?<!\w)(?:non-)?{re.escape(trait)}(?!\w)'
        if (
            re.search(pattern, text, re.IGNORECASE)
            and 'non-' not in text.lower()
        ):
            found.append(trait)
    return found


def _parse_actions(text: str) -> list[tuple[str, str, int]]:
    """Extract (action_desc, action_type, cost_blood) tuples."""
    results = []
    # Pattern: "as a (D) action" or "as a +N stealth action"
    m = re.search(
        r'as a \+?(\d+)?\s*stealth\s+\(?D\)?\s*action', text, re.IGNORECASE
    )
    if m:
        stealth = int(m.group(1)) if m.group(1) else 0
        results.append(('directed_action', 'directed', stealth))
    return results


def _parse_effects(text: str, parsed: ParsedCard) -> list[CardEffect]:
    effects = []
    remaining = text

    # Remove sect/title prefix for effect parsing
    if parsed.sect:
        # Remove "Camarilla:" or "Sabbat archbishop:" style prefixes
        remaining = re.sub(
            rf'^{re.escape(parsed.sect)}\s*.*?:?\s*',
            '',
            remaining,
            flags=re.IGNORECASE,
        )
        remaining = re.sub(
            rf'^{re.escape(parsed.sect)}\s+',
            '',
            remaining,
            flags=re.IGNORECASE,
        )
    # Remove standalone sect at start
    remaining = re.sub(
        r'^(Camarilla|Sabbat|Independent|Laibon|Anarch)[.\s]*', '', remaining
    )

    # Modifiers at end of text (like "+1 bleed")
    mods = _parse_modifiers(remaining)
    if mods:
        parsed.modifiers.update(mods)
        # Remove from remaining
        for mtype in mods:
            remaining = re.sub(
                rf'[+-]\d+\s*{re.escape(mtype.value)}',
                '',
                remaining,
                flags=re.IGNORECASE,
            )

    # "gets +N stealth" style
    m = re.search(r'gets?\s*\+?(\d+)\s+(\w+)', remaining, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        kind = m.group(2).lower()
        kind_map = {
            'stealth': ModifierType.stealth,
            'intercept': ModifierType.intercept,
            'bleed': ModifierType.bleed,
            'strength': ModifierType.strength,
        }
        if kind in kind_map:
            parsed.modifiers[kind_map[kind]] = (
                parsed.modifiers.get(kind_map[kind], 0) + val
            )

    # "can prevent N damage" -> damage reduction
    m = re.search(r'prevent\s*(\d+)\s*damage', remaining, re.IGNORECASE)
    if m:
        effects.append(
            CardEffect(
                trigger=TriggerType.on_damage,
                effect='prevent_damage',
                modifiers={ModifierType.damage: -int(m.group(1))},
                text=m.group(0),
            )
        )

    # "once each turn" effects
    m = re.search(
        r'once each turn[.,]?\s*(.*?)(?:[.]+|$)', remaining, re.IGNORECASE
    )
    if m:
        effect_text = m.group(1).strip()
        effects.append(
            CardEffect(
                trigger=TriggerType.once_per_turn,
                text=effect_text,
                effect=effect_text,
            )
        )

    # "once each combat" effects
    m = re.search(
        r'once each combat[.,]?\s*(.*?)(?:[.]+|$)', remaining, re.IGNORECASE
    )
    if m:
        effect_text = m.group(1).strip()
        effects.append(
            CardEffect(
                trigger=TriggerType.once_per_combat,
                text=effect_text,
                effect=effect_text,
            )
        )

    # "If X, Y" conditions
    for m in re.finditer(
        r'If\s+(.+?),\s*(.+?)(?:[.]+|$)', remaining, re.IGNORECASE
    ):
        effects.append(
            CardEffect(
                trigger=TriggerType.passive,
                condition=m.group(1).strip(),
                effect=m.group(2).strip(),
                text=m.group(0).strip(),
            )
        )

    # "When X, Y" triggers
    for m in re.finditer(
        r'When\s+(.+?),\s*(.+?)(?:[.]+|$)', remaining, re.IGNORECASE
    ):
        effects.append(
            CardEffect(
                trigger=TriggerType.on_action,
                condition=m.group(1).strip(),
                effect=m.group(2).strip(),
                text=m.group(0).strip(),
            )
        )

    # "During X phase, Y"
    for m in re.finditer(
        r'(During your \w+ phase)[.,]?\s*(.*?)(?:[.]+|$)',
        remaining,
        re.IGNORECASE,
    ):
        timing = _parse_timing(m.group(1))
        effects.append(
            CardEffect(
                trigger=TriggerType.on_phase,
                timing=timing,
                effect=m.group(2).strip(),
                text=m.group(0).strip(),
            )
        )

    # "can/may X" abilities
    for m in re.finditer(r'may\s+(.+?)(?:[.]+|$)', remaining, re.IGNORECASE):
        eff_text = m.group(1).strip()
        # Skip if already captured by more specific patterns
        if not any(e.text == eff_text for e in effects):
            effects.append(
                CardEffect(
                    trigger=TriggerType.on_action,
                    effect=eff_text,
                    text=eff_text,
                )
            )

    return effects


def _parse_keywords(text: str) -> list[str]:
    kws = []
    # Type keywords
    type_kw = [
        'weapon',
        'gun',
        'melee weapon',
        'electronic equipment',
    ]
    for kw in type_kw:
        if re.search(rf'\b{re.escape(kw)}\b', text, re.IGNORECASE):
            kws.append(kw)

    return kws


def _extract_abilities(
    text: str, default_context: str = ''
) -> tuple[list[Ability], str]:
    abilities = []
    non_ability_lines = []

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        m = ABILITY_RE.match(line)
        if m:
            discs = [m.group(1)]
            if m.group(2):
                discs.append(m.group(2))
            context = m.group(3)
            if context:
                context = context.upper()
            else:
                context = default_context.upper() if default_context else ''
            effect_text = m.group(4).strip()
            abilities.append(
                Ability(disciplines=discs, context=context, text=effect_text)
            )
        else:
            non_ability_lines.append(line)

    return abilities, '\n'.join(non_ability_lines)


def _populate_ability_effects(ability: Ability) -> None:
    text = ability.text

    mods = _parse_modifiers(text)
    if mods:
        ability.modifiers.update(mods)

    strike = _parse_strike(text)
    if strike:
        ability.strike = strike

    effects: list[CardEffect] = []

    if re.search(r'put this card on', text, re.IGNORECASE):
        effects.append(
            CardEffect(
                trigger=TriggerType.on_action,
                effect='equip_self',
                text='put this card on this vampire',
            )
        )

    m = re.search(r'Only usable at ([^.]+)', text, re.IGNORECASE)
    if m:
        effects.append(
            CardEffect(
                trigger=TriggerType.passive,
                condition=f'only usable at {m.group(1).lower()}',
                effect='restrict_use',
                text=m.group(0).strip(),
            )
        )

    if re.search(r'damage.*is aggravated', text, re.IGNORECASE):
        effects.append(
            CardEffect(
                trigger=TriggerType.passive,
                effect='damage_aggravated',
                text='Damage is aggravated',
            )
        )

    if re.search(r'unlock this vampire', text, re.IGNORECASE):
        effects.append(
            CardEffect(
                trigger=TriggerType.on_action,
                effect='unlock',
                text='unlock this vampire',
            )
        )

    for m in re.finditer(
        r'If\s+(.+?),\s*(.+?)(?:[.]+|$)', text, re.IGNORECASE
    ):
        effects.append(
            CardEffect(
                trigger=TriggerType.passive,
                condition=m.group(1).strip(),
                effect=m.group(2).strip(),
                text=m.group(0).strip(),
            )
        )

    for m in re.finditer(
        r'(?:may|can)\s+(.+?)(?:[.]+|$)', text, re.IGNORECASE
    ):
        eff_text = m.group(1).strip().rstrip(')')
        if not any(e.effect == eff_text for e in effects):
            effects.append(
                CardEffect(
                    trigger=TriggerType.on_action,
                    effect=eff_text,
                    text=eff_text,
                )
            )

    ability.effects = effects


def parse_card_text(
    name: str,
    tipo: str,
    text: str,
    disciplines: str = '',
) -> ParsedCard:
    parsed = ParsedCard(name=name, tipo=tipo, raw_text=text)

    if tipo == 'vampire':
        parsed.sect, parsed.title = _parse_sect_title(text)
        parsed.traits = _parse_traits(text)
        parsed.effects = _parse_effects(text, parsed)
        return parsed

    # Library card parsing
    parsed.keywords = _parse_keywords(text)
    parsed.traits = _parse_traits(text)
    parsed.is_unique = bool(
        re.search(r'(?<!\w)(?:non-)?Unique(?!\w)', text, re.IGNORECASE)
        and 'non-unique' not in text.lower()
    )
    parsed.is_weapon = 'weapon' in text.lower()
    parsed.is_gun = 'gun' in text.lower()
    parsed.is_melee = 'melee' in text.lower()
    parsed.is_electronic = 'electronic' in text.lower()

    # Extract abilities (e.g., "[pro] [COMBAT] ...")
    default_context = tipo.replace('_', ' ').upper() if tipo != 'vampire' else ''
    abilities, remaining = _extract_abilities(text, default_context)
    if abilities:
        parsed.abilities = abilities
        for ab in abilities:
            _populate_ability_effects(ab)

    # Strike parsing (from non-ability text)
    strike = _parse_strike(remaining)
    if strike:
        parsed.default_strike = strike

    # "optional maneuver each combat"
    if re.search(r'optional maneuver', remaining, re.IGNORECASE):
        parsed.optional_manoeuvres = 1

    # Effects from non-ability text
    parsed.effects = _parse_effects(remaining, parsed)

    # Aggregate ability effects into flat lists for backward compat
    for ab in parsed.abilities:
        parsed.effects.extend(ab.effects)
        for k, v in ab.modifiers.items():
            parsed.modifiers[k] = parsed.modifiers.get(k, 0) + v

    return parsed
