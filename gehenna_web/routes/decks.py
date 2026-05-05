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
    tags = StringField('Tags')
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
            'tags': form.tags.data or '',
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
            form.tags.data = deck.get('tags', '')
            form.preconstructed.data = deck.get('preconstructed')
            form.code.data = deck.get('code')

    if form.validate_on_submit():
        data = {
            'name': form.name.data,
            'description': form.description.data,
            'creator': form.creator.data,
            'player': form.player.data,
            'tipo': form.tipo.data,
            'tags': form.tags.data or '',
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


@bp.route('/<int:deck_id>/missing')
def missing_cards(deck_id):
    username = session.get('username')
    response = api_client.get_deck(deck_id)
    deck = None
    if response.status_code == 200:
        deck = response.json()

    missing = {'cards': [], 'total': 0}
    if username:
        response = api_client.get_missing_cards(deck_id, username)
        if response.status_code == 200:
            data = response.json()
            cards = data.get('cards', [])
            for card in cards:
                response = api_client.get_preconstructed_decks_with_card(card['card_id'])
                if response.status_code == 200:
                    card['preconstructed_decks'] = response.json().get('decks', [])
                else:
                    card['preconstructed_decks'] = []
            missing = {'cards': cards, 'total': data.get('total', 0)}

    return render_template('decks/missing.html', deck=deck, missing=missing)


@bp.route('/import-vdb', methods=['GET', 'POST'])
@login_required
def import_vdb():
    form = VDBImportForm()
    if form.validate_on_submit():
        deck_id = form.deck_id.data
        owner_id = session.get('user_id')
        response = api_client.import_vdb_deck(deck_id, owner_id)
        if response.status_code == 200:
            data = response.json()
            flash(f"Deck imported: {data.get('name')} ({data.get('cards_imported')} cards)", 'success')
            return redirect(url_for('decks.my_decks'))
        flash('Error importing deck', 'error')
    return render_template('decks/import_vdb.html', form=form)


class VDBImportForm(FlaskForm):
    deck_id = StringField('VDB Deck ID', validators=[DataRequired()], description='Ex: 8c46348db')
    submit = SubmitField('Import')


@bp.route('/<int:deck_id>/import', methods=['GET', 'POST'])
@login_required
def import_to_moviment(deck_id):
    response = api_client.get_deck(deck_id)
    deck = None
    if response.status_code == 200:
        deck = response.json()

    if not deck or deck.get('owner_id') != session.get('user_id'):
        flash('Deck not found or not yours', 'error')
        return redirect(url_for('decks.my_decks'))

    if request.method == 'POST':
        date_move = request.form.get('date_move')
        price = float(request.form.get('price') or 0)
        owner_id = session.get('user_id')
        response = api_client.create_moviment_from_deck(
            deck_id=deck_id,
            owner_id=owner_id,
            date_move=date_move,
            price=price,
        )
        if response.status_code == 201:
            data = response.json()
            flash(f"Moviment created: {data.get('total_cards')} cards imported", 'success')
            return redirect(url_for('moviments.list'))
        flash('Error creating moviment', 'error')

    from datetime import date
    return render_template('decks/import.html', deck=deck, today=date.today().isoformat())