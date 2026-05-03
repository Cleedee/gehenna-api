from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from gehenna_web.routes.auth import login_required
from gehenna_web.services import api_client

bp = Blueprint('decks', __name__, url_prefix='/decks')


class DeckForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    creator = StringField('Creator')
    player = StringField('Player')
    tipo = StringField('Type', validators=[DataRequired()])
    preconstructed = BooleanField('Preconstructed')
    code = IntegerField('Code')
    submit = SubmitField('Save')


@bp.route('/')
def list():
    username = request.args.get('username')
    name = request.args.get('name')
    card_name = request.args.get('card_name')
    code = request.args.get('code')
    preconstructed = request.args.get('preconstructed')

    response = api_client.get_decks(
        username=username,
        name=name,
        card_name=card_name,
        code=code,
        preconstructed=preconstructed
    )
    decks = []
    if response.status_code == 200:
        data = response.json()
        decks = data.get('decks', [])
    return render_template('decks/list.html', decks=decks, username=username)


@bp.route('/my')
@login_required
def my_decks():
    username = session.get('username')
    response = api_client.get_decks(username=username)
    decks = []
    if response.status_code == 200:
        data = response.json()
        decks = data.get('decks', [])
    return render_template('decks/list.html', decks=decks, username=username)


@bp.route('/<int:deck_id>')
def detail(deck_id):
    response = api_client.get_deck(deck_id)
    deck = None
    if response.status_code == 200:
        deck = response.json()
    return render_template('decks/detail.html', deck=deck)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = DeckForm()
    if form.validate_on_submit():
        data = {
            'name': form.name.data,
            'description': form.description.data,
            'creator': form.creator.data,
            'player': form.player.data,
            'tipo': form.tipo.data,
            'preconstructed': form.preconstructed.data,
            'code': form.code.data,
            'owner_id': session.get('user_id'),
            'created': date.today().isoformat()
        }
        response = api_client.create_deck(data)
        if response.status_code == 201:
            flash('Deck created', 'success')
            return redirect(url_for('decks.my_decks'))
        flash('Error creating deck', 'error')
    return render_template('decks/form.html', form=form, title='Create Deck')


@bp.route('/<int:deck_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(deck_id):
    form = DeckForm()
    if request.method == 'GET':
        response = api_client.get_deck(deck_id)
        if response.status_code == 200:
            deck = response.json()
            form.name.data = deck.get('name')
            form.description.data = deck.get('description')
            form.creator.data = deck.get('creator')
            form.player.data = deck.get('player')
            form.tipo.data = deck.get('tipo')
            form.preconstructed.data = deck.get('preconstructed')
            form.code.data = deck.get('code')

    if form.validate_on_submit():
        data = {
            'name': form.name.data,
            'description': form.description.data,
            'creator': form.creator.data,
            'player': form.player.data,
            'tipo': form.tipo.data,
            'preconstructed': form.preconstructed.data,
            'code': form.code.data,
            'owner_id': session.get('user_id')
        }
        response = api_client.update_deck(deck_id, data)
        if response.status_code == 200:
            flash('Deck updated', 'success')
            return redirect(url_for('decks.detail', deck_id=deck_id))
        flash('Error updating deck', 'error')

    return render_template('decks/form.html', form=form, title='Edit Deck')


@bp.route('/<int:deck_id>/delete')
@login_required
def delete(deck_id):
    response = api_client.delete_deck(deck_id)
    if response.status_code == 200:
        flash('Deck deleted', 'success')
    else:
        flash('Error deleting deck', 'error')
    return redirect(url_for('decks.my_decks'))