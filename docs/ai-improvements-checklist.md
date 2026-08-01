# AI Improvements Checklist

> Funcionalidades a implementar no StrategyBot para jogos mais inteligentes.

---

## 1. Conhecimento de Mesa (Game State Awareness)

- [x] Saber quem é presa, predador e cross
- [x] Avaliar ameaça de cada jogador
- [ ] Avaliar força relativa (quem é mais forte)
- [ ] Avaliar posição na mesa (quem ataca quem)

## 2. Lógica de Cross-Table

- [ ] Identificar predador de cada cross
- [ ] Decidir quando ajudar cross (atacar predador dele)
- [ ] Priorizar ações que beneficiam múltiplos aliados
- [ ] Não atacar cross sem razão

## 3. Timing de Cartas

- [ ] Usar modifiers só após confirmação de bloqueio
- [ ] Usar stealth quando há blockers perigosos
- [ ] Usar deflection contra bleeds grandes
- [ ] Usar rush só contra ameaças reais
- [ ] Usar Govern sup quando há vampiro barato no uncontrolled

## 4. Card Knowledge (saber qual carta usar)

- [ ] Mapear cartas na mão para situações
- [ ] Priorizar cartas baseado no estado do jogo
- [ ] Guardar cartas defensivas para momentos críticos
- [ ] Usar cartas de combo no timing certo

## 5. Avaliação de Situação

- [ ] Estou ganhando? (agressivo)
- [ ] Estou perdendo? (defensivo)
- [ ] Mesa está equilibrada? (diplomático)
- [ ] Qual a melhor ação para cada situação?

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
