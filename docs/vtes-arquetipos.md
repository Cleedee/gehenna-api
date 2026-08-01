# Arquétipos de Deck em V:TES

> Fonte: [Codex of the Damned - Arquétipos](https://codex-of-the-damned.org/pt/archetypes/index.html)

---

## Classificação

Arquétipos são classificados por nível de vitórias em torneios (20+ jogadores, últimos 3 anos).

### 💀 Top Tier (Metade das vitórias qualificadas)

| Arquétipo | Categoria | Descrição |
|-----------|-----------|-----------|
| **Gangrel Thing** | Wall | Controle defensivo com Gangrel |
| **Endless Dance** | Vote | Votação com Tremere/Inner Circle |
| **Govern Resistance** | Toolbox | Govern + resistência, flexível |
| **Haqim Royalty** | Toolbox | Banu Haqim com títulos |
| **Illegal Brawl** | Rush/Toolbox | Rush com combate |
| **Living Museum** | Stealth & Bleed | Furtividade + sangria (deck 241!) |
| **Lutz Politics** | Vote & Bleed | Votação + sangria |
| **Nephandii** | Allies Swarm | Enxame de aliados |
| **Platinum Revelation** | Stealth & Bleed | Furtividade + sangria |
| **Protean Barons** | Toolbox | Gangrel com títulos |
| **Ravnos Bonds** | Stealth & Bleed | Ravnos furtivo |
| **The Unnamed** | Stealth & Bleed | Lasombra furtivo |

### Concorrentes (Próximos ao Top)

| Arquétipo | Categoria |
|-----------|-----------|
| Ani Barons | Rush |
| Capuchin Toolbox | Toolbox |
| Emerald Legion | Toolbox |
| Hecata Corpse | Toolbox |
| Hecata Swarm | Swarm Bleed |
| Helena Guns | Wall |
| **Juliet's Dream** | Vote |
| Kalinda | Stealth & Bleed |
| Malk'22 | Stealth & Bleed |
| Oblivion Bleed | Stealth & Bleed |
| Pop Captivation | Vote & Bleed |
| Salubri Powerbleed | Powerbleed |
| Shalmath | Toolbox |
| Stanislava | Vote & Bleed |
| Tupdogs | Rush |

### Novatos (Potencial)

- Lasombra Politics (Vote)
- Piper War Ghoul '24 (Rush)
- Qawiyya Caine (Rush)

### Velha Guarda (Consolidados)

| Arquétipo | Categoria |
|-----------|-----------|
| Anti Ventrue Grinder | Toolbox |
| Dementation Bleed | Stealth & Bleed |
| Goratrix High Tower | Wall |
| Khazar's Diary | Swarm |
| Lasombra Pop | Vote & Bleed |
| Nergal Beast | Stealth & Bleed |
| Palla Grande | Wall |
| Princess Toolbox | Toolbox |
| Tzimisce Toolbox | Rush |

---

## Categorias Principais

### 1. Bleed (Sangria)
- Foco: eliminar presa via sangria
- Disciplinas: D (Dominate), R (Presence), E (Auspex)
- Subcategorias:
  - **Stealth & Bleed**: furtividade para passar ações
  - **Powerbleed**: sangria massiva sem stealth
  - **Bruise & Bleed**: combate + sangria

### 2. Vote (Votação)
- Foco: usar votos para aprovar referendos
- Disciplinas: V (Dominate), P (Presence)
- Vantagem: afeta todos os jogadores simultaneamente

### 3. Rush (Agro)
- Foco: provocar combate diretamente
- Disciplinas: C (Celeridade), P (Potence), W (Protean)
- Objetivo: eliminar servos dos oponentes

### 4. Wall (Defesa)
- Foco: controlar mesa via defesa
- Disciplinas: O (Obfuscate), W (Protean), A (Animalism)
- Estilo: passivo-agressivo

### 5. Toolbox (Flexível)
- Foco: adaptar-se à situação
- Múltiplas disciplinas
- Cartas para diversas situações

### 6. Swarm (Enxame)
- Foco: muitos servos/aliados
- Estilo:数量压倒
- Exemplo: Nephandii, Tupdogs

---

## Deck 275 - Análise de Arquétipo

O deck **"Path of Death Ally Toolbox"** (ID 275) se enquadra em:

**Categoria Primária**: Toolbox
**Categoria Secundária**: Rush (via Freakish Conglomeration)

### Comparação com Arquétipos Top

| Aspecto | Deck 275 | Living Museum (Top) | Govern Resistance (Top) |
|---------|----------|---------------------|-------------------------|
| Categoria | Toolbox/Rush | Stealth & Bleed | Toolbox |
| Disciplina Principal | OBL | DOM | GOV |
| Estilo | Controle via aliados | Furtividade | Flexível |
| Vantagem | Freakish rush | Govern sup | Resistência |

### Potencial
- O deck tem元件 de arquétipos vencedores
- Freakish Conglomeração dá capacidade de rush
- Govern sup + Shroud de Decay = controle
- Poderia ser otimizado para estilo mais competitivo

---

## Configuração de Bot por Arquétipo

### Stealth & Bleed
```json
{
  "bleed_priority": 0.8,
  "stealth_priority": 0.7,
  "rush_priority": 0.0,
  "vote_priority": 0.0
}
```

### Vote
```json
{
  "bleed_priority": 0.4,
  "vote_priority": 0.9,
  "stealth_priority": 0.4,
  "early_phase": { "vote_modifier": -0.2 }
}
```

### Rush
```json
{
  "bleed_priority": 0.3,
  "rush_priority": 0.9,
  "rush_threshold": 3.0,
  "early_phase": { "rush_modifier": -0.2 }
}
```

### Wall
```json
{
  "bleed_priority": 0.2,
  "control_priority": 0.8,
  "bloat_priority": 0.5,
  "late_phase": { "control_modifier": 0.2 }
}
```

### Ally Toolbox (Deck 275)
```json
{
  "bleed_priority": 0.5,
  "rush_priority": 0.5,
  "control_priority": 0.4,
  "bloat_priority": 0.3,
  "early_phase": { "bloat_modifier": 0.2, "rush_modifier": -0.2 },
  "late_phase": { "bleed_modifier": 0.2, "rush_modifier": 0.2 }
}
```
