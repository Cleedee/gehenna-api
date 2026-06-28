# Gehenna API - Documentacao

Bem-vindo a documentacao do Gehenna API, sistema para gerenciamento de
colecoes e decks de V:TES (Vampire: The Eternal Struggle).

## Navegacao Rapida

| Documento | Descricao |
|-----------|-----------|
| [Getting Started](getting-started.md) | Instalacao, configuracao e primeiros passos |
| [Arquitetura](architecture.md) | Visao geral do sistema e seus componentes |
| [API Reference](api-reference.md) | Endpoints da API FastAPI |
| [Web UI](web-ui.md) | Interface web Flask |
| [Game Engine](game-engine.md) | Motor de jogo V:TES |
| [KRCG](krcg-integration.md) | Integracao com recursos KRCG |
| [Regras do Jogo](rules/index.md) | Documentacao das regras do V:TES |
| [Desenvolvimento](development.md) | Checklists e tendencias |
| [Changelog](changelog.md) | Historico de alteracoes |
| [Dev Notes](dev-notes.md) | Notas para desenvolvedores |

---

## Arquitetura Resumida

```
+-------------+     +-------------+     +-------------+
|  Web UI     |---->|  FastAPI    |---->|  SQLite     |
|  (Flask)    |     |  (8002)     |     |  Database   |
+-------------+     +-------------+     +-------------+
                           |
                    +------+------+
                    |  Motor de   |
                    |  Jogo V:TES |
                    +-------------+
```

**Modulos principais:**
- `gehenna_api/` — API REST + Motor de jogo
- `gehenna_web/` — Interface web Flask
- `scripts/` — Utilitarios de gerenciamento
- `tests/` — Testes automatizados

Ver detalhes em [Arquitetura](architecture.md).

---

## Links Externos

- [KRCG](https://static.krcg.org/) — Recursos estaticos (imagens, dados)
- [VDB](https://vdb.im/) — Vampire Database (importacao de decks)
- [TWDA](https://twda.net/) — Tournament Winning Deck Archive
- [V:TES Rules](https://www.blackchantry.com/resources/) — Regras oficiais

---

## Como Contribuir

1. Documentacao vai em `docs/`
2. PDFs para extração vao em `docs/raw/`
3. Imagens e assets vao em `docs/assets/`
4. Referencias cruzadas entre documentos sao encorajadas
5. Para novas funcionalidades, atualizar o [Changelog](changelog.md)

---

## Estrutura de Diretorios

```
docs/
├── index.md                    # Voce esta aqui
├── getting-started.md          # Instalacao e setup
├── architecture.md             # Arquitetura do sistema
├── api-reference.md            # Endpoints REST
├── web-ui.md                   # Interface Flask
├── game-engine.md              # Motor de jogo
├── krcg-integration.md         # KRCG (imagens, dados externos)
├── development.md              # Checklists de desenvolvimento
├── changelog.md                # Historico de versoes
├── dev-notes.md                # Notas tecnicas
├── rules/                      # Regras do V:TES (ingles)
│   ├── index.md                # Indice das regras
│   ├── 01-introduction.md
│   └── ...
├── assets/                     # Imagens e diagramas
└── raw/                        # PDFs para extracao
```

---

*Ultima atualizacao: 2026-06-28*
