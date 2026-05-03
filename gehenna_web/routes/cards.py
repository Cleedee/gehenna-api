from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional

from gehenna_web.services import api_client

bp = Blueprint('cards', __name__, url_prefix='/cards')


class SearchForm(FlaskForm):
    name = StringField('Card Name', validators=[Optional()])
    code = StringField('Card Code', validators=[Optional()])
    submit = SubmitField('Search')


@bp.route('/')
def search():
    form = SearchForm()
    name = request.args.get('name')
    code = request.args.get('code')

    cards = []
    if name or code:
        response = api_client.get_cards(name=name, code=code)
        if response.status_code == 200:
            data = response.json()
            cards = data.get('cards', [])

    return render_template('cards/search.html', form=form, cards=cards, name=name, code=code)


@bp.route('/<int:card_id>')
def detail(card_id):
    response = api_client.get_card(card_id)
    card = None
    if response.status_code == 200:
        card = response.json()
    return render_template('cards/detail.html', card=card)