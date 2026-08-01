# Estratégia Geral em V:TES

> Fonte: [Codex of the Damned - Estratégia](https://codex-of-the-damned.org/pt/strategy/index.html)

---

## 1. Fundamentos

### Sangria (Bleed)
- **Base para vencer**: destruir recursos da presa via sangria
- ~75% dos decks viáveis eliminam presa por sangria
- Disciplinas de sangria: **D** (Dominate) é a mais forte, seguida de **R** (Presence) e **E** (Auspex)
- Modificadores (Conditioning, etc.) devem ser jogados **após** presa recusar bloquear
- Modificadores são "limitados" (1 por ação), exceto cartas específicas (Leverage, Command of the Beast)

### Reduce & Bounce
- **Redirecionamentos**: mudam alvo da sangria (Deflection, Telepathic Misdirection)
- **Reduções**: diminuem valor da sangria
- Jogar **após** valor confirmado pelo predador
- Apenas 8 cartas permitem redirecionar: Deflection, Redirection, Telepathic Misdirection, etc.

---

## 2. Combate

### Posturas Estratégicas
1. **Neutralizar servos** (agressiva) - retarda adversários, controle de mesa
2. **Desgastar** (equilibrada) - foca no sangue da presa
3. **Resistir** (defensiva) - sobreviver a ataques

### Disciplinas de Combate
| Disciplina | Melhor Para |
|------------|-------------|
| **P** (Potence) | Dano alto |
| **C** (Celeridade) | Múltiplos golpes |
| **O** (Obfuscate) | Furtividade |
| **W** (Protean) | Dano agravado (Wolf Claws) |
| **T** (Thaumaturgy) | Theft of Vitae (+4 sangue) |

### Tipos de Deck de Combate
- **Rush**: provoca combate diretamente (Bum's Rush, Freakish Conglomeration)
- **Bloat**: foca em acumular recursos
- **Wall**: foca em defesa e controle

---

## 3. Boiar (Bloat)

### Extração de Sangue
Cartas que recuperam sangue de vampiros:
- **Villein** (até 5 sangue, errata 2018)
- **Minion Tap** (mais eficiente)
- **Blood Doll**, **Vessel**, **Tribute to the Master**

### Territórios (Hunting Grounds)
- Recuperam sangue durante unlock
- Um para quase cada clã
- Exemplos: The Rack, Papillon, Carfax Abbey

### Estratégia
- Todo deck eficiente tem módulo de bloat
- Colocar sangue em vampiros não controlados = bloat indireto
- Combina com cartas que regeneram sangue

---

## 4. Construção de Deck

### Módulos e Densidade
| Tipo | Densidade | Expectativa (mão=7) | Uso |
|------|-----------|---------------------|-----|
| **Spam** | >25% | >1,75 | Cartas jogadas várias vezes/turno |
| **Primário** | 14-25% | 1-1,5 | Usado 1-2x por turno |
| **Secundário** | 7-14% | 0,5-1 | Usado regularmente |
| **Tático** | <7% | <0,5 | Suporte específico |

### Regra de Ouro
- Ter 5-6 cópias de uma carta primária = ~90% chance de ver na mão inicial
- Densidade afeta consistência do deck

---

## 5. Negociação de Mesa

### Conceitos Chave
- **Mesa é multi-jogador**: alianças temporárias são parte do jogo
- **Predador/Prey**: entender posições é crucial
- **Equilíbrio de mesa**: manter todos em níveis similares de recursos
- **Reconhecer ameaças**: identificar quem está vencendo

### Táticas
- Pedir ajuda contra líder
- Sugerir ações contra oponentes perigosos
- Negociar trégua temporária
- Usar medo para influenciar decisões

---

## 6. Princípios Básicos para Bot

### Prioridades de Ação
1. **Sangrar presa** quando possível
2. **Controlar mesa** se houver ameaça grande
3. **Boiar** quando recursos baixos
4. **Caçar** se sangue = 0

### Decisões de Bloqueio
- Bloquear sangrias grandes contra si
- Considerar bloquear ações perigosas para a mesa
- Não bloquear ações pequenas (desperdiça recursos)

### Gestão de Recursos
- Manter sangue em vampiros > 1
- Usar Villein/Minion Tap quando possível
- Caçar apenas em último caso

---

## 7. Configuração do StrategyBot

### Estrutura do JSON

```json
{
  "deck_id": 275,
  "name": "Deck Name",
  "bleed_priority": 0.6,
  "rush_priority": 0.5,
  "vote_priority": 0.0,
  "control_priority": 0.4,
  "bloat_priority": 0.3,
  "early_phase": { "bleed_modifier": -0.1 },
  "mid_phase": { "bleed_modifier": 0.1 },
  "late_phase": { "bleed_modifier": 0.2 },
  "final_phase": { "bleed_modifier": 0.3 }
}
```

### Prioridades por Arquétipo

| Arquétipo | bleed | rush | vote | control | bloat |
|-----------|-------|------|------|---------|-------|
| **Stealth & Bleed** | 0.8 | 0.0 | 0.0 | 0.2 | 0.3 |
| **Powerbleed** | 0.9 | 0.0 | 0.0 | 0.1 | 0.4 |
| **Vote** | 0.4 | 0.0 | 0.9 | 0.2 | 0.4 |
| **Rush** | 0.3 | 0.9 | 0.0 | 0.3 | 0.2 |
| **Wall** | 0.2 | 0.1 | 0.0 | 0.8 | 0.5 |
| **Toolbox** | 0.5 | 0.3 | 0.2 | 0.5 | 0.3 |
| **Swarm** | 0.4 | 0.5 | 0.0 | 0.3 | 0.6 |
| **Ally Toolbox** | 0.5 | 0.5 | 0.0 | 0.4 | 0.3 |

### Ajustes por Fase

| Fase | Prioridade | Ajuste Típico |
|------|------------|---------------|
| **Early** (1-5) | Bloat | +0.2 bloat, -0.2 rush |
| **Mid** (6-15) | Equilibrado | Base |
| **Late** (16+) | Agressivo | +0.2 bleed/rush, -0.2 bloat |
| **Final** (2 jogadores) | Ataque total | +0.3 bleed/rush, -0.3 bloat |

### Cartas Reconhecidas

O bot reconhece automaticamente:

| Tipo | Exemplos | Efeito |
|------|----------|--------|
| **Rush Action** | Ambush, Bum's Rush | action.rush |
| **Bleed Action** | Govern, Deep Song | bleed no texto |
| **Bleed Modifier** | Conditioning, Bonding | +bleed no texto |
| **Ally** | Freakish Conglomeration | tipo='Ally' |
