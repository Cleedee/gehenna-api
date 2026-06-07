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
- ❌ Political Action (call referendum)

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
- ✅ 1. Before Range (placeholder - no card play yet)
- ✅ 2. Determine Range (close default)
- ✅ 3. Before Strikes (placeholder - no card play yet)
- ✅ 4. Strike (choose and resolve)
- ✅ 5. Damage Resolution (mend with blood)
- ✅ 6. Press (simplified - ends after 1 round)
- ✅ 7. End of Round (placeholder)

### 6.3 Strike Effects
- ✅ Hand Strike (damage = strength, close range only)
- ✅ Dodge (no damage, protects from opponent's strike, any range)
- ✅ Combat Ends (ends combat immediately, resolves first, any range)
- ✅ Steal Blood (transfers blood, not damage, any range)
- ✅ First Strike (resolves before normal strikes; if only one, may kill before counter)
- ✅ Ranged Strike (works at any range)

### 6.4 Combat Cards
- ❌ Maneuvers (change range close ↔ long)
- ❌ Press (continue/end combat with cards)
- ❌ Damage Prevention (prevent damage with cards)
- ❌ Additional Strikes (extra strikes per round)
- ❌ Weapons (modify strikes)

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
- ✅ Transfers (1 on turn 1, 2 on turn 2, 3 on turn 3, 4 thereafter)
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
- ❌ Reflex cards (cancel specific card types)

## 13. Action Modifier Cards
- ✅ Played by acting minion before resolution
- ✅ Can increase bleed, stealth
- ✅ Cost blood from acting minion
- ✅ Removed from hand to ash heap
- ❌ Same card cannot be played twice per action (simplified: one per action)

## 14. Political System
- ❌ Political Action cards
- ❌ Referendums (call, polling, resolve)
- ❌ Votes (from titles, Edge, cards)
- ❌ Blood Hunt referendum (after diablerie)

## 15. Titles
- ❌ Primogen (1 vote)
- ❌ Prince/Baron (2 votes)
- ❌ Justicar (3 votes)
- ❌ Inner Circle (4 votes)
- ❌ Contested titles (1 blood per unlock phase)

## 16. Advanced Rules
- ❌ Advanced vampires (merge with base)
- ❌ Contested cards (1 pool per unlock phase)
- ❌ Unique cards/locations
- ❌ Trifle master cards (already in master phase)

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
- ✅ 115 unit tests passing
- ❌ Integration tests (full game simulation)
- ❌ Edge case tests

---

## Summary

| Category | Implemented | Total | Progress |
|---|---|---|---|
| Game Setup | 7 | 7 | 100% |
| Turn Sequence | 6 | 6 | 100% |
| Unlock Phase | 3 | 3 | 100% |
| Master Phase | 4 | 4 | 100% |
| Minion Phase (Basic) | 5 | 5 | 100% |
| Minion Phase (Cards) | 3 | 4 | 75% |
| Action Resolution | 9 | 9 | 100% |
| Combat System | 16 | 24 | 67% |
| Influence Phase | 4 | 4 | 100% |
| Discard Phase | 2 | 2 | 100% |
| Edge Mechanics | 5 | 6 | 83% |
| Predator/Prey | 4 | 4 | 100% |
| Ousting/Victory | 8 | 8 | 100% |
| Reaction Cards | 5 | 6 | 83% |
| Action Modifiers | 4 | 5 | 80% |
| Political System | 0 | 4 | 0% |
| Titles | 0 | 5 | 0% |
| Advanced Rules | 0 | 4 | 0% |
| Persistence | 0 | 3 | 0% |
| CLI/Interface | 1 | 4 | 25% |
| Testing | 1 | 3 | 33% |

**Overall Progress: ~70% (82/118 features)**

---

## Next Steps (Priority Order)

1. **Combat Cards** - Maneuvers, Press, Damage Prevention, Additional Strikes, Weapons
2. **Reflex Cards** - Cancel specific card types
3. **Political System** - Referendums, Blood Hunts
4. **Titles** - Prince, Baron, Justicar, Inner Circle
5. **Persistence** - Save/load game state
6. **CLI/Human Interface** - Human player input
7. **Integration Tests** - Full game simulation
