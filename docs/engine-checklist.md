# V:TES Game Engine - Implementation Checklist

## Legend
- ✅ = Implemented
- 🔄 = Partially implemented
- ❌ = Not implemented

---

## 1. Game Setup
- ✅ 30 pool per player
- ✅ Blood bank (999,999)
- ✅ Edge starts uncontrolled
- ✅ Crypt/Library separation
- ✅ 7 cards drawn to hand
- ✅ 4 crypt cards to uncontrolled (face down/locked)
- ✅ First player gets Edge on first unlock

## 2. Turn Sequence
- ✅ Unlock phase
- ✅ Master phase
- ✅ Minion phase
- ✅ Influence phase
- ✅ Discard phase
- ✅ Turn advancement

## 3. Unlock Phase
- ✅ Unlock all ready cards
- ✅ Edge holder gains 1 pool
- ✅ Uncontrolled Edge granted to current player

## 4. Master Phase
- ✅ 1 master phase action (default)
- ✅ Play master card from hand
- ✅ Trifles (+1 action if first master played)
- ✅ Out-of-turn master card penalty (-1 action next turn)
- ❌ Master locations (permanent locations)
- ❌ Discipline cards (grant Disciplines to vampires)

## 5. Minion Phase

### 5.1 Basic Intrinsic Actions (no card required)
- ✅ Bleed (target: prey, stealth: 0, damage: 1 + card modifier)
- ✅ Hunt (mandatory if blood=0, stealth: +1, gain 1 blood)
- ✅ Leave Torpor (cost: 2 blood, move to ready)
- ✅ Rescue from Torpor (cost: 2 blood, target: vampire in torpor)
- ✅ Diablerie (steal blood, burn victim, +1 cap if victim older)

### 5.2 Action Card Actions (require card in hand)
- ✅ Equip (attach equipment, costs blood)
- ✅ Employ Retainer (attach retainer with life, costs blood)
- ✅ Recruit Ally (create ally in ready, locked first turn, costs blood)
- ✅ Political Action (call referendum, costs blood)

### 5.3 Action Resolution
- ✅ Announce action (lock acting minion)
- ✅ Action modifier phase (acting minion plays first)
- ✅ Block attempts (stealth vs intercept + reaction bonus)
- ✅ Directed actions: only target can block
- ✅ Undirected actions: prey first, then predator
- ✅ Block succeeds if intercept >= stealth
- ✅ Reaction phase (other Methuselahs can react)
- ✅ Combat on successful block
- ✅ Resolve action if not blocked

## 6. Combat System

### 6.1 Combat Initiation
- ✅ Combat on blocked action
- ✅ Only ready minions can participate
- ✅ Locked/unlocked doesn't matter for combat

### 6.2 Combat Sequence (7 steps per round)
- ✅ 1. Before Range (placeholder - combat cards pending)
- ✅ 2. Determine Range (close default, maneuvers change to long)
- ✅ 3. Before Strikes (placeholder - combat cards pending)
- ✅ 4. Strike (choose and resolve with first strike order)
- ✅ 5. Damage Resolution (mend with blood, aggravated damage)
- ️🔄 6. Press (ends after 1 round - press cards pending)
- ✅ 7. End of Round (placeholder)

### 6.3 Strike Effects
- ✅ Hand Strike (damage = strength, close range only)
- ✅ Dodge (0 damage, protects from opponent's strike, any range)
- ✅ Combat Ends (ends combat immediately, resolves first, any range)
- ✅ Steal Blood (transfers blood, not damage, any range)
- ✅ First Strike (resolves before normal strikes)
- ✅ Ranged Strike (works at any range)
- 🔄 Additional Strikes (extra strikes per round - needs cards)

### 6.4 Combat Cards
- ✅ Weapons (grant maneuvers via equipment attachments)
- 🔄 Maneuvers from cards (change range close ↔ long)
- ❌ Press cards (continue/end combat with cards)
- ❌ Damage Prevention cards (prevent damage)
- ❌ Additional Strike cards (extra strikes per round)

### 6.5 Damage Types
- ✅ Normal damage (mend with blood)
- ✅ Aggravated damage (cannot mend, burns wounded vampires)
- ❌ Environmental damage (cannot be dodged)
- ❌ Immune to damage

### 6.6 Damage Resolution
- ✅ Mend damage (burn 1 blood per point)
- ✅ Torpor (when damage > blood to mend)
- ✅ Burning (aggravated damage on wounded vampire)
- ❌ Damage prevention cards

## 7. Influence Phase
- ✅ Transfers (1/2/3/4 for first 4 turns, then 4)
- ✅ Add blood to uncontrolled vampires (1 transfer + 1 pool per blood)
- ✅ Move vampire from crypt to uncontrolled (4 transfers + 1 pool)
- ✅ Move vampire to ready when blood >= capacity

## 8. Discard Phase
- ✅ Discard down to 7 cards
- ✅ Event cards (1 per discard phase - placeholder)

## 9. Edge Mechanics
- ✅ Starts uncontrolled
- ✅ Granted on first unlock
- ✅ +1 pool during unlock
- ✅ Gained by successful bleed against predator
- ✅ Returns to uncontrolled on oust
- ❌ Can be burned for 1 vote (referendum)

## 10. Predator/Prey Relationships
- ✅ Prey = player to the left (counter-clockwise)
- ✅ Predator = player to the right (clockwise)
- ✅ Updates on oust
- ✅ 2-player game (each is prey/predator of the other)

## 11. Ousting and Victory
- ✅ Oust player (pool = 0)
- ✅ Predator gains 6 pool and 1 VP
- ✅ All ousted player's cards removed from game
- ✅ Edge returns to uncontrolled
- ✅ Prey relationships update
- ✅ Last survivor gets +1 VP
- ✅ Game ends when 1 player remains
- ✅ Final scores sorted by VP

## 12. Reaction Cards
- ✅ Played in response to actions
- ✅ Do not lock the minion playing them
- ✅ Only other Methuselahs' minions can play
- ✅ Can increase intercept (help block)
- ✅ Cost blood from ready minion
- ✅ Removed from hand to ash heap
- ❌ Reflex cards (cancel specific card types as played)

## 13. Action Modifier Cards
- ✅ Played by acting minion before resolution
- ✅ Can increase bleed, stealth
- ✅ Cost blood from acting minion
- ✅ Removed from hand to ash heap
- 🔄 One per action (simplified)

## 14. Political System
- ✅ Political Action cards (call referendum)
- ✅ Referendums (call, polling, resolve)
- ✅ Votes from titles (Primogen 1, Prince/Baron 2, Justicar 3, Inner Circle 4)
- ✅ Blood Hunt referendum (after diablerie)
- ❌ Votes from Edge (burn Edge for 1 vote)
- ❌ Votes from political action cards (1 vote each)

## 15. Titles
- ✅ Primogen (1 vote)
- ✅ Prince/Baron (2 votes)
- ✅ Justicar (3 votes)
- ✅ Inner Circle (4 votes)
- ❌ Contested titles (1 blood per unlock phase)
- ❌ Titled vampires (votes from ready titled minions)

## 16. Advanced Rules
- ❌ Advanced vampires (merge with base)
- ❌ Contested cards (1 pool per unlock phase)
- ❌ Unique cards/locations
- ❌ Red List (trophies)

## 17. Persistence
- ❌ Save game state to database
- ❌ Load game state from database
- ❌ Turn history log

## 18. CLI / Human Interface
- ✅ WebSocket endpoint (basic, from server.py)
- ❌ Human player input handling
- ❌ Game state visualization
- ❌ Action selection UI

## 19. Testing
- ✅ 131 unit tests passing
- ❌ Integration tests (full game simulation)
- ❌ Edge case tests

---

## Summary

| Category | Implemented | Total | Progress |
|---|---|---|---|
| Game Setup | 7 | 7 | 100% |
| Turn Sequence | 6 | 6 | 100% |
| Unlock Phase | 3 | 3 | 100% |
| Master Phase | 4 | 6 | 67% |
| Minion Phase (Basic) | 5 | 5 | 100% |
| Minion Phase (Cards) | 4 | 4 | 100% |
| Action Resolution | 9 | 9 | 100% |
| Combat System | 19 | 27 | 70% |
| Influence Phase | 4 | 4 | 100% |
| Discard Phase | 2 | 2 | 100% |
| Edge Mechanics | 5 | 6 | 83% |
| Predator/Prey | 4 | 4 | 100% |
| Ousting/Victory | 8 | 8 | 100% |
| Reaction Cards | 5 | 6 | 83% |
| Action Modifiers | 4 | 5 | 80% |
| Political System | 5 | 7 | 71% |
| Titles | 4 | 6 | 67% |
| Advanced Rules | 0 | 4 | 0% |
| Persistence | 0 | 3 | 0% |
| CLI/Interface | 1 | 4 | 25% |
| Testing | 1 | 3 | 33% |

**Overall Progress: ~75% (99/132 features)**

---

## Next Steps (Priority Order)

1. **Reflex Cards** - Cancel specific card types as played
2. **Advanced Rules** - Advanced vampires, contested cards, Red List
3. **Edge for Vote** - Burn Edge for 1 vote in referendum
4. **Persistence** - Save/load game state
5. **CLI/Human Interface** - Human player input
6. **Integration Tests** - Full game simulation
7. **Damage Prevention Cards** - Combat card subtype
8. **Additional Strike Cards** - Combat card subtype
9. **Press Cards** - Combat card subtype
10. **Master Locations/Disciplines** - Permanent master cards
