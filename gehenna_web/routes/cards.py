from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import Optional

from gehenna_web.services import api_client

bp = Blueprint('cards', __name__, url_prefix='/cards')

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
    if name or code or tipo:
        response = api_client.get_cards(name=name, code=code, tipo=tipo)
        if response.status_code == 200:
            data = response.json()
            cards = data.get('cards', [])

    return render_template('cards/search.html', form=form, cards=cards, name=name, code=code, tipo=tipo)


@bp.route('/<int:card_id>')
def detail(card_id):
    response = api_client.get_card(card_id)
    card = None
    if response.status_code == 200:
        card = response.json()
    return render_template('cards/detail.html', card=card)