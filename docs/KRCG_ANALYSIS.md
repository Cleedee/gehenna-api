# Análise KRCG - Recursos Disponíveis e Insights

## Visão Geral

O KRCG (Kindle Reader Card Generator / V:TES Companion) fornece recursos estáticos e API para desenvolvimento de aplicações V:TES (Vampire: The Eternal Struggle).

- **Site Estático**: https://static.krcg.org/
- **API**: https://api.krcg.org/
- **Licença**: Dark Pack Agreement (gratuito com mesma licença)

---

## 1. Recursos do Site Estático

### 1.1 Imagens de Cartas

**URL Base**: `https://static.krcg.org/card/`

**Formatos**:
- WEBP (preferencial - menor tamanho)
- JPG (legacy)

**Nomenclatura**:
- Nome normalizado (sem espaços, minúsculo)
- Exemplo: `powerbasezurich.webp`

**Parâmetros disponíveis**:
- `g{n}` - Grupo (ex: `powerbasezurichg2.webp`)
- `adv` - Advanced cards (ex: `theobellg2adv.webp`)

**Recursos adicionais**:
- Card backs: `cardbackcrypt.jpg`, `cardbacklibrary.jpg`
- Card sets: `/set/jyhad/44magnum.jpg`
- Traduções: `/card/fr/fame.jpg`

**ZIP completo**: `card/_all_cards.zip` (todas as cartas em WEBP)

### 1.2 Ícones SVG (Vetoriais)

**URL Base**: `https://static.krcg.org/svg/`

#### Clãs (`svg/clan/`)
- Todos os clãs: `tremere.svg`, `brujah.svg`, etc.
- Versões Sabbat com selo vermelho: `sealtremereantitribu.png`
- Clãs deprecated: `clan/deprecated/`

#### Disciplinas (`svg/disc/`)
- Inferiores: `disc/inf/aus.svg`
- Superiores: `disc/sup/aus.svg`
- Especiais: `flight.svg`, `maleficia.svg`, `striga.svg`

#### Ícones de Jogo (`svg/icon/`)
- action, blood, pool, capacity, etc.

### 1.3 Ícones PNG (Raster)

**URLs disponíveis**:
- `/png/` - Com transparência
- `/png_wb/` - Com bordas brancas (ideal para web)
- `/webp/` - WEBP com transparência
- `/webp_wb/` - WEBP com bordas brancas

### 1.4 Fontes

| Fonte | Uso | URL |
|-------|-----|-----|
| ankha2.otf | Disciplines, virtues, card types | `/web/ankha2.otf` |
| vtes-clans.otf | Clans, creeds icons | `/web/vtes-clans.otf` |
| ankha.ttf | Legacy (retrocompatibilidade) | `/web/ankha.ttf` |

### 1.5 Dados JSON

| Arquivo | Descrição |
|---------|-----------|
| `data/vtes.json` | Todas as cartas com rulings e traduções (V3) |
| `data/v2/vtes.json` | Formato V2 (descontinuado) |
| `data/twda.json` | TWDA ( Tournament Winning Deck Archive) |
| `data/twd.htm` | TWDA normalizado |

---

## 2. API KRCG

**URL Base**: `https://api.krcg.org/`

### Endpoints disponíveis (documentação limitada)

A API oferece endpoints para:
- Consulta de cartas
- Decks e decklists
- TWDA (Arquivo de Decks Vencedores)

**Nota**: Documentação limitada no momento da análise.

---

## 3. Funcionalidades JS/CSS

### krcg.js + krcg.css

Inclui funcionalidades de display:
- **Card hover**: Mostra imagem ao passar mouse
- **Card click**: Abre modal com imagem
- **Discipline icons**: usando `<span class="krcg-icon">f</span>`
- **Clan icons**: usando `<span class="krcg-clan">s</span>`

### krcg-blogger.js

Script especial para plataformas Blogger.

---

## 4. Mapeamentos de Ícones

### Disciplinas (trigramas)

| Código | Inferior | Superior |
|--------|----------|----------|
| ANI | animalism | ANIMALISM |
| AUS | auspex | AUSEX |
| CEL | celerity | CELERITY |
| DOM | dominate | DOMINATE |
| FOR | fortitude | FORTITUDE |
| MEL | melee | MELEE |
| NEC | necromancy | NECROMANCY |
| OBF | obfuscate | OBFUSCATE |
| OBL | oblivion | OBLIVION |
| POT | potence | POTENCE |
| PRE | presence | PRESENCE |
| PRO | protean | PROTEAN |
| QUI | quietus | QUIETUS |
| SAN | sanity | SANITY |
| SER | serpentis | SERPENTIS |
| THA | thaumaturgy | THAUMATURGY |
| THN | thanatosis | THANATOSIS |
| VIC | vicissitude | VICISSITUDE |
| VIN | vision | VISION |

### Clãs

| Código | Clã |
|--------|-----|
| a | Assamite |
| b | Baali |
| c | Bonnie |
| d | Caitiff |
| e | Giovanni |
| f | Harbinger of Skulls |
| g | Lasombra |
| h | Ravnos |
| i | Sette |
| j | Toreador |
| k | Tzimisce |
| l | Brujah |
| m | Gangrel |
| n | Malkavian |
| o | Nosferatu |
| p | Tremere |
| q | Ventrue |
| r | Salubri |
| s | Nosferatu (legacy) |
| t | Tzimisce (legacy) |
| u | Ventrue (legacy) |
| v | Oblivion |

---

## 5. Insights para Funcionalidades Futuras

### 5.1 Já Implementado (Gehenna API)

- [x] Imagens de cartas (WEBP com group/advanced)
- [x] Ícones de disciplinas (inferiores/superiores)
- [x] Ícones de clãs
- [x] Ícones de custo (blood/pool)
- [x] Ícone de capacity

### 5.2 Funcionalidades Sugeridas

#### Alta Prioridade
1. **Card Hover/Modal**: Implementar `krcg.js` para mostrar imagem ao hover nas listas
2. **Deck Lists com Ícones**: Mostrar disciplinas de vampires em decklists
3. **Card Back Images**: Usar `cardbackcrypt.jpg` para cartas sem imagem

#### Média Prioridade
4. **Filtros por Disciplina/Clã**: Usar dados KRCG para filtrar cartas
5. ** TWDA Integration**: Importar decklists do TWDA (`vtes.json` ou API)
6. **Traduções**: Suporte a imagens em outros idiomas (`/card/fr/`, etc.)

#### Baixa Prioridade
7. **Fontes Customizadas**: Usar `ankha2.otf` e `vtes-clans.otf` para текст
8. **Card Set Images**: Mostrar imagens originais por set
9. **Cache Busting**: Usar `#data` ou `/bust/{digits}/` para updates

### 5.3 Dados do vtes.json para Exploração

O arquivo `data/vtes.json` contém:
- Todas as cartas com metadados completos
- Rulings oficiais
- Traduções em múltiplos idiomas
- Tipo (Vampire, Master, Combat, etc.)
- Disciplinas, Clã, Custo, Capacity
- Título, Sect, Atributos

**Ideia**: Sincronizar base de dados local com `vtes.json` periodicamente.

---

## 6. URLs de Referência Rápida

```
# Imagens de cartas
https://static.krcg.org/card/{nome}.webp
https://static.krcg.org/card/{nome}g{grupo}.webp
https://static.krcg.org/card/{nome}g{grupo}adv.webp

# Ícones PNG
https://static.krcg.org/png/clan/{clan}.png
https://static.krcg.org/png/disc/inf/{disc}.png
https://static.krcg.org/png/disc/sup/{disc}.png
https://static.krcg.org/png/icon/{tipo}.png

# Dados
https://static.krcg.org/data/vtes.json
https://static.krcg.org/data/twda.json

# Fonts
https://static.krcg.org/web/ankha2.otf
https://static.krcg.org/web/vtes-clans.otf

# CSS/JS
https://static.krcg.org/web/krcg.css
https://static.krcg.org/web/krcg.js
```

---

## 7. Considerações de Cache

- **Cache-Control**: 1 hora
- **Last-Modified**: Confiável para verificar updates
- **Cache Busting**:
  - Fragment identifier: `card/fame.jpg#2022-01-25-14`
  - Prefix: `https://static.krcg.org/bust/2022012514/card/fame.jpg`

---

*Documento gerado em: 2026-05-04*
*Fonte: https://static.krcg.org/ e https://api.krcg.org/*