from __future__ import annotations

import argparse
import time

import httpx

API_BASE = 'http://localhost:8002'


# ── ANSI helpers ──────────────────────────────────────────────────────


def _c(code: str, text: str) -> str:
    return f'{code}{text}\033[0m'


def green(t: str) -> str:
    return _c('\033[92m', t)


def yellow(t: str) -> str:
    return _c('\033[93m', t)


def red(t: str) -> str:
    return _c('\033[91m', t)


def cyan(t: str) -> str:
    return _c('\033[96m', t)


def dim(t: str) -> str:
    return _c('\033[90m', t)


def bold(t: str) -> str:
    return _c('\033[1m', t)


# ── API client ────────────────────────────────────────────────────────


class GameAPI:
    def __init__(self, base_url: str = API_BASE) -> None:
        self.client = httpx.Client(base_url=base_url, timeout=15)

    def create_game(self, player_names: list[str], deck_ids: list[int], seed: int | None = None) -> dict:
        body = {'player_names': player_names, 'deck_ids': deck_ids}
        if seed is not None:
            body['seed'] = seed
        r = self.client.post(
            '/game/new',
            json=body,
        )
        r.raise_for_status()
        return r.json()

    def get_state(self, game_id: str) -> dict:
        r = self.client.get(f'/game/{game_id}')
        r.raise_for_status()
        return r.json()

    def get_summary(self, game_id: str) -> dict:
        r = self.client.get(f'/game/{game_id}/summary')
        r.raise_for_status()
        return r.json()

    def run_turn(self, game_id: str) -> dict:
        r = self.client.post(f'/game/{game_id}/turn')
        r.raise_for_status()
        return r.json()

    def get_log(self, game_id: str) -> list[dict]:
        r = self.client.get(f'/game/{game_id}/log')
        r.raise_for_status()
        return r.json().get('log', [])

    def list_decks_api(self) -> list[dict]:
        r = self.client.get('/decks/', params={'limit': 500})
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self.client.close()


# ── Deck listing ──────────────────────────────────────────────────────


def list_decks_cmd(api: GameAPI) -> None:
    data = api.list_decks_api()
    decks = data if isinstance(data, list) else data.get('decks', data)

    print(f'\n{"ID":>4}  {"Name":<50} {"Type":<20} {"Owner ID":<10}')
    print('-' * 90)
    for d in decks:
        print(
            f'{d["id"]:>4}  {d.get("name", "?"):<50} '
            f'{d.get("tipo", "?"):<20} {d.get("owner_id", "?"):<10}'
        )
    print(f'\nTotal: {len(decks)} decks')


# ── State display ─────────────────────────────────────────────────────


def show_summary(summary: dict) -> None:
    print(bold(cyan(f'\nTurn {summary["turn"]} — Phase: {summary["phase"]}')))
    for p in summary['players']:
        color = green if p.get('has_edge') else (lambda t: t)
        prefix = '▶ ' if p['id'] == summary.get('current_player') else '  '
        print(
            f'{color(prefix)}{p["name"]:12} '
            f'Pool: {p["pool"]:>2}  '
            f'H: {p["hand_size"]:>2}  '
            f'Lib: {p["library_size"]:>3}  '
            f'VP: {p["vp"]}  '
            f'Edge: {"✓" if p["has_edge"] else "·"}'
        )
        for m in p.get('minions', []):
            status = green('✓') if m['ready'] else dim('🔒')
            print(f'  {status} {m["name"]:25} ♥{m["blood"]}')

    winner = summary.get('winner')
    if winner:
        print(bold(green(f'\nWinner: Player {winner}!')))


# ── Simulation mode ───────────────────────────────────────────────────


def run_simulation(
    api: GameAPI,
    deck_ids: list[int],
    num_players: int | None = None,
    max_turns: int = 30,
    delay: float = 0.5,
    seed: int | None = None,
) -> None:
    if num_players is None:
        num_players = len(deck_ids)
    names = [f'Bot-{chr(65 + i)}' for i in range(num_players)]

    print(green(bold('\n=== BOT SIMULATION ===')))
    result = api.create_game(names, deck_ids, seed=seed)
    if 'error' in result:
        print(red(f'Error: {result["error"]}'))
        return
    gid = result['game_id']
    print(f'Game {gid} created with {result["players"]} players')
    print(f'Decks: {deck_ids}')

    prev_log_len = 0
    for turn in range(max_turns):
        time.sleep(delay)

        api.run_turn(gid)
        summary = api.get_summary(gid)
        log = api.get_log(gid)

        show_summary(summary)
        current_player_id = summary.get('current_player')
        for entry in log[prev_log_len:]:
            data = entry.get('data', {})
            text = data.get('text', '')
            if text:
                # Determine which player performed this action
                player_id = entry.get('player_id', current_player_id)
                player_name = '??'
                for p in summary['players']:
                    if p['id'] == player_id:
                        player_name = p['name']
                        break
                print(dim(f'  [{player_name}] {text}'))
        prev_log_len = len(log)

        if summary.get('winner'):
            break

    summary = api.get_summary(gid)
    winner = summary.get('winner')
    if winner:
        print(green(bold(f'\nWinner: Player {winner}!')))
    else:
        print(red(f'\nNo winner after {max_turns} turns'))

    for p in summary['players']:
        print(f'  {p["name"]}: pool={p["pool"]}, vp={p["vp"]}')


# ── Human play mode ────────────────────────────────────────────────────


def run_human_game(
    api: GameAPI,
    deck_ids: list[int],
    num_bots: int | None = None,
    max_turns: int = 50,
    seed: int | None = None,
) -> None:
    if num_bots is None:
        num_bots = len(deck_ids) - 1
    human_name = input(f'  Your name [{green("You")}]: ').strip() or 'You'
    names = [human_name] + [f'Bot-{chr(66 + i)}' for i in range(num_bots)]

    # Ensure we have enough deck_ids
    if len(deck_ids) < len(names):
        deck_ids = deck_ids + [deck_ids[-1]] * (len(names) - len(deck_ids))

    print(green(bold('\n=== HUMAN VS BOTS ===')))
    result = api.create_game(names, deck_ids, seed=seed)
    gid = result['game_id']
    print(f'Game {gid} created')
    print(
        f'Deck: {result["deck"]["crypt"]} crypt + '
        f'{result["deck"]["library"]} library'
    )

    prev_log_len = 0
    turn = 0
    while turn < max_turns:
        time.sleep(0.2)
        api.run_turn(gid)
        summary = api.get_summary(gid)
        log = api.get_log(gid)

        show_summary(summary)
        for entry in log[prev_log_len:]:
            text = entry.get('data', {}).get('text', '')
            if text:
                print(dim(f'  {text}'))
        prev_log_len = len(log)

        current = summary.get('current_player')
        if current is not None:
            player_state = next(
                (p for p in summary['players'] if p['id'] == current),
                None,
            )
            name = player_state['name'] if player_state else f'#{current}'
            is_human = name == human_name

            if is_human:
                input(dim(f'\n{name}, press Enter for your turn...'))
            else:
                time.sleep(0.3)

        turn += 1

        if summary.get('winner'):
            break

    summary = api.get_summary(gid)
    winner = summary.get('winner')
    if winner:
        print(green(bold(f'\nWinner: Player {winner}!')))
    else:
        print(red(f'\nNo winner after {max_turns} turns'))

    for p in summary['players']:
        h = '✓' if p.get('has_edge') else ' '
        print(f'  {p["name"]:12} pool={p["pool"]:>2}  vp={p["vp"]}  edge={h}')


# ── CLI entry ──────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description='V:TES Game Engine CLI (via REST API)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  python -m gehenna_api.engine.cli list-decks\n'
            '  python -m gehenna_api.engine.cli play 1 --bots 2\n'
            '  python -m gehenna_api.engine.cli simulate 1 2 --turns 20\n'
            '  python -m gehenna_api.engine.cli simulate 1 2 --seed 123 --turns 20\n'
        ),
    )
    parser.add_argument(
        '--api',
        default=API_BASE,
        help=f'API base URL (default: {API_BASE})',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list-decks', help='List available decks')

    p_play = sub.add_parser('play', help='Play as human vs bots')
    p_play.add_argument('decks', type=int, nargs='+', help='Deck IDs (one per player)')
    p_play.add_argument('--bots', type=int, default=None, help='Number of bots (default: len(decks)-1)')
    p_play.add_argument('--turns', type=int, default=50, help='Max turns')
    p_play.add_argument('--seed', type=int, default=42, help='Seed for reproducibility (default: 42)')

    p_sim = sub.add_parser('simulate', help='Bot vs bot simulation')
    p_sim.add_argument('decks', type=int, nargs='+', help='Deck IDs (one per player)')
    p_sim.add_argument(
        '--players', type=int, default=None, help='Number of players (default: len(decks))'
    )
    p_sim.add_argument('--turns', type=int, default=30, help='Max turns')
    p_sim.add_argument(
        '--delay', type=float, default=0.5, help='Delay between turns'
    )
    p_sim.add_argument('--seed', type=int, default=42, help='Seed for reproducibility (default: 42)')

    args = parser.parse_args()
    api = GameAPI(args.api)

    try:
        if args.command == 'list-decks':
            list_decks_cmd(api)
        elif args.command == 'play':
            run_human_game(api, args.decks, args.bots, args.turns, seed=args.seed)
        elif args.command == 'simulate':
            run_simulation(
                api, args.decks, args.players, args.turns, args.delay, seed=args.seed
            )
    finally:
        api.close()


if __name__ == '__main__':
    main()
