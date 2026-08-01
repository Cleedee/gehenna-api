# Plano de Implementação: Reinforcement Learning para V:TES

## Objetivo
Implementar um sistema de Q-Learning para o bot de V:TS aprender a jogar melhor através da experiência.

---

## 1. Conceitos Básicos

### Q-Learning
- **Q(s, a)**: Valor de escolher ação `a` no estado `s`
- **Estado (s)**: Situação atual do jogo (pool, ameaça, cartas, etc.)
- **Ação (s)**: Tipo de ação (bleed, rush, control, bloat, etc.)
- **Recompensa (r)**: Ganho por tomar uma ação

### Fórmula Q-Learning
```
Q(s, a) = Q(s, a) + α * [r + γ * max(Q(s', a')) - Q(s, a)]

Onde:
- α = taxa de aprendizado (0.1)
- γ = fator de desconto (0.9)
- r = recompensa imediata
- s' = próximo estado
```

---

## 2. Definição do Estado (Features)

### Features do Estado (12 dimensões)

| # | Feature | Descrição | Valores |
|---|---------|-----------|---------|
| 1 | pool_ratio | Pool do bot / 30 | 0.0 - 1.0 |
| 2 | prey_pool_ratio | Pool da presa / 30 | 0.0 - 1.0 |
| 3 | predator_pool_ratio | Pool do predador / 30 | 0.0 - 1.0 |
| 4 | own_threat | Ameaça do bot | 0.0 - 10.0 |
| 5 | prey_threat | Ameaça da presa | 0.0 - 10.0 |
| 6 | predator_threat | Ameaça do predador | 0.0 - 10.0 |
| 7 | phase | Fase do jogo | 0.0 (early) - 1.0 (final) |
| 8 | minion_count | Número de minios prontos | 0 - 6 |
| 9 | hand_size | Cartas na mão | 0 - 7 |
| 10 | has_bleed_card | Tem carta de sangria | 0 ou 1 |
| 11 | has_defense_card | Tem carta de defesa | 0 ou 1 |
| 12 | has_rush_card | Tem carta de rush | 0 ou 1 |

---

## 3. Definição das Ações

### Ações Disponíveis (7)

| # | Ação | Descrição |
|---|------|-----------|
| 0 | bleed | Sangrar presa |
| 1 | rush | Atacar minio com rush |
| 2 | control | Usar cartas de controle |
| 3 | bloat | Recuperar pool |
| 4 | stealth | Jogar stealth para passar |
| 5 | recruit | Recrutar aliado |
| 6 | pass | Não fazer nada |

---

## 4. Sistema de Recompensas

### Recompensas Imediatas

| Evento | Recompensa | Descrição |
|--------|------------|-----------|
| Bleed bem-sucedido | +0.3 | Dano na presa |
| Bleed bloqueado | -0.1 | Perdeu turno |
| Rush bem-sucedido | +0.2 | Eliminou minio |
| Oust de presa | +1.0 | Ganhou VP |
| Pool perdido | -0.1 | Perdeu pool |
| Pool ganho | +0.2 | Ganhou pool |
| Turno sem ação | -0.05 | Perdeu oportunidade |

### Recompensas por Fase

| Fase | Multiplicador |
|------|---------------|
| Early (1-5) | 0.8 (foco em setup) |
| Mid (6-15) | 1.0 (neutro) |
| Late (16+) | 1.2 (mais agressivo) |
| Final (2 jogadores) | 1.5 (máximo) |

---

## 5. Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    Game Engine                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │              StrategyBot (atual)                 │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │           QLearningAgent                 │   │   │
│  │  │  ┌─────────────────────────────────┐   │   │   │
│  │  │  │         Q-Table (hash map)       │   │   │   │
│  │  │  │   estado → {ação: valor Q}       │   │   │   │
│  │  │  └─────────────────────────────────┘   │   │   │
│  │  │  ┌─────────────────────────────────┐   │   │   │
│  │  │  │       Replay Buffer             │   │   │   │
│  │  │  │   (estado, ação, recompensa,    │   │   │   │
│  │  │  │    próximo estado)               │   │   │   │
│  │  │  └─────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Processo de Treinamento

### Etapa 1: Coleta de Dados (1000 jogos)
```
Para cada jogo:
  1. Inicializar estado
  2. Para cada turno:
     a. Extrair features do estado
     b. Escolher ação (ε-greedy)
     c. Executar ação
     d. Observar recompensa e próximo estado
     e. Armazenar no replay buffer
  3. Atualizar Q-Table
```

### Etapa 2: Treinamento (off-line)
```
Para cada episódio no replay buffer:
  1. Calcular Q(s, a) usando fórmula
  2. Atualizar Q-Table
  3. Reduzir ε (exploração)
```

### Etapa 3: Validação
```
Rodar 100 jogos com bot treinado vs RandomBot
Comparar taxa de vitória
```

---

## 7. Hiperparâmetros

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| α (learning_rate) | 0.1 | Taxa de aprendizado |
| γ (discount_factor) | 0.9 | Fator de desconto |
| ε (exploration_rate) | 0.3 → 0.01 | Exploração (decresce) |
| ε_decay | 0.995 | Decaimento da exploração |
| batch_size | 32 | Tamanho do batch |
| buffer_size | 10000 | Tamanho do replay buffer |

---

## 8. Implementação

### Arquivos a Criar

| Arquivo | Descrição |
|---------|-----------|
| `gehenna_api/engine/ai/q_learning.py` | Agente Q-Learning |
| `gehenna_api/engine/ai/state_encoder.py` | Codificador de estado |
| `gehenna_api/engine/ai/reward.py` | Sistema de recompensas |
| `gehenna_api/engine/ai/trainer.py` | Treinador off-line |
| `tests/test_q_learning.py` | Testes unitários |

### Integração

```python
# No StrategyBot
class StrategyBot:
    def __init__(self, deck_id, use_rl=False):
        if use_rl:
            self.agent = QLearningAgent()
            self.agent.load('q_table.json')
    
    def choose_action_type(self, state, player_id, minion_id):
        if self.agent:
            # Usar Q-Learning
            features = encode_state(state, player_id)
            return self.agent.choose_action(features)
        else:
            # Usar heurísticas (fallback)
            return self._heuristic_action(...)
```

---

## 9. Métricas de Avaliação

| Métrica | Meta | Atual |
|---------|------|-------|
| Taxa de vitória vs RandomBot | > 50% | 38% |
| VP médio por jogo | > 1.5 | ~1.0 |
| Tempo de treinamento | < 1 hora | - |
| Tamanho da Q-Table | < 100MB | - |

---

## 10. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Q-Table muito grande | Usar approximativa (neural net) |
| Treinamento lento | Paralelizar jogos |
| Overfitting | Validar com decks diferentes |
| Instabilidade | Usar replay buffer |

---

## 11. Cronograma

| Fase | Duração | Entregável |
|------|---------|------------|
| 1. Protótipo | 2 horas | Q-Learning básico |
| 2. Integração | 1 hora | Bot usando RL |
| 3. Treinamento | 1 hora | Q-Table treinada |
| 4. Validação | 1 hora | Métricas de performance |
| **Total** | **5 horas** | Bot RL funcional |

---

> Este plano implementa Q-Learning como base. Se necessário, pode ser
> estendido para Deep Q-Network (DQN) usando redes neurais.
