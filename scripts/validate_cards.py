#!/usr/bin/env python3
"""
Card data validator — checks completeness of card data for simulation decks.

Usage:
    python scripts/validate_cards.py                    # all decks
    python scripts/validate_cards.py --deck 241          # single deck
    python scripts/validate_cards.py --verbose           # detailed output
    python scripts/validate_cards.py --critical-only     # only combat + reactions + modifiers
"""

import argparse
import sys
import os

# Ensure we can import from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gehenna_api.engine.card_loader import (
    validate_card_data,
    validate_deck,
    validate_all_decks,
    get_all_deck_ids,
)


CRITICAL_TIPOS = frozenset({
    'combat', 'action modifier', 'action modifier/combat',
    'action', 'reaction', 'equipment', 'retainer', 'ally',
    'action modifier/reaction', 'reaction/action modifier',
    'combo',
})


def _card_priority(report: dict) -> int:
    """Lower number = higher priority for fixing."""
    tipo = (report.get('tipo') or '').lower()
    if tipo in ('combat', 'action modifier/combat'):
        return 0
    if tipo in ('action modifier', 'reaction', 'action modifier/reaction',
                 'reaction/action modifier'):
        return 1
    if tipo in ('equipment', 'retainer', 'ally'):
        return 2
    if tipo in ('action', 'political action'):
        return 3
    if tipo == 'vampire':
        return 4
    return 5


def print_report(report: dict, verbose: bool = False, critical_only: bool = False):
    """Print validation report for a deck."""
    name = report.get('name', f'Deck #{report["deck_id"]}')
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  Deck #{report['deck_id']}")
    print(f"{'='*60}")
    print(f"  Cards: {report['total_cards']} total, "
          f"{report['ok']} OK, "
          f"{report['with_issues']} with issues, "
          f"{report['total_warnings']} warnings")

    if report['with_issues'] == 0 and report['total_warnings'] == 0:
        print(f"  ✅ All cards have complete data!")
        return

    # Sort by priority
    cards = sorted(report.get('cards', []), key=_card_priority)

    for card in cards:
        warnings = card.get('warnings', [])
        issues = card.get('issues', [])
        tipo = card.get('tipo', '?').lower()

        if critical_only and tipo not in CRITICAL_TIPOS:
            continue

        if card['status'] == 'missing':
            print(f"  ❌ MISSING  codevdb={card['codevdb']}")
            continue

        status_icon = '⚠️' if warnings else '✅'
        if issues:
            status_icon = '❌'

        if verbose:
            print(f"  {status_icon} {card['name']:35} [{card['tipo']:20}] "
                  f"ab={card['abilities_count']} mod={card['modifiers_count']} "
                  f"strike={'Y' if card['has_default_strike'] else 'N'}")
            for w in warnings:
                print(f"      ⚠  {w}")
            for issue in issues:
                print(f"      ❌  {issue}")
        elif warnings or issues or critical_only:
            if warnings and not issues:
                pass  # skip minor warnings in non-verbose mode
            else:
                print(f"  {status_icon} {card['name']:35} [{card['tipo']:20}] "
                      f"ab={card['abilities_count']} mod={card['modifiers_count']}")


def main():
    parser = argparse.ArgumentParser(
        description='Validate card data completeness for simulation decks'
    )
    parser.add_argument('--deck', type=int, help='Specific deck ID to validate')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output for all cards')
    parser.add_argument('--critical-only', '-c', action='store_true',
                        help='Only show combat/action/reaction/equipment cards')
    args = parser.parse_args()

    if args.deck:
        reports = [validate_deck(args.deck)]
    else:
        reports = validate_all_decks()

    for report in reports:
        print_report(report, verbose=args.verbose, critical_only=args.critical_only)

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")

    total_ok = sum(r['ok'] for r in reports)
    total_issues = sum(r['with_issues'] for r in reports)
    total_warnings = sum(r['total_warnings'] for r in reports)
    total_cards = sum(r['total_cards'] for r in reports)

    print(f"  Decks validated: {len(reports)}")
    print(f"  Total cards:     {total_cards}")
    print(f"  OK:              {total_ok} ({100*total_ok//max(total_cards,1)}%)")
    print(f"  With issues:     {total_issues}")
    print(f"  Warnings:        {total_warnings}")

    if total_issues == 0:
        print(f"\n  ✅ All decks ready for simulation!")
    else:
        print(f"\n  ⚠️  {total_issues} cards need attention")

    return 0 if total_issues == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
