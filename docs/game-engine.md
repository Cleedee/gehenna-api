# Game Engine — V:TES

Motor de jogo para V:TES (Vampire: The Eternal Struggle).

## Status

Progresso: ~75% (99/132 features)

Ver [checklist completo](game-engine-checklist.md) para detalhes.

## Arquitetura

```
gehenna_api/engine/
├── cli.py          # Interface de linha de comando
├── game.py         # Logica principal do jogo
├── player.py       # Jogadores e bots
├── card.py         # Carregamento de cartas
├── actions/        # Acoes do jogo
├── combat/         # Sistema de combate
└── state.py        # Estado do jogo
```

## Funcionalidades Implementadas

### Setup
- 30 pool por jogador
- Blood bank (999,999)
- Edge comeca descontrolado
- Crypt/Library separados
- 7 cartas na mao
- 4 cartas crypt descontroladas

### Turno (5 fases)
1. **Unlock** — desbloquear cartas, Edge da +1 pool
2. **Master** — 1 acao master (trifles dao +1)
3. **Minion** — acoes de lacaios (bleed, hunt, equip, etc.)
4. **Influence** — transferir influencia para cartas
5. **Discard** — descartar ate 7 cartas

### Acoes Basicas
- Bleed (atacar pool do prey)
- Hunt (recuperar sangue se blood=0)
- Leave Torpor / Rescue from Torpor
- Diablerie
- Equip, Employ Retainer, Recruit Ally
- Political Action

### Combate
- Hand Strike, Dodge, Combat Ends
- Steal Blood, First Strike, Ranged Strike
- Dano normal e agravado
- Torpor e Burning

### Sistema Politico
- Referendums
- Titulos (Primogen, Prince, Justicar, Inner Circle)
- Blood Hunt

### Reacoes e Modificadores
- Reacoes (Deflection, Deep Ecology, Guard Dogs)
- Modificadores de acao (stealth, bleed)

## Proximos Passos

1. Reflex Cards
2. Advanced Vampires
3. Persistencia (save/load)
4. CLI/Human Interface
5. Testes de integracao

## Como Executar

```bash
# Simulacao bot vs bot
python -m gehenna_api.engine.cli simulate 1 --players 2 --turns 20

# Com seed reprodutivel
python -m gehenna_api.engine.cli simulate 1 --players 2 --turns 20 --seed 42

# Listar decks
python -m gehenna_api.engine.cli list-decks
```

Ver:
- [Regras do Jogo](rules/index.md) para documentacao das regras
- [Checklist](game-engine-checklist.md) para status detalhado
- [Architecture](architecture.md) para visao geral
