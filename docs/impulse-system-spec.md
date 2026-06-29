# Sistema de Impulso (Impulse) — Especificação de Redesign

> **Referências:** Regras do V:TES — `docs/rules/03-card-types-library.md` (Sequencing, p.8), `docs/rules/13-glossary.md` (Impulse, p.41), `docs/rules/07-minion-phase-actions.md` (Action Resolution, p.23–25)
>
> **Código atual:** `gehenna_api/engine/phases.py` — `_minion_action()`, `_resolve_block_attempts()`, `_play_reactions()`, `_play_action_modifiers()`

---

## 1. Visão Geral

### 1.1 Problema

O motor atual não implementa o conceito de **Impulso** (Impulse) do V:TES. A resolução de ações é feita com chamadas de métodos em ordem fixa e hardcoded, sem um ciclo generalizado de "quem quer jogar algo?". Isso impede a implementação correta de:

- Cartas reativas (Deflection, Wake, Eagle's Sight, Delaying Tactics)
- Out-of-turn master cards (Direct Intervention já é ad-hoc, mas não escala)
- Múltiplos modificadores de stealth/reactions no mesmo bloqueio
- Ciclo de impulso com recuperação para o Methuselah ativo

### 1.2 Objetivo

Implementar um sistema de **janelas de jogo** (game windows) com **ciclo de impulso** (impulse cycle) que:

1. Permita que qualquer Methuselah jogue cartas no momento apropriado
2. Siga a ordem de impulso das regras: ativo → defensor/presa → predador → todos em ordem horária
3. Recupere o impulso para o ativo após cada carta jogada
4. Suporte todos os tipos de carta: action modifiers, reactions, out-of-turn masters, reflex cards
5. Seja extensível para novas cartas sem modificar o core engine

---

## 2. Arquitetura

### 2.1 Game Windows

Uma **Game Window** é um ponto no fluxo de resolução onde cartas podem ser jogadas. Cada janela tem:

- **Nome**: identificador único
- **Ator primário**: quem age primeiro (acting minion, blocking minion, etc.)
- **Ordem de impulso**: a sequência em que o impulso passa
- **Contexto**: dados disponíveis para decisão (action_info, combat_info, etc.)
- **Cartas elegíveis**: quais tipos/cartas podem ser jogadas nesta janela

#### Hierarquia de Janelas

```
TURN FLOW
├── UNLOCK PHASE (sem janelas)
├── MASTER PHASE (sem janelas — o ativo joga masters normalmente)
├── MINION PHASE
│   ├── [WINDOW] antes de qualquer ação (cartas de início de fase)
│   └── Para cada minion:
│       └── ACTION RESOLUTION
│           ├── [WINDOW] as_announced — "as the action is announced"
│           │   ├── Wake effects
│           │   ├── Direct Intervention (out-of-turn master)
│           │   └── Reflex cards
│           ├── [WINDOW] before_block — antes de tentar bloquear
│           │   └── Action modifiers (stealth)
│           ├── [WINDOW] block_attempt — durante tentativa de bloqueio
│           │   ├── Stealth modifiers (acting minion)
│           │   ├── Intercept reactions (blocking minion)
│           │   └── Wake (para acordar minions para bloquear)
│           ├── [WINDOW] after_blocks — após todos os bloqueios (ação bem-sucedida)
│           │   ├── Action modifiers (bleed, outros)
│           │   └── "other than acting minion" modifiers
│           ├── [WINDOW] before_resolution — antes de resolver
│           │   ├── Reactions (Deflection, outros)
│           │   ├── Direct Intervention (out-of-turn master)
│           │   └── Delaying Tactics (political action cancel)
│           └── [WINDOW] resolution — resolve a ação (sem cartas)
│
├── INFLUENCE PHASE (sem janelas — transferências simples)
└── DISCARD PHASE (sem janelas)

COMBAT RESOLUTION
├── [WINDOW] combat_before_range
├── [WINDOW] combat_range
├── [WINDOW] combat_before_strikes
├── [WINDOW] combat_strike
├── [WINDOW] combat_damage
├── [WINDOW] combat_press
└── [WINDOW] combat_end

REFERENDUM RESOLUTION
├── [WINDOW] referendum_declared
├── [WINDOW] referendum_votes
└── [WINDOW] referendum_resolution
```

### 2.2 Ciclo de Impulso

O ciclo de impulso é o mecanismo central que processa cada janela:

```
FUNCTION process_impulse_window(window, context):
    
    order = calculate_impulse_order(window, context)
    # Para ação dirigida a 1: [acting, target]
    # Para ação não-dirigida: [acting, prey, predator, rest...]
    # Para combate: [attacker, defender]
    
    passed_players = set()
    current_idx = 0
    
    WHILE len(passed_players) < len(order):
        current_player = order[current_idx]
        
        IF current_player.id in passed_players:
            current_idx = (current_idx + 1) % len(order)
            CONTINUE
        
        cards = get_playable_cards(current_player, window, context)
        
        IF cards:
            card = choose_card(cards, current_player, context)
            play_card(card, current_player, context)
            passed_players.clear()
            # Reset: ativo recupera impulso
            current_idx = 0
        ELSE:
            passed_players.add(current_player.id)
            current_idx = (current_idx + 1) % len(order)
    
    # Todos passaram — janela fechada
    RETURN True se alguma carta foi jogada, senão False
```

#### Ordem de Impulso por Tipo de Janela

| Janela | Ordem de Impulso |
|---|---|
| `as_announced` | Ativo → presa → predador → demais em ordem horária |
| `before_block` | Ativo → (apenas modificadores do ativo) |
| `block_attempt` | Ativo → bloqueador → ativo → bloqueador → ... |
| `after_blocks` | Ativo → (apenas action modifiers) |
| `before_resolution` | Ativo → presa → predador → demais em ordem horária |
| `combat_*` | Atacante → defensor → atacante → defensor → ... |

### 2.3 Card Playability por Janela

Cada carta precisa declarar em quais janelas ela pode ser jogada e sob quais condições. Isso é feito via um campo novo em `CardInstance` ou via um registry central:

```python
class CardPlayability:
    """Define em quais janelas uma carta pode ser jogada."""
    windows: list[str]              # Ex: ['as_announced', 'before_resolution']
    conditions: dict[str, Any]      # Condições adicionais (ex: 'action_type': 'bleed')
    cost: Callable | None           # Custo dinâmico (opcional)
    effect: str                     # Nome do efeito a executar
```

#### Registry de Cartas Jogáveis por Janela

```python
# CardPlayability Registry
# Mapeia nome_da_carta -> CardPlayability

CARD_PLAYABILITY_REGISTRY = {
    'Direct Intervention': CardPlayability(
        windows=['as_announced', 'before_resolution'],
        conditions={'action_type': ('political', 'action_card')},
        effect='cancel_action',
    ),
    'Deflection': CardPlayability(
        windows=['before_resolution'],
        conditions={'action_type': 'bleed', 'is_directed': True},
        effect='redirect_bleed',
    ),
    'Wake': CardPlayability(
        windows=['as_announced', 'block_attempt', 'before_resolution'],
        conditions={},
        effect='wake_minion',
    ),
    'On the Qui Vive': CardPlayability(
        windows=['block_attempt'],
        conditions={},
        effect='wake_minion',
    ),
    'Delaying Tactics': CardPlayability(
        windows=['before_resolution'],
        conditions={'action_type': 'political'},
        effect='cancel_political',
    ),
    'Eagle\'s Sight': CardPlayability(
        windows=['block_attempt'],
        conditions={},
        effect='grant_intercept',
    ),
    'Form of the Bat': CardPlayability(
        windows=['as_announced', 'block_attempt', 'after_blocks'],
        conditions={'minion_has_discipline': 'ANI'},
        effect='stealth_modifier',  # ou maneuver em combate
    ),
    'Earth Control': CardPlayability(
        windows=['block_attempt'],
        conditions={'minion_has_discipline': 'pro'},
        effect='stealth_modifier',
    ),
    'Spying Mission': CardPlayability(
        windows=['block_attempt'],
        conditions={},
        effect='stealth_modifier',
    ),
    'Party Out Of Bounds': CardPlayability(
        windows=['block_attempt'],
        conditions={'action_type': 'action_card'},
        effect='intercept_reaction',
    ),
    'Revelation of the Serpent': CardPlayability(
        windows=['after_blocks'],
        conditions={'minion_has_discipline': 'ser'},
        effect='bleed_modifier',
    ),
}
```

Para cartas sem entrada no registry (a maioria), o sistema usa heurísticas baseadas no `tipo` da carta:
- `tipo == 'action_modifier'` → windows `['block_attempt', 'after_blocks']`
- `tipo == 'reaction'` → windows `['block_attempt', 'before_resolution']`
- `master_type == 'reaction'` → windows `['as_announced', 'before_resolution']`

---

## 3. Especificação Detalhada

### 3.1 Novos Campos no CardInstance

```python
class CardInstance(BaseModel):
    # ... campos existentes ...

    # NOVOS CAMPOS
    playable_windows: list[str] = []
    """Janelas onde esta carta pode ser jogada. Se vazio, usa heurística do tipo."""
    
    impulse_priority: int = 0
    """Prioridade dentro da mesma janela (maior = jogada primeiro, 0 = normal)."""
    
    out_of_turn: bool = False
    """Se True, é uma out-of-turn master card."""
```

### 3.2 Novos Campos no PlayerState

```python
class PlayerState(BaseModel):
    # ... campos existentes ...

    # NOVOS CAMPOS
    out_of_turn_played_this_cycle: bool = False
    """Já jogou uma out-of-turn master entre seus turnos? (reset no próprio unlock phase)"""
    
    master_actions_penalty: int = 0
    """Quantas master phase actions perderá no próximo turno por out-of-turn cards."""
```

### 3.3 Engine Integration — PhaseManager

```python
class PhaseManager:
    # ... métodos existentes ...

    # NOVO MÉTODO PRINCIPAL
    def _process_window(
        self,
        window: str,
        acting_player: PlayerState,
        context: dict,
        bots: dict[int, Bot],
    ) -> bool:
        """Processa uma janela de impulso."""
        order = self._get_impulse_order(window, context)
        passed = set()
        idx = 0
        
        while len(passed) < len(order):
            player = order[idx]
            if player.id in passed:
                idx = (idx + 1) % len(order)
                continue
            
            playables = self._get_playable_cards(player, window, context, bots)
            
            if playables:
                card = self._choose_card_for_window(player, playables, window, context, bots)
                self._execute_card_in_window(card, player, window, context)
                passed.clear()
                # Ativo recupera impulso
                idx = 0
            else:
                passed.add(player.id)
                idx = (idx + 1) % len(order)
        
        return True  # janela processada

    def _get_impulse_order(self, window: str, context: dict) -> list[PlayerState]:
        """Calcula ordem de impulso para a janela."""
        acting = context.get('acting_player')
        target = context.get('target_player')
        prey = self.state.prey_of(acting.id)
        pred = self.state.predator_of(acting.id)
        
        window_orders = {
            'as_announced': self._order_all_from_acting,
            'before_block': lambda ctx: [acting],  # só o ativo
            'block_attempt': lambda ctx: self._order_block_attempt(ctx),
            'after_blocks': lambda ctx: [acting],  # só o ativo
            'before_resolution': self._order_all_from_acting,
        }
        
        if window in window_orders:
            return window_orders[window](context)
        return [acting]

    def _order_all_from_acting(self, context: dict) -> list[PlayerState]:
        """Retorna [acting, prey, pred, rest...] em ordem horária."""
        acting = context.get('acting_player')
        if not acting:
            return []
        result = [acting]
        # Percorre a mesa em ordem horária a partir de acting
        current = self.state.prey_of(acting.id)
        seen = {acting.id}
        while current and current.id not in seen:
            result.append(current)
            seen.add(current.id)
            current = self.state.prey_of(current.id)
        return result

    def _get_playable_cards(
        self,
        player: PlayerState,
        window: str,
        context: dict,
        bots: dict[int, Bot],
    ) -> list[CardInstance]:
        """Retorna cartas na mão do jogador que podem ser jogadas nesta janela."""
        playables = []
        
        for cid in player.hand:
            card = self.state.card_by_id(cid)
            if not card:
                continue
            
            if not self._can_play_in_window(card, window, context):
                continue
            
            if not self._can_afford_card(card, player, context):
                continue
            
            # Verificar restrições específicas da carta
            if not self._check_card_conditions(card, window, context):
                continue
            
            playables.append(card)
        
        return playables

    def _can_play_in_window(self, card: CardInstance, window: str, context: dict) -> bool:
        """Verifica se a carta pode ser jogada nesta janela."""
        # 1. Verificar registry
        registry = CARD_PLAYABILITY_REGISTRY.get(card.name)
        if registry:
            return window in registry.windows
        
        # 2. Verificar playable_windows do CardInstance
        if card.playable_windows:
            return window in card.playable_windows
        
        # 3. Heurística por tipo
        tipo_key = card.tipo.strip().lower()
        if window == 'block_attempt':
            if tipo_key in ('action_modifier', 'action modifier'):
                # Action modifiers com stealth podem ser jogados durante bloqueio
                return card.stealth > 0
            if tipo_key == 'reaction':
                # Reactions com intercept podem ser jogadas durante bloqueio
                return card.intercept > 0
            if card.name == 'Wake':  # nome específico (registry é melhor)
                return True
        
        if window == 'after_blocks':
            if tipo_key in ('action_modifier', 'action modifier'):
                return True  # Modifiers sem stealth podem ser jogados pós-bloqueio
        
        if window == 'before_resolution':
            if tipo_key == 'reaction':
                return True  # Qualquer reaction pode ser jogada antes da resolução
        
        # Out-of-turn masters com master_type 'reaction'
        if window in ('as_announced', 'before_resolution'):
            if getattr(card, 'master_type', None) == 'reaction':
                return True
        
        return False

    def _check_card_conditions(
        self,
        card: CardInstance,
        window: str,
        context: dict,
    ) -> bool:
        """Verifica condições específicas para jogar a carta."""
        registry = CARD_PLAYABILITY_REGISTRY.get(card.name)
        if not registry:
            return True
        
        for key, value in registry.conditions.items():
            if key == 'action_type':
                action_type = context.get('action_type')
                if isinstance(value, tuple):
                    if action_type not in value:
                        return False
                elif action_type != value:
                    return False
            
            if key == 'is_directed':
                if context.get('is_directed') != value:
                    return False
            
            if key == 'minion_has_discipline':
                disc = value
                minion = context.get('minion')
                if not minion or not self._minion_has_discipline(minion, disc):
                    return False
        
        return True

    def _execute_card_in_window(
        self,
        card: CardInstance,
        player: PlayerState,
        window: str,
        context: dict,
    ) -> None:
        """Executa o efeito de uma carta jogada em uma janela."""
        # Pagar custo
        self._pay_card_cost(card, player, context)
        
        # Remover da mão
        if card.id in player.hand:
            player.hand.remove(card.id)
        
        # Registrar no log
        action_name = f'{card.name} ({window})'
        self._log_action(player, f'{player.username} plays {action_name}')
        
        # Executar efeito baseado no tipo da janela/efeito
        effect_name = self._get_card_effect(card)
        self._resolve_window_effect(effect_name, card, player, context)
        
        # Posicionar carta
        if getattr(card, 'master_type', None) == 'reaction':
            # Out-of-turn masters vão para bottom of library
            card.position = CardPosition.bottom_of_library
            # Rastrear penalidade
            self._track_out_of_turn_master(player, card)
        else:
            card.position = CardPosition.ash_heap
        
        # Emitir evento
        self.events.emit(GameEvent(
            type=EventType.card_played,
            player_id=player.id,
            data={'card': card.name, 'window': window},
        ))
```

### 3.4 Out-of-Turn Master Cards — Lógica Completa

```python
# NOVAS REGRAS para out-of-turn master cards

def _can_play_out_of_turn_master(
    self,
    card: CardInstance,
    player: PlayerState,
    context: dict,
) -> bool:
    """Verifica se o jogador pode jogar uma out-of-turn master card."""
    # 1. Não pode jogar no próprio turno
    current_player = self.state.current_player
    if current_player and current_player.id == player.id:
        return False
    
    # 2. Só pode jogar uma entre seus turnos
    if player.out_of_turn_played_this_cycle:
        return False
    
    # 3. Precisa ter pool para pagar (1 por padrão)
    cost = card.pool_cost if card.pool_cost > 0 else 1
    if player.pool < cost:
        return False
    
    return True


def _track_out_of_turn_master(
    self,
    player: PlayerState,
    card: CardInstance,
) -> None:
    """Registra que o jogador jogou uma out-of-turn master."""
    player.out_of_turn_played_this_cycle = True
    player.master_actions_penalty += 1


def _reset_out_of_turn_tracking(self, player: PlayerState) -> None:
    """Reseta o tracking de out-of-turn no unlock phase do jogador."""
    player.out_of_turn_played_this_cycle = False
    # A penalidade é aplicada DURANTE o master phase, não aqui
```

#### Integração no Master Phase

```python
def execute_master(self, bots: dict[int, Bot]) -> None:
    player = self.state.current_player
    if not player or self.state.is_finished:
        return
    
    # Aplicar penalidade de out-of-turn cards
    base_actions = 1
    effective_actions = max(0, base_actions - player.master_actions_penalty)
    player.master_actions = effective_actions
    player.master_actions_penalty = 0  # reset após aplicar
    
    bot = bots.get(player.id)
    if bot:
        self._player_master_phase(player, bot)
```

---

## 4. Fluxo de Resolução de Ação — Novo

### 4.1 Código Novo (`_minion_action` refatorado)

```python
def _minion_action(self, minion, player, bot, bots=None):
    if minion.has_acted_this_turn:
        return
    
    action_type = bot.choose_action_type(self.state, player.id, minion.id)
    action_info = self._get_action_info(action_type, minion, player)
    
    # Preparar contexto compartilhado para as janelas
    context = {
        'minion': minion,
        'acting_player': player,
        'action_type': action_type,
        'action_info': action_info,
        'is_directed': action_info.get('directed', False),
    }
    
    # ==========================================
    # JANELA 1: "as the action is announced"
    # ==========================================
    # Anunciar ação primeiro (sempre acontece)
    self._log_action(player, f'{minion.name} announces {action_info["name"]}')
    minion.lock()
    
    # Processar janela "as_announced" — aqui entra Direct Intervention, Wake, etc.
    self._process_window('as_announced', player, context, bots or {})
    
    # Se a ação foi cancelada (ex: Direct Intervention), parar
    if context.get('cancelled'):
        minion.unlock()
        minion.has_acted_this_turn = False
        return
    
    # ==========================================
    # JANELA 2: before_block — action modifiers
    # ==========================================
    # O ativo pode jogar action modifiers (stealth) antes de qualquer
    # tentativa de bloqueio
    self._process_window('before_block', player, context, bots or {})
    
    # ==========================================
    # JANELA 3: block_attempt — loop de bloqueio
    # ==========================================
    blocked, blocker = self._resolve_block_attempts_v2(
        minion, player, action_info, bot, context, bots or {}
    )
    
    if blocked:
        self._log_action(player, f'{action_info["name"]} blocked by {blocker.name}')
        self._start_combat(minion, blocker)
        minion.has_acted_this_turn = True
        return
    
    # ==========================================
    # JANELA 4: after_blocks — action modifiers
    # ==========================================
    # O ativo pode jogar action modifiers (bleed, etc.) após bloqueios
    self._process_window('after_blocks', player, context, bots or {})
    
    # ==========================================
    # JANELA 5: before_resolution — reactions
    # ==========================================
    # Qualquer Methuselah pode jogar reactions
    self._process_window('before_resolution', player, context, bots or {})
    
    if context.get('cancelled'):
        minion.unlock()
        minion.has_acted_this_turn = False
        return
    
    # ==========================================
    # RESOLUÇÃO
    # ==========================================
    if '_action_card' in action_info:
        action_info['resolve'](minion, player, bot, action_info)
    else:
        action_info['resolve'](minion, player, bot)
    
    minion.has_acted_this_turn = True
```

### 4.2 `_resolve_block_attempts_v2` — Com Ciclo de Impulso

```python
def _resolve_block_attempts_v2(
    self,
    minion: CardInstance,
    player: PlayerState,
    action_info: dict,
    bot: Bot,
    context: dict,
    bots: dict[int, Bot],
) -> tuple[bool, Optional[CardInstance]]:
    """Resolve bloqueios com ciclo de impulso entre ativo e bloqueador."""
    
    # Determinar bloqueadores potenciais (mesmo que antes)
    potential_blockers = self._get_potential_blockers(player, action_info)
    
    acting_stealth = action_info['stealth']
    
    for blocker in potential_blockers:
        blocker_player = self.state.player_by_id(
            self._player_id_for_minion(blocker)
        )
        if not blocker_player:
            continue
        
        # Verificar se o bloqueador tem chance de bloquear
        if not self._can_potentially_block(blocker, blocker_player, acting_stealth):
            continue
        
        # Bot decide se tenta bloquear
        should_block = bot.choose_block(self.state, blocker_player.id, minion.id)
        if not should_block:
            continue
        
        # --- CICLO DE IMPULSO NO BLOQUEIO ---
        # Ordem: ativo → bloqueador → ativo → bloqueador → ... até ambos passarem
        
        block_context = {
            **context,
            'blocker': blocker,
            'blocker_player': blocker_player,
        }
        
        self._process_window('block_attempt', player, block_context, bots)
        
        # Recalcular após as janelas
        acting_stealth = action_info['stealth'] + action_info.get('modifier_stealth', 0)
        blocker_intercept = blocker.intercept + action_info.get('reaction_intercept', 0)
        
        if blocker_intercept >= acting_stealth:
            blocker.lock()
            return True, blocker
        else:
            self._log_action(
                blocker_player,
                f'{blocker.name} fails to block {minion.name} '
                f'(intercept {blocker_intercept} < stealth {acting_stealth})'
            )
    
    return False, None
```

---

## 5. Efeitos de Janela — Implementação

### 5.1 Registry de Efeitos

```python
WINDOW_EFFECTS_REGISTRY = {
    'stealth_modifier': {
        'handler': '_apply_stealth_modifier',
        'context_key': 'modifier_stealth',
    },
    'intercept_reaction': {
        'handler': '_apply_intercept_reaction',
        'context_key': 'reaction_intercept',
    },
    'bleed_modifier': {
        'handler': '_apply_bleed_modifier',
        'context_key': 'bleed_bonus',
    },
    'cancel_action': {
        'handler': '_apply_cancel_action',
        'context_key': 'cancelled',
    },
    'cancel_political': {
        'handler': '_apply_cancel_political',
        'context_key': 'cancelled',
    },
    'redirect_bleed': {
        'handler': '_apply_redirect_bleed',
        'context_key': 'redirect_target',
    },
    'wake_minion': {
        'handler': '_apply_wake_minion',
        'context_key': None,
    },
    'grant_intercept': {
        'handler': '_apply_grant_intercept',
        'context_key': 'reaction_intercept',
    },
}
```

### 5.2 Handlers de Efeito

```python
def _apply_stealth_modifier(self, card, player, context):
    """Aplica +stealth ao minion ativo."""
    context['modifier_stealth'] = context.get('modifier_stealth', 0) + card.stealth
    card.position = CardPosition.ash_heap
    minion = context.get('minion')
    if minion and card.pool_cost > 0:
        minion.blood -= card.pool_cost


def _apply_intercept_reaction(self, card, player, context):
    """Aplica +intercept ao bloqueador."""
    context['reaction_intercept'] = context.get('reaction_intercept', 0) + card.intercept
    card.position = CardPosition.ash_heap
    blocker = context.get('blocker')
    if blocker and card.pool_cost > 0:
        blocker.blood -= card.pool_cost


def _apply_cancel_action(self, card, player, context):
    """Cancela a ação atual."""
    context['cancelled'] = True
    card.position = CardPosition.bottom_of_library
    if card.pool_cost > 0:
        player.pool -= card.pool_cost


def _apply_wake_minion(self, card, player, context):
    """Acorda um minion para reagir/bloquear."""
    card.position = CardPosition.ash_heap
    # Marca o jogador como "acordado" para esta ação
    context['woke_players'] = context.get('woke_players', set())
    context['woke_players'].add(player.id)
    # Na prática, o motor precisa permitir que minions locked ajam como
    # se estivessem unlocked durante a ação


def _apply_redirect_bleed(self, card, player, context):
    """Redireciona um bleed para outro Methuselah."""
    # Lógica complexa — escolher novo alvo
    card.position = CardPosition.ash_heap
    # Marcar no contexto para o resolver usar o novo alvo
    context['redirect_to'] = self._choose_redirect_target(player, context)
```

---

## 6. Migração — Plano de Implementação

### Fase 1: Fundação (sem quebrar nada existente)

1. **Adicionar campos aos models**
   - `CardPosition.bottom_of_library` ✅ (já feito)
   - `PlayerState.out_of_turn_played_this_cycle` (novo)
   - `PlayerState.master_actions_penalty` (novo)
   - `CardInstance.playable_windows` (novo)
   - `CardInstance.out_of_turn` (novo)

2. **Criar registry de janelas e efeitos**
   - `CARD_PLAYABILITY_REGISTRY` (dict global)
   - `WINDOW_EFFECTS_REGISTRY` (dict global)

3. **Implementar `_process_window()` base**
   - Método que itera jogadores em ordem de impulso
   - Chama `_get_playable_cards()` para cada jogador
   - Se joga carta, executa efeito e reseta ciclo

4. **Implementar `_get_playable_cards()`**
   - Verifica registry, depois `playable_windows`, depois heurística por tipo

**Testes:** 130 testes existentes continuam passando (nada muda ainda)

### Fase 2: Integração Gradual

1. **Substituir `_check_direct_intervention()` por janela `as_announced`**
   - Adicionar Direct Intervention ao `CARD_PLAYABILITY_REGISTRY`
   - Remover o `if` específico em `_minion_action()` (ou mantê-lo como fallback)
   - Testar simulação com Direct Intervention

2. **Substituir `_play_stealth_modifiers()` + `_play_block_reactions()` por janela `block_attempt`**
   - Action modifiers com stealth viram `CARD_PLAYABILITY_REGISTRY` entries
   - Reactions com intercept viram entries
   - `_process_window('block_attempt')` substitui os métodos específicos

3. **Substituir `_play_action_modifiers()` por janela `after_blocks`**
   - Action modifiers sem stealth (ou com bleed) viram entries

4. **Substituir `_play_reactions()` por janela `before_resolution`**
   - Todas as reactions (não só intercept) podem ser jogadas aqui
   - Funciona para todos os action_types, não só bleed

**Testes:** Após cada substituição, rodar simulação e verificar se o comportamento é idêntico ou melhor

### Fase 3: Out-of-Turn Masters

1. **Implementar `_can_play_out_of_turn_master()`**
   - Verificar `out_of_turn_played_this_cycle`
   - Verificar se não é o próprio turno

2. **Integrar no `_process_window()`**
   - Quando uma out-of-turn master é jogada, chamar `_track_out_of_turn_master()`

3. **Aplicar penalidade no master phase**
   - `player.master_actions = max(0, base - player.master_actions_penalty)`

4. **Reset no unlock phase**
   - `player.out_of_turn_played_this_cycle = False`

**Testes:** Simular com Direct Intervention confirmando que a penalidade de master action funciona

### Fase 4: Novas Cartas

1. **Implementar Wake/On the Qui Vive**
   - Efeito `wake_minion`: permite que minions locked ajam como unlocked durante a ação
   - Adicionar suporte no motor: durante `block_attempt` e `before_resolution`, minions locked com wake podem jogar reactions

2. **Implementar Deflection**
   - Efeito `redirect_bleed`: muda o alvo do bleed para outro Methuselah
   - Modificar `_resolve_bleed_action()` para usar `context['redirect_to']`

3. **Implementar Delaying Tactics**
   - Efeito `cancel_political`: similar a cancel_action, mas só para referendums

4. **Adicionar cartas aos decks de teste**
   - Incluir estas cartas nos decks da simulação

**Testes:** Simulações específicas para cada carta

---

## 7. Testes

### 7.1 Testes Unitários

```python
# tests/test_impulse_system.py

def test_process_window_as_announced():
    """Verifica que a janela as_announced processa Direct Intervention."""

def test_process_window_block_attempt():
    """Verifica ciclo stealth → intercept → stealth → ..."""

def test_impulse_order_undirected():
    """Ordem: ativo → presa → predador → demais."""

def test_impulse_order_directed():
    """Ordem: ativo → alvo → demais."""

def test_impulse_back_to_active():
    """Após alguém jogar carta, ativo recupera impulso."""

def test_out_of_turn_master_tracking():
    """Verifica out_of_turn_played_this_cycle e master_actions_penalty."""

def test_out_of_turn_not_on_own_turn():
    """Não pode jogar out-of-turn no próprio turno."""

def test_out_of_turn_one_per_cycle():
    """Só pode jogar uma out-of-turn entre seus turnos."""

def test_cancel_action_unlocks_minion():
    """Direct Intervention cancela ação e destrava minion."""

def test_wake_allows_block():
    """Wake permite que minion locked bloqueie."""
```

### 7.2 Testes de Simulação

```python
# Simulações específicas
def test_direct_intervention_on_action_card():
    """Direct Intervention cancela Enchant Kindred."""

def test_direct_intervention_on_political():
    """Direct Intervention cancela referendum."""

def test_deflection_redirects_bleed():
    """Deflection redireciona bleed para outro Methuselah."""

def test_wake_then_block():
    """Wake acorda minion que então bloqueia."""

def test_multiple_stealth_modifiers():
    """Múltiplos stealth modifiers no mesmo bloqueio."""

def test_out_of_turn_penalty_applied():
    """Penalidade de master action é aplicada no próximo turno."""
```

---

## 8. Impacto nos Arquivos Existentes

| Arquivo | Mudança |
|---|---|
| `engine/card_instance.py` | + `playable_windows`, `out_of_turn`, `impulse_priority` |
| `engine/state.py` → `PlayerState` | + `out_of_turn_played_this_cycle`, `master_actions_penalty` |
| `engine/phases.py` | Refatorar `_minion_action`, `_resolve_block_attempts`, `_play_*` métodos |
| `engine/phases.py` (novos) | `_process_window`, `_get_impulse_order`, `_get_playable_cards`, `_can_play_in_window`, `_check_card_conditions`, `_execute_card_in_window` |
| `engine/phases.py` (efeitos) | `_apply_stealth_modifier`, `_apply_intercept_reaction`, `_apply_cancel_action`, etc. |
| `engine/engine.py` | Reset de `out_of_turn_played_this_cycle` no unlock phase |
| `data/cards/impulse_registry.py` (novo) | `CARD_PLAYABILITY_REGISTRY`, `WINDOW_EFFECTS_REGISTRY` |
| `data/cards/overrides/*.json` | Novos overrides com `playable_windows` para cartas reativas |

---

## 9. Considerações de Design

### 9.1 Performance

O ciclo de impulso pode iterar várias vezes por janela se vários jogadores jogarem cartas. Para evitar loops infinitos:

```python
MAX_IMPULSE_ROUNDS_PER_WINDOW = 50  # Safety limit

def _process_window(self, window, acting_player, context, bots):
    rounds = 0
    # ... loop ...
    while len(passed) < len(order):
        rounds += 1
        if rounds > MAX_IMPULSE_ROUNDS_PER_WINDOW:
            self._log_action(None, f'[WARNING] Impulse window {window} timed out')
            break
        # ...
```

### 9.2 Decisões do Bot

O bot precisa de um método novo para decidir qual carta jogar em cada janela:

```python
class Bot:
    # ... métodos existentes ...
    
    def choose_card_for_window(
        self,
        state: GameState,
        player_id: int,
        cards: list[CardInstance],
        window: str,
        context: dict,
    ) -> Optional[str]:  # retorna card.id ou None
        """Escolhe qual carta jogar em uma janela de impulso."""
        # Implementação padrão: sempre joga a primeira carta disponível
        # Bots mais avançados podem analisar contexto
        if cards:
            return cards[0].id
        return None
```

### 9.3 Extensibilidade

Para adicionar uma nova carta reativa ao jogo:

```python
# 1. Criar override JSON
{
    "playable_windows": ["before_resolution"],
    "effects": [{"function": "reaction.redirect_bleed", ...}]
}

# 2. OU adicionar ao registry (se precisar de lógica complexa)
CARD_PLAYABILITY_REGISTRY['New Card'] = CardPlayability(
    windows=['before_resolution'],
    conditions={'action_type': 'bleed'},
    effect='redirect_bleed',
)

# 3. Se o efeito é novo, criar handler
def _apply_new_effect(self, card, player, context):
    # ... implementação ...
    pass
```

---

## 10. Glossário

| Termo | Definição |
|---|---|
| **Janela (Game Window)** | Ponto no fluxo de resolução onde cartas podem ser jogadas |
| **Impulso (Impulse)** | Direito de jogar a próxima carta ou efeito |
| **Ordem de Impulso** | Sequência de jogadores que recebem o impulso |
| **Ciclo de Impulso** | Iteração: ativo → próximo → ... → todos passam → fecha janela |
| **Recuperação de Impulso** | Se alguém joga uma carta, o ativo recupera o impulso |
| **Out-of-Turn Master** | Master card jogada no turno de outro jogador, usando uma master action futura |
| **As the Action is Announced** | Janela especial para cartas que respondem ao anúncio da ação |
| **Registry** | Mapeamento de nomes de cartas para suas propriedades de janela/efeito |
