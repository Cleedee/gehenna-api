from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import Optional

from gehenna_web.services import api_client

bp = Blueprint('cards', __name__, url_prefix='/cards')

KRCG_BASE = 'https://static.krcg.org'

CLAN_ICONS = {
    'brujah': 'brujah',
    'gangrel': 'gangrel',
    'malkavian': 'malkavian',
    'nosferatu': 'nosferatu',
    'tremere': 'tremere',
    'ventrue': 'ventrue',
    'assamite': 'assamite',
    'baali': 'baali',
    'caitiff': 'caitiff',
    'giovanni': 'giovanni',
    'harbingerofskulls': 'harbinger',
    'lasombra': 'lasombra',
    'ravnos': 'ravnos',
    'sette': 'sette',
    'toreador': 'toreador',
    'tzimisce': 'tzimisce',
    'ventrueantitribu': 'ventrueantitribu',
    'brujahantitribu': 'brujahantitribu',
    'gangrelantitribu': 'gangrelantitribu',
    'malkavianantitribu': 'malkavianantitribu',
    'nosferatuantitribu': 'nosferatuantitribu',
    'tremereantitribu': 'tremereantitribu',
    'toreadorantitribu': 'toreadorantitribu',
    'salubri': 'salubri',
    'hecata': 'hecata',
    'hecataantitribu': 'hecataantitribu',
    'bonny': 'bonny',
    'defender': 'defender',
    'oblivion': 'oblivion',
}

DISCIPLINE_ICONS = {
    'ani': ('ani', False),
    'ANI': ('ani', True),
    'aus': ('aus', False),
    'AUS': ('aus', True),
    'cel': ('cel', False),
    'CEL': ('cel', True),
    'dom': ('dom', False),
    'DOM': ('dom', True),
    'for': ('for', False),
    'FOR': ('for', True),
    'mel': ('mel', False),
    'MEL': ('mel', True),
    'nec': ('nec', False),
    'NEC': ('nec', True),
    'obf': ('obf', False),
    'OBF': ('obf', True),
    'obl': ('obl', False),
    'OBL': ('obl', True),
    'pot': ('pot', False),
    'POT': ('pot', True),
    'pre': ('pre', False),
    'PRE': ('pre', True),
    'pro': ('pro', False),
    'PRO': ('pro', True),
    'qui': ('qui', False),
    'QUI': ('qui', True),
    'san': ('san', False),
    'SAN': ('san', True),
    'ser': ('ser', False),
    'SER': ('ser', True),
    'tha': ('tha', False),
    'THA': ('tha', True),
    'thn': ('thn', False),
    'THN': ('thn', True),
    'vic': ('vic', False),
    'VIC': ('vic', True),
    'vin': ('vin', False),
    'VIN': ('vin', True),
    'flight': ('flight', False),
    'maleficia': ('maleficia', False),
    'striga': ('striga', False),
}


def get_clan_icon_url(clan: str) -> str | None:
    if not clan:
        return None
    clan_lower = clan.lower().replace(' ', '').replace("'", '').replace('-', '')
    filename = CLAN_ICONS.get(clan_lower)
    if filename:
        return f'{KRCG_BASE}/png/{filename}.png'
    return None


def get_discipline_icons(disciplines: str) -> list[dict]:
    if not disciplines:
        return []
    icons = []
    for disc in disciplines.split('|'):
        disc = disc.strip()
        if not disc:
            continue
        if disc in DISCIPLINE_ICONS:
            name, superior = DISCIPLINE_ICONS[disc]
            folder = 'sup' if superior else 'inf'
            icons.append({
                'name': name.upper(),
                'superior': superior,
                'url': f'{KRCG_BASE}/png/{folder}/{name}.png'
            })
    return icons


def get_cost_icon(cost: str) -> dict | None:
    if not cost:
        return None
    cost_lower = cost.lower().strip()
    if cost_lower.startswith('x') or cost_lower == 'x':
        return {'type': 'blood', 'url': f'{KRCG_BASE}/png/icon/xblood.png', 'value': cost}
    elif cost_lower.startswith('+'):
        return {'type': 'pool', 'url': f'{KRCG_BASE}/png/icon/pluspool.png', 'value': cost}
    elif cost_lower.isdigit():
        return {'type': 'pool', 'url': f'{KRCG_BASE}/png/icon/blood.png', 'value': cost}
    return None


def process_card_icons(card: dict) -> dict:
    card = dict(card)
    clan = card.get('clan', '')
    disciplines = card.get('disciplines', '')
    card['clan_icon_url'] = get_clan_icon_url(clan)
    card['discipline_icons'] = get_discipline_icons(disciplines)
    return card


CARD_TYPES = [
    ('', 'All Types'),
    ('Vampire', 'Vampire'),
    ('Master', 'Master'),
    ('Action', 'Action'),
    ('Combat', 'Combat'),
    ('Action Modifier', 'Action Modifier'),
    ('Political Action', 'Political Action'),
    ('Equipment', 'Equipment'),
    ('Reaction', 'Reaction'),
    ('Ally', 'Ally'),
    ('Retainer', 'Retainer'),
    ('Event', 'Event'),
    ('Imbued', 'Imbued'),
]


class SearchForm(FlaskForm):
    name = StringField('Card Name', validators=[Optional()])
    code = StringField('Card Code', validators=[Optional()])
    tipo = SelectField('Type', choices=CARD_TYPES, default='')
    submit = SubmitField('Search')


@bp.route('/')
def search():
    form = SearchForm()
    name = request.args.get('name')
    code = request.args.get('code')
    tipo = request.args.get('tipo')

    if request.args.get('form.name'):
        form.name.data = request.args.get('form.name')
    if request.args.get('form.tipo'):
        form.tipo.data = request.args.get('form.tipo')

    cards = []
    response = api_client.get_cards(name=name, code=code, tipo=tipo, limit=50)
    if response.status_code == 200:
        data = response.json()
        cards = [process_card_icons(c) for c in data.get('cards', [])]

    return render_template('cards/search.html', form=form, cards=cards, name=name, code=code, tipo=tipo)


@bp.route('/<int:card_id>')
def detail(card_id):
    response = api_client.get_card(card_id)
    card = None
    if response.status_code == 200:
        card = response.json()

    card_image_url = None
    prices = []
    clan_icon_url = None
    discipline_icons = []
    cost_icon = None
    if card and card.get('name'):
        card_image_url = api_client.get_card_image_url(
            card['name'], 'webp',
            group=card.get('group'),
            advanced=card.get('avancado')
        )
        price_data = api_client.search_joestock_prices(card['name'])
        if price_data.get('success'):
            prices = price_data.get('results', [])
        clan_icon_url = get_clan_icon_url(card.get('clan'))
        discipline_icons = get_discipline_icons(card.get('disciplines'))
        cost_icon = get_cost_icon(card.get('cost'))

    return render_template(
        'cards/detail.html',
        card=card,
        prices=prices,
        card_image_url=card_image_url,
        clan_icon_url=clan_icon_url,
        discipline_icons=discipline_icons,
        cost_icon=cost_icon
    )