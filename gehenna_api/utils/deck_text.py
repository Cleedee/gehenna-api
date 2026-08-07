"""Parse V:TES deck text lists (VDB/TWDA style).

Example input:

    Deck Name: Tô com o Sombra aí ó.

    Autor: Thyago

    Crypt(12 cards, min=13, max=28, avg=5.30)
    -----------------------------------------
    2x Parijat, the Dark Oracle      7  AUS DOM FOR OBL      Hecata:6
    ...

    Library (90 cards)
    Master (16; 2 trifle)
    5x Villein
    ...

The parser produces a dict with the deck name, author, description and the
crypt/library cards (quantity, name and extra crypt columns).
"""

import re

_CARD_RE = re.compile(r'^\s*(\d+)\s*[xX×]\s*(.+?)\s*$')
_PLAIN_CARD_RE = re.compile(r'^\s*(\d+)\s+(\S.*?)\s*$')
_SECTION_RE = re.compile(r'^\s*([A-Za-z][A-Za-z /-]*?)\s*\(\s*\d')
_SEPARATOR_RE = re.compile(r'^\s*[-=]{3,}\s*$')


def _parse_card_line(line: str) -> tuple[int, str] | None:
    """Extract (quantity, name) from a line like ``5x Villein``."""
    match = _CARD_RE.match(line)
    if match:
        return int(match.group(1)), match.group(2).strip()
    match = _PLAIN_CARD_RE.match(line)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None


def _parse_crypt_line(line: str) -> dict:
    """Parse a crypt line with quantity, name and extra columns."""
    parsed = _parse_card_line(line)
    if parsed is None:
        return {}
    qty, rest = parsed

    parts = re.split(r'\s{2,}', rest)
    name = parts[0].strip()
    body = [p.strip() for p in parts[1:] if p.strip()]

    capacity = ''
    # Capacity is usually its own column, but may be merged with the
    # disciplines (single space), e.g. "11 AUS FOR OBE THA VAL".
    if body:
        tokens = body[0].split()
        if tokens and tokens[0].isdigit():
            capacity = tokens[0]
            body[0] = ' '.join(tokens[1:])
    body = [b for b in body if b]

    clan = ''
    group = ''
    if body and ':' in body[-1]:
        clan, _, group = body[-1].partition(':')
        body = body[:-1]

    disciplines = ' '.join(body)

    return {
        'name': name,
        'quantity': qty,
        'capacity': capacity,
        'disciplines': disciplines,
        'clan': clan.strip(),
        'group': group.strip(),
    }


def parse_deck_text(text: str) -> dict:
    """Parse V:TES deck text into a structured dict."""
    deck = {
        'name': '',
        'author': '',
        'description': '',
        'crypt': [],
        'library': [],
    }

    section = None          # 'crypt' | 'library' | None
    library_tipo = ''
    description_lines = []
    in_description = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if _SEPARATOR_RE.match(line):
            continue
        if not line.strip():
            if in_description:
                in_description = False
            continue

        if in_description:
            description_lines.append(line)
            continue

        lower = line.strip().lower()
        name_match = re.match(
            r'^\s*Deck\s+Name\s*:\s*(.+?)\s*$', line, re.IGNORECASE
        )
        if name_match:
            deck['name'] = name_match.group(1).strip()
            continue

        author_match = re.match(
            r'^\s*(?:Autor|Author|Player)\s*:\s*(.+?)\s*$', line, re.IGNORECASE
        )
        if author_match:
            deck['author'] = author_match.group(1).strip()
            continue

        if re.match(r'^\s*Description\s*:\s*$', line, re.IGNORECASE):
            in_description = True
            continue

        if 'crypt' in lower and '(' in line:
            section = 'crypt'
            library_tipo = ''
            continue
        if 'library' in lower and '(' in line:
            section = 'library'
            library_tipo = ''
            continue

        if section == 'crypt':
            card = _parse_crypt_line(line)
            if card:
                deck['crypt'].append(card)
            continue

        if section == 'library':
            section_match = _SECTION_RE.match(line)
            if section_match:
                library_tipo = section_match.group(1).strip()
                continue
            card = _parse_card_line(line)
            if card:
                deck['library'].append(
                    {
                        'name': card[1],
                        'quantity': card[0],
                        'tipo': library_tipo,
                    }
                )
                continue

    if description_lines:
        deck['description'] = '\n'.join(description_lines).strip()

    return deck
