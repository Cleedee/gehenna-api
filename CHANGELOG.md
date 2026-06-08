# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [A Publicar]

### Adicionado

- Atualizar texto de cartas atualizadas.

## 0.4.0 — 2026-06-08

### Adicionado

- Motor de jogo V:TES (gehenna_api/engine/).
- Simulação de partidas entre bots via `uv run python -m gehenna_api.engine.cli simulate`.
- Seed-based reproducibility (padrão 42) para simulações determinísticas.
- Sistema de fases: Unlock, Master, Minion (com ações), Influence.
- Implementação das regras de stealth/intercept para bloqueios.
- Cartas de combate: Earth Meld, Entombment, Oubliette, Form of Mist etc.
- Modificadores de ação (stealth, bleed) jogados no timing correto.
- Reações (Deflection, Deep Ecology, Guard Dogs etc.) durante bloqueios.
- Two-player game loop com suporte a expansão futura.
- Servidor HTTP com API REST para gerenciar partidas (`/game/new`, `/game/{id}/turn`).
- Bot aleatório (RandomBot) como adversário.
- Atualizadas as seções de configuração para Docker.

### Corrigido

- Equipamentos agora recebem +1 stealth por padrão (regra oficial).
- Modificadores de stealth puro não são mais jogados após fase de bloqueio.
- Bloqueadores não tentam bloquear se intercept é insuficiente.
- Intercept de reações (ex.: Deep Ecology +2) extraído corretamente do texto.
- Nome da ação exibido nos logs em vez de "action" genérico.
- Duplicação de bloqueadores em jogos de 2 jogadores (prey == predator).

## 0.3.0
 - Interface Web UI
 - Extração de deck da internet.
 - Estatísticas.
 - Recomendações.
 - Cartas faltantes para montar um deck.
 - Em quais preconstruídos podemos encontrar cartas que faltam.
 - Configuração para Docker.

## 0.2.0

- Consultar item de movimento por id com GET /stocks/item/id

## [0.1.0]

### Adicionado

- Atualizar as cartas com os IDs do VDB.
- Cadastrar novas cartas de cripta.
- Cadastrar novas cartas de biblioteca.
