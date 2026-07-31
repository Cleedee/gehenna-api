# Metagame em V:TES - O Jogo Dentro do Jogo

> Fonte: [Codex of the Damned](https://codex-of-the-damned.org/pt/strategy/articles/advanced/the-game-of-the-game.html) - Mark Loughman

---

## 1. O que é Metagame?

### Definição
- **Metagame**: o jogo sobre o jogo
- Entender como oponentes jogam
- Adaptar estratégia conforme o ambiente

### Níveis
1. **Local**: grupo de jogo regular
2. **Regional**: cena de torneios
3. **Global**: top tier competitivo

---

## 2. Ciclo de Meta

### Fase 1: Dominância
- Arquétipo forte domina
- Exemplo: Stealth & Bleed

### Fase 2: Resposta
- Oponentes adaptam
- Adicionam counter-cards
- Exemplo: mais Percepção

### Fase 3: Contra-Resposta
- Arquético original muda
- Adiciona cartas para evitar counters
- Exemplo: mais Daring the Dawn

### Fase 4: Evolução
- Novos arquétipos surgem
- Meta se diversifica

---

## 3. Estratégias de Adaptação

### 3.1 Contra Stealth & Bleed
**Counter-cards**:
- Percepção (Reaction)
- Deflection (Reaction)
- Enhanced Senses (Reaction)

**Estratégia**:
- Bloquear quando possível
- Redirecionar sangrias grandes
- Não desperdiçar recursos em bloqueios pequenos

### 3.2 Contra Rush
**Counter-cards**:
- Dodges (Combat)
- Form of Mist (Combat)
- Earth Meld (Combat)

**Estratégia**:
- Evitar combate
- Usar aliados como escudo
- Manter distance

### 3.3 Contra Vote
**Counter-cards**:
- Direct Intervention (Master)
- Delaying Tactics (Reaction)

**Estratégia**:
- Negociar com outros jogadores
- Votar contra quando possível
- Manter pool alta

### 3.4 Contra Wall
**Counter-cards**:
-制御 (Control)
- Bait & Switch (Reaction)

**Estratégia**:
- Não lutar defensivamente
- Focar em sangria
- Usar vote como alternativa

---

## 4. Leitura de Mesa

### Identificar Ameaças
1. **Recursos altos** = perigo
2. **Muitos servos** = perigo
3. **Títulos** = perigo
4. **Sangria alta** = perigo

### Prioridades de Ação
1. **Maior ameaça** → controlar
2. **Predador** → pressionar (reduzir ameaça pelas costas)
3. **Presa** → eliminar (VP)
4. **Outros** → avaliar

### Sinais de Alerta
- Vampiro com muita força
- Muitos servos prontos
- Pool > 20
- Títulos múltiplos

---

## 5. Negociação de Mesa

### Conceitos
- **Alianças temporárias**: unir contra ameaça
- **Promessas**: trocar favores
- **Ameaças**: persuadir por medo

### Táticas
1. **Apontar ameaça**: "Ele está vencendo!"
2. **Sugerir ação**: "Vamos atacar ele juntos"
3. **Oferecer trégua**: "Não vou te atacar se..."
4. **Usar medo**: "Se ele vencer, perdemos todos"

### Limites
- Negociação é parte do jogo
- Mas promessas não são obrigatórias
- "Tudo é permitido, nada é garantido"

---

## 6. Adaptação para Bot

### Sistema de Prioridades
```yaml
priorities:
  - type: threat_assessment
    factors:
      - pool: high
      - minions: many
      - titles: yes
      - bleed_power: high
  
  - type: target_selection
    rules:
      - if: threat_level > threshold
        action: control
      - if: is_predator
        action: pressure
      - if: is_prey
        action: eliminate
  
  - type: card_play
    rules:
      - if: enemy_played_counter
        action: adapt
      - if: no_counters
        action: standard
```

### Memória de Partida
- Registrar cartas jogadas
- Identificar tendências
- Adaptar rodada seguinte

### Reação ao Meta
- Se muitos bloqueios → mais stealth
- Se muitos dodges → mais dano
- Se muito vote → mais defense
- Se muito rush → mais dodge

---

## 7. Exemplo Prático

### Cenário
- Mesa com 4 jogadores
- 1 Stealth & Bleed (forte)
- 1 Rush (forte)
- 1 Vote (médio)
- 1 Toolbox (você)

### Análise
1. **Stealth & Bleed**: ameaça maior (sangria alta)
2. **Rush**: ameaça secundária (pode te atacar)
3. **Vote**: ameaça potencial (depende de votos)
4. **Você**: precisa se posicionar

### Estratégia
1. **Turnos 1-3**: desenvolver recursos
2. **Turnos 4-6**: pressionar predador (reduzir ameaça)
3. **Turnos 7+**: focar em presa (VP)

### Reações
- Se Rush te ataca → usar defesa
- Se Stealth & Bleed sangra → redirecionar
- Se Vote ameaça → negociar contra
