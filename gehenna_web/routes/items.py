from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired

from gehenna_web.routes.auth import login_required
from gehenna_web.services import api_client

bp = Blueprint('items', __name__, url_prefix='/items')


class ItemForm(FlaskForm):
    moviment_id = IntegerField('Moviment ID', validators=[DataRequired()])
    card_id = IntegerField('Card ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    code = IntegerField('Code')
    submit = SubmitField('Save')


@bp.route('/<int:moviment_id>')
@login_required
def list(moviment_id):
    response = api_client.get_items(moviment_id)
    items = []
    if response.status_code in (200, 201):
        data = response.json()
        items = data.get('items', [])
    return render_template('items/list.html', items=items, moviment_id=moviment_id)


@bp.route('/<int:moviment_id>/create', methods=['GET', 'POST'])
@login_required
def create(moviment_id):
    form = ItemForm()
    if form.validate_on_submit():
        data = {
            'moviment_id': form.moviment_id.data,
            'card_id': form.card_id.data,
            'quantity': form.quantity.data,
            'code': form.code.data or 0,
        }
        response = api_client.create_item(data)
        if response.status_code == 201:
            flash('Item added', 'success')
            return redirect(url_for('items.list', moviment_id=moviment_id))
        flash('Error adding item', 'error')
    return render_template('items/form.html', form=form, moviment_id=moviment_id, title='Add Item')


@bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    form = ItemForm()
    response = api_client.get_item(item_id)
    if response.status_code == 200:
        item = response.json()
        moviment_id = item.get('moviment_id')
    else:
        moviment_id = request.args.get('moviment_id', 0, type=int)

    if request.method == 'GET' and response.status_code == 200:
        item = response.json()
        form.moviment_id.data = item.get('moviment_id')
        form.card_id.data = item.get('card_id')
        form.quantity.data = item.get('quantity')
        form.code.data = item.get('code')

    if form.validate_on_submit():
        data = {'quantity': form.quantity.data}
        response = api_client.update_item(item_id, data)
        if response.status_code == 200:
            flash('Item updated', 'success')
            return redirect(url_for('items.list', moviment_id=moviment_id))
        flash('Error updating item', 'error')

    return render_template('items/form.html', form=form, moviment_id=moviment_id, title='Edit Item')


@bp.route('/<int:item_id>/delete')
@login_required
def delete(item_id):
    moviment_id = request.args.get('moviment_id', 0, type=int)
    response = api_client.delete_item(item_id)
    if response.status_code == 200:
        flash('Item removed', 'success')
    else:
        flash('Error removing item', 'error')
    return redirect(url_for('items.list', moviment_id=moviment_id))