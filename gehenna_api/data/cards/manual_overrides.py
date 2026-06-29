"""
Manual overrides for card data that the automated parser couldn't extract.

Only cards used in simulation decks (241, 242, 244, 249) are included.
Cards with existing abilities/modifiers in their JSON file are NOT listed here.

Format: {codevdb: {field: value, ...}}

Priority groups for overrides creation:
1. COMBAT  — strike types, damage, maneuvers (critical for combat resolution)
2. EQUIPMENT — stealth, intercept, bleed bonuses (affects equip actions)
3. ACTION MODIFIER — bleed, stealth values (affects action resolution)
4. REACTION — intercept values (affects block attempts)
5. MASTER, POLITICAL ACTION, EVENT — mostly informational (no engine effect yet)
6. VAMPIRE — disciplines, special abilities (complex, lower priority)
"""

MANUAL_OVERRIDES = {
    # ═══════════════════════════════════════════════════════════════
    # COMBAT CARDS
    # ═══════════════════════════════════════════════════════════════

    # Earth Meld already has abilities — no override needed

    # Form of Mist already has abilities — no override needed

    # ═══════════════════════════════════════════════════════════════
    # ACTION MODIFIERS
    # ═══════════════════════════════════════════════════════════════

    102221: {  # Enchanting Gaze
        'modifiers': {},
        'abilities': [
            {
                'disciplines': ['dom'],
                'context': 'ACTION MODIFIER',
                'effects': [
                    {'function': 'modifier.stealth', 'params': {'value': 1},
                     'text': '+1 stealth.'},
                ],
            },
            {
                'disciplines': ['DOM'],
                'context': 'ACTION MODIFIER',
                'effects': [
                    {'function': 'modifier.stealth', 'params': {'value': 2},
                     'text': '+2 stealth.'},
                    {'function': 'modifier.bleed', 'params': {'value': 1},
                     'text': '+1 bleed.'},
                ],
            },
        ],
    },

    100687: {  # Faceless Night
        'modifiers': {'stealth': 2},
        'abilities': [
            {
                'disciplines': ['OBF'],
                'context': 'ACTION MODIFIER',
                'effects': [
                    {'function': 'modifier.stealth', 'params': {'value': 2},
                     'text': '+2 stealth.'},
                ],
            },
        ],
    },

    100769: {  # Forgotten Labyrinth
        'modifiers': {'stealth': 2},
        'abilities': [
            {
                'disciplines': ['ANI'],
                'context': 'ACTION MODIFIER',
                'effects': [
                    {'function': 'modifier.stealth', 'params': {'value': 2},
                     'text': '+2 stealth.'},
                ],
            },
        ],
    },

    102224: {  # Form of the Cobra — Action Modifier/Combat
        'modifiers': {'stealth': 1, 'strength': 1},
        'abilities': [
            {
                'disciplines': ['ser'],
                'context': 'ACTION MODIFIER',
                'effects': [
                    {'function': 'modifier.stealth', 'params': {'value': 1},
                     'text': '+1 stealth.'},
                ],
            },
            {
                'disciplines': ['SER'],
                'context': 'COMBAT',
                'effects': [
                    {'function': 'combat.strike', 'params': {
                        'strike_type': 'hand_strike',
                        'damage_type': 'aggravated',
                    }, 'text': 'Strike: hand strike at superior with aggravated damage.'},
                ],
            },
        ],
    },

    101125: {  # Lost in Crowds
        'modifiers': {'stealth': 2},
        'abilities': [
            {
                'disciplines': ['ANI'],
                'context': 'ACTION MODIFIER',
                'effects': [
                    {'function': 'modifier.stealth', 'params': {'value': 2},
                     'text': '+2 stealth.'},
                ],
            },
        ],
    },

    102233: {  # Revelation of the Serpent
        'modifiers': {},
        'abilities': [
            {
                'disciplines': ['SER'],
                'context': 'ACTION MODIFIER',
                'effects': [
                    {'function': 'modifier.bleed', 'params': {'value': 2},
                     'text': '+2 bleed.'},
                ],
            },
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # REACTIONS
    # ═══════════════════════════════════════════════════════════════

    102218: {  # Bait and Switch
        'modifiers': {'intercept': 1},
        'abilities': [
            {
                'disciplines': [],
                'context': 'REACTION',
                'effects': [
                    {'function': 'reaction.intercept', 'params': {'value': 1},
                     'text': '+1 intercept.'},
                ],
            },
        ],
    },

    100519: {  # Delaying Tactics
        'modifiers': {},
        'abilities': [
            {
                'disciplines': ['PRE'],
                'context': 'REACTION',
                'effects': [
                    {'function': 'reaction.delay', 'params': {},
                     'text': 'Cancel an action and put it on the bottom of the acting minion\'s library.'},
                ],
            },
        ],
    },

    100680: {  # Eyes of Argus
        'modifiers': {'intercept': 2},
        'abilities': [
            {
                'disciplines': ['AUS'],
                'context': 'REACTION',
                'effects': [
                    {'function': 'reaction.intercept', 'params': {'value': 2},
                     'text': '+2 intercept.'},
                ],
            },
        ],
    },

    101321: {  # On the Qui Vive
        'modifiers': {},
        'abilities': [
            {
                'disciplines': ['AUS'],
                'context': 'REACTION',
                'effects': [
                    {'function': 'reaction.unlock', 'params': {},
                     'text': 'A ready minion can attempt to block even if locked.'},
                ],
            },
        ],
    },

    101706: {  # Second Tradition: Domain
        'modifiers': {'intercept': 2},
        'abilities': [
            {
                'disciplines': [],
                'context': 'REACTION',
                'effects': [
                    {'function': 'reaction.intercept', 'params': {'value': 2},
                     'text': '+2 intercept.'},
                ],
            },
        ],
    },

    101949: {  # Telepathic Misdirection
        'modifiers': {},
        'abilities': [
            {
                'disciplines': ['AUS'],
                'context': 'REACTION',
                'effects': [
                    {'function': 'reaction.redirect_bleed', 'params': {},
                     'text': 'Redirect a bleed to another Methuselah.'},
                ],
            },
        ],
    },

    102231: {  # Party Out of Bounds
        'modifiers': {'intercept': 1},
        'abilities': [
            {
                'disciplines': [],
                'context': 'REACTION',
                'effects': [
                    {'function': 'reaction.intercept', 'params': {'value': 1},
                     'text': '+1 intercept.'},
                ],
            },
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # EQUIPMENT
    # ═══════════════════════════════════════════════════════════════

    100422: {  # Cooler
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'EQUIPMENT',
                'effects': [
                    {'function': 'equipment.blood_management', 'params': {},
                     'text': 'During your unlock phase, you may move a blood counter from this vampire to the blood bank or vice versa.'},
                ],
            },
        ],
    },

    100374: {  # Codex of the Edenic Groundskeepers
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'EQUIPMENT',
                'effects': [
                    {'function': 'equipment.bleed_bonus', 'params': {'value': 1},
                     'text': 'Bearer gets +1 bleed.'},
                ],
            },
        ],
    },

    100903: {  # Heart of Nizchetus
        'modifiers': {},
        'abilities': [
            {
                'disciplines': ['pro'],
                'context': 'EQUIPMENT',
                'effects': [
                    {'function': 'equipment.draw', 'params': {},
                     'text': 'Once each turn, the bearer may burn 1 blood to draw 1 card.'},
                ],
            },
        ],
    },

    100972: {  # Incriminating Videotape
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'EQUIPMENT',
                'effects': [
                    {'function': 'equipment.steal', 'params': {},
                     'text': 'Steal 1 pool from target Methuselah.'},
                ],
            },
        ],
    },

    101014: {  # Ivory Bow
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'COMBAT',
                'effects': [
                    {'function': 'combat.weapon', 'params': {
                        'damage': 1,
                        'damage_type': 'ranged',
                        'maneuver': 1,
                    }, 'text': 'Weapon: bow. Strike: 1R damage, with 1 optional maneuver.'},
                ],
            },
        ],
        'default_strike': [
            {'function': 'combat.strike', 'params': {
                'damage': 1,
                'damage_type': 'ranged',
            }, 'text': '1R damage'},
            {'function': 'combat.maneuver', 'params': {'value': 1},
             'text': '1 optional maneuver'},
        ],
    },

    101781: {  # Signet of King Saul, The
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'EQUIPMENT',
                'effects': [
                    {'function': 'equipment.bleed_bonus', 'params': {'value': 1},
                     'text': 'The bearer gets +1 bleed.'},
                ],
            },
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    100652: {  # Entrancement
        'modifiers': {},
        'abilities': [
            {
                'disciplines': ['dom'],
                'context': 'ACTION',
                'effects': [
                    {'function': 'action.steal_minion', 'params': {},
                     'text': 'Take control of a minion.'},
                ],
            },
        ],
    },

    100904: {  # Heart of the City
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'ACTION',
                'effects': [
                    {'function': 'action.bleed', 'params': {'value': 1},
                     'text': 'Bleed at +1 stealth.'},
                ],
            },
        ],
    },

    102232: {  # The Platinum Protocol
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'ACTION',
                'effects': [
                    {'function': 'action.bleed', 'params': {'value': 1},
                     'text': 'Bleed action.'},
                ],
            },
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # POLITICAL ACTIONS
    # ═══════════════════════════════════════════════════════════════

    100605: {  # Eat the Rich
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.burn_minion', 'params': {},
                     'text': 'Burn a minion.'},
                ],
            },
        ],
    },

    100131: {  # Banishment
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.burn_minion', 'params': {},
                     'text': 'Burn a vampire.'},
                ],
            },
        ],
    },

    101056: {  # Kine Resources Contested
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.pool_bonus', 'params': {},
                     'text': 'Gain pool.'},
                ],
            },
        ],
    },

    101353: {  # Parity Shift
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.pool_shift', 'params': {},
                     'text': 'Shift pool between Methuselahs.'},
                ],
            },
        ],
    },

    101417: {  # Political Stranglehold
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.block_actions', 'params': {},
                     'text': 'No minion can act.'},
                ],
            },
        ],
    },

    101663: {  # Rumors of Gehenna
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.pool_burn', 'params': {},
                     'text': 'All Methuselahs lose pool.'},
                ],
            },
        ],
    },

    100059: {  # Anarchist Uprising
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.anarch', 'params': {},
                     'text': 'Anarch effect.'},
                ],
            },
        ],
    },

    100065: {  # Ancilla Empowerment
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.bonus', 'params': {},
                     'text': 'Ancilla bonus.'},
                ],
            },
        ],
    },

    102270: {  # Camarilla's Iron Fist
        'modifiers': {},
        'abilities': [
            {
                'disciplines': [],
                'context': 'POLITICAL ACTION',
                'effects': [
                    {'function': 'political.burn', 'params': {},
                     'text': 'Burn a Camarilla vampire.'},
                ],
            },
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # MASTERS  (mostly informational for now — engine handles masters generically)
    # ═══════════════════════════════════════════════════════════════

    # Masters are played generically in the engine (pay cost, put in ash heap).
    # The overrides below are for future use when specific master effects are implemented.

    101238: {  # Monastery of Shadows (permanent, location)
        'modifiers': {},
        'master_type': 'permanent',
        'abilities': [
            {'disciplines': [], 'context': 'MASTER',
             'effects': [
                 {'function': 'master.hand_size', 'params': {'value': 1},
                  'text': '+1 hand size (permanent).'},
             ]},
        ],
    },

    100588: {  # Dreams of the Sphinx (permanent)
        'modifiers': {},
        'master_type': 'permanent',
        'abilities': [
            {'disciplines': [], 'context': 'MASTER',
             'effects': [{'function': 'master.draw', 'params': {},
                          'text': 'Draw 1 card during your master phase.'}]},
        ],
    },

    102121: {  # Villein (Trifle, attached to vampire)
        'modifiers': {},
        'master_type': 'attached',
        'abilities': [
            {'disciplines': [], 'context': 'MASTER',
             'effects': [
                 {'function': 'master.blood', 'params': {'min_blood': 2},
                  'text': 'Put this card on a vampire you control and move 2+ blood to your pool.'},
                 {'function': 'master.minion_tap_penalty', 'params': {},
                  'text': 'Minion Tap cards cost an additional pool on this vampire.'},
                 {'function': 'master.play_cost_penalty', 'params': {'extra_pool': 1},
                  'text': 'Villein costs an additional pool to play on this vampire.'},
             ]},
        ],
    },

    101896: {  # Sudden Reversal
        'modifiers': {},
        'abilities': [
            {'disciplines': [], 'context': 'MASTER',
             'effects': [{'function': 'master.cancel', 'params': {},
                          'text': 'Cancel a card just played (as it is played).'}]},
        ],
    },

    102180: {  # Wider View
        'modifiers': {},
        'abilities': [
            {'disciplines': [], 'context': 'MASTER',
             'effects': [{'function': 'master.draw', 'params': {'value': 1},
                          'text': 'Draw 1 additional card.'}]},
        ],
    },

    100297: {  # Carfax Abbey
        'modifiers': {},
        'abilities': [
            {'disciplines': [], 'context': 'MASTER',
             'effects': [{'function': 'master.pool', 'params': {},
                          'text': 'Add 1 pool.'}]},
        ],
    },

    100809: {  # Garibaldi-Meucci Museum
        'modifiers': {},
        'abilities': [
            {'disciplines': [], 'context': 'MASTER',
             'effects': [{'function': 'master.transfer', 'params': {},
                          'text': 'Gain +1 transfer.'}]},
        ],
    },

    # ═══════════════════════════════════════════════════════════════
    # VAMPIRES — Special Abilities
    # ═══════════════════════════════════════════════════════════════

    201411: {  # The Unnamed (G6) — Baali, 10 cap
        'disciplines': ['CEL', 'DAI', 'OBF', 'PRE', 'PRO'],
        'special_effects': [
            'strike_blood_for_aggravated',
            'bleed_gain_pool',
        ],
    },
}
