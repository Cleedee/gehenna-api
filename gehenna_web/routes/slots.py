from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional

from gehenna_web.routes.auth import login_required
from gehenna_web.services import api_client

bp = Blueprint('slots', __name__, url_prefix='/slots')


class SlotForm(FlaskForm):
    card_id = HiddenField('Card ID')
    card_name = StringField('Card Name')
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    code = IntegerField('Code', validators=[Optional()])
    submit = SubmitField('Save')


def resolve_card_id(card_name):
    """Resolve a card name to its id via the API, returning None on failure."""
    if not card_name:
        return None
    response = api_client.get_card_by_name(card_name)
    if response.status_code == 200:
        card = response.json()
        return card.get('id')
    return None


def _fetch_card(card_id):
    response = api_client.get_card(card_id)
    if response.status_code == 200:
        return response.json()
    return None


@bp.route('/<int:deck_id>')
@login_required
def list(deck_id):
    response = api_client.get_slots(deck_id)
    slots = []
    if response.status_code in (200, 201):
        data = response.json()
        slots = data.get('slots', [])
    return render_template('slots/list.html', slots=slots, deck_id=deck_id)


@bp.route('/<int:deck_id>/create', methods=['GET', 'POST'])
@login_required
def create(deck_id):
    form = SlotForm()
    if form.validate_on_submit():
        card_id = form.card_id.data or resolve_card_id(form.card_name.data)
        if not card_id:
            flash('Select a valid card from the suggestions', 'error')
            return render_template(
                'slots/form.html',
                form=form,
                deck_id=deck_id,
                title='Add Card to Deck',
            )
        data = {
            'deck_id': deck_id,
            'card_id': int(card_id),
            'quantity': form.quantity.data,
            'code': form.code.data or 0,
        }
        response = api_client.create_slot(data)
        if response.status_code == 201:
            flash('Card added to deck', 'success')
            return redirect(url_for('slots.list', deck_id=deck_id))
        flash('Error adding card', 'error')
    return render_template(
        'slots/form.html',
        form=form,
        deck_id=deck_id,
        title='Add Card to Deck',
    )


@bp.route('/<int:slot_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(slot_id):
    form = SlotForm()
    response = api_client.get_slot(slot_id)
    if response.status_code == 200:
        slot = response.json()
        deck_id = slot.get('deck_id')
    else:
        deck_id = request.args.get('deck_id', 0, type=int)
        slot = None

    selected_card = None
    if request.method == 'GET' and slot:
        form.card_id.data = slot.get('card_id')
        form.quantity.data = slot.get('quantity')
        form.code.data = slot.get('code')
        selected_card = _fetch_card(slot.get('card_id'))
        if selected_card:
            form.card_name.data = selected_card.get('name')

    if form.validate_on_submit():
        data = {'quantity': form.quantity.data}
        response = api_client.update_slot(slot_id, data)
        if response.status_code == 200:
            flash('Slot updated', 'success')
            return redirect(url_for('slots.list', deck_id=deck_id))
        flash('Error updating slot', 'error')

    return render_template(
        'slots/form.html',
        form=form,
        deck_id=deck_id,
        title='Edit Slot',
        selected_card=selected_card,
    )


@bp.route('/<int:slot_id>/delete')
@login_required
def delete(slot_id):
    deck_id = request.args.get('deck_id', 0, type=int)
    response = api_client.delete_slot(slot_id)
    if response.status_code == 200:
        flash('Card removed from deck', 'success')
    else:
        flash('Error removing card', 'error')
    return redirect(url_for('slots.list', deck_id=deck_id))