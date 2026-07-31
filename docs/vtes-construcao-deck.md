# Construção de Deck em V:TES

> Fonte: [Codex of the Damned](https://codex-of-the-damned.org/pt/strategy/deck-building.html)

---

## 1. Conceitos Fundamentais

### Tamanho do Deck
- **Mínimo**: 60 cartas (40 biblioteca + 12 cripta)
- **Recomendado**: 75-80 cartas
- **Mão inicial**: 7 cartas

### Proporção Ideal
- **Cripta**: 12-15 cartas (25-30%)
- **Biblioteca**: 60-70 cartas (70-75%)

---

## 2. Módulos e Densidade

### Definição
- **Módulo**: grupo de cartas com objetivo semelhante
- **Densidade**: porcentagem do deck que o módulo representa
- **Expectativa**: número de cartas do módulo em uma mão de 7

### Classificação por Densidade

| Tipo | Densidade | Expectativa | Uso |
|------|-----------|-------------|-----|
| **Spam** | >25% | >1,75 | Várias vezes/turno |
| **Primário** | 14-25% | 1-1,5 | 1-2x por turno |
| **Secundário** | 7-14% | 0,5-1 | Regularmente |
| **Tático** | <7% | <0,5 | Situações específicas |

### Cálculo de Expectativa
```
Expectativa = Densidade × 7 (tamanho da mão)

Exemplo: 20% densidade × 7 = 1.4 cartas esperadas
```

---

## 3. Módulos Comuns

### 3.1 Ação Principal (Primário)
- Carta que define a estratégia
- Exemplo: Govern the Unaligned (bleed)
- Densidade: 15-25%

### 3.2 Suporte (Secundário)
- Cartas que melhoram ação principal
- Exemplo: Conditioning (+bleed)
- Densidade: 10-15%

### 3.3 Defesa (Secundário/Tático)
- Cartas para sobreviver
- Exemplo: Deflection, Dodge
- Densidade: 10-20%

### 3.4 Bloat (Primário/Secundário)
- Recuperação de recursos
- Exemplo: Villein, Minion Tap
- Densidade: 10-15%

### 3.5 Combo (Tático)
- Sinergias específicas
- Exemplo: Govern + Bonding
- Densidade: 5-10%

---

## 4. Regras de Ouro

### Consistência
- **5-6 cópias** de carta primária = ~90% chance na mão inicial
- **3-4 cópias** = ~70% chance
- **2 cópias** = ~50% chance

### Eficiência
- Mínimo de cartas táticas
- Foco em módulos primários
- Evitar cartas "win more"

### Flexibilidade
- Ter opções para diferentes situações
- Não depender de combo específico
- Incluir cartas de múltiplo propósito

---

## 5. Exemplo: Deck 275

### Análise de Módulos

| Módulo | Cartas | Densidade | Tipo |
|--------|--------|-----------|------|
| Govern | 7x | 9.3% | Primário |
| Freakish | 7x | 9.3% | Primário |
| Deflection | 6x | 8.0% | Secundário |
| Shroud | 5x | 6.7% | Secundário |
| Stygian | 4x | 5.3% | Tático |
| Pass Through | 4x | 5.3% | Tático |
| Veil Thins | 3x | 4.0% | Tático |
| Outros | ~39x | 52.0| Misto |

### Observações
- Govern + Freakish = 18.6% (bom para primário)
- Defesa (Deflection + Pass Through) = 13.3%
- Bloat (Villein) = apenas 2.7% (baixo!)
- Potencial para melhorar módulo de bloat

---

## 6. Dicas para Bot

### Priorização de Cartas
1. **Primárias**: sempre jogar quando possível
2. **Secundárias**: jogar conforme situação
3. **Táticas**: guardar para momentos-chave

### Gestão de Mão
- Manter 2-3 cartas primárias
- Descartar cartas táticas se mão cheia
- Comprar para ter opções

### Decisões de Compra
- Priorizar módulos com menor densidade
- Não comprar cartas que já tem na mão
- Considerar o que o oponente pode ter
