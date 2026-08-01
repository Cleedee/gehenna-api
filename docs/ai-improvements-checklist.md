# AI Improvements Checklist

> Funcionalidades a implementar no StrategyBot para jogos mais inteligentes.

---

## 1. Conhecimento de Mesa (Game State Awareness)

- [x] Saber quem é presa, predador e cross
- [x] Avaliar ameaça de cada jogador
- [x] Avaliar força relativa (quem é mais forte)
- [x] Avaliar posição na mesa (quem ataca quem)

## 2. Lógica de Cross-Table

- [x] Identificar predador de cada cross
- [x] Decidir quando ajudar cross (atacar predador dele)
- [x] Priorizar ações que beneficiam múltiplos aliados
- [x] Não atacar cross sem razão

## 3. Timing de Cartas

- [x] Usar modifiers só após confirmação de bloqueio
- [x] Usar stealth quando há blockers perigosos
- [x] Usar deflection contra bleeds grandes
- [x] Usar rush só contra ameaças reais
- [x] Usar Govern sup quando há vampiro barato no uncontrolled

## 4. Card Knowledge (saber qual carta usar)

- [x] Mapear cartas na mão para situações
- [x] Priorizar cartas baseado no estado do jogo
- [x] Guardar cartas defensivas para momentos críticos
- [ ] Usar cartas de combo no timing certo

## 5. Avaliação de Situação

- [x] Estou ganhando? (agressivo)
- [x] Estou perdendo? (defensivo)
- [x] Mesa está equilibrada? (diplomático)
- [x] Qual a melhor ação para cada situação?

## 6. Prioridades Dinâmicas

- [ ] Early game: bloat + investimento
- [ ] Mid game: eliminação de presa
- [ ] Late game: lunge final
- [ ] Final: ataque total

## 7. Aprendizado (ideal)

- [ ] Lembrar o que funcionou antes
- [ ] Adaptar estratégia ao longo do jogo
- [ ] Reconhecer padrões de oponentes

---

## Prioridade Máxima

1. **Prey/Predator/Cross awareness** (fundamental)
2. **Card Knowledge** (saber qual carta usar)
3. **Timing de cartas** (quando usar)
4. **Lógica de cross-table** (alianças indiretas)

---

## Referências

- `gehenna_api/engine/ai/strategy.py` - StrategyEngine
- `gehenna_api/engine/ai/strategy_bot.py` - StrategyBot
- `docs/vtes-estrategia-geral.md` - Estratégia geral
- `docs/vtes-arquetipos.md` - Arquétipos de deck
