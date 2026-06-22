from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired

from gehenna_web.routes.auth import login_required
from gehenna_web.services import api_client

bp = Blueprint('moviments', __name__, url_prefix='/moviments')


class MovimentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    tipo = SelectField('Type', choices=[('E', 'Entry (E)'), ('S', 'Sale (S)')], validators=[DataRequired()])
    date_move = StringField('Date (YYYY-MM-DD)', validators=[DataRequired()])
    price = DecimalField('Price', validators=[InputRequired()])
    code = IntegerField('Code')
    submit = SubmitField('Save')


@bp.route('/')
@login_required
def list():
    username = session.get('username')
    tipo = request.args.get('tipo')
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    response = api_client.get_moviments(username, tipo=tipo, skip=skip, limit=per_page + 1)
    moviments = []
    has_next = False
    if response.status_code == 200:
        data = response.json()
        all_moviments = data.get('moviments', [])
        if len(all_moviments) > per_page:
            moviments = all_moviments[:per_page]
            has_next = True
        else:
            moviments = all_moviments
    return render_template('moviments/list.html', moviments=moviments, username=username, page=page, has_next=has_next, tipo=tipo)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = MovimentForm()
    form.date_move.data = date.today().isoformat()
    form.code.data = 0
    if form.validate_on_submit():
        data = {
            'name': form.name.data,
            'tipo': form.tipo.data,
            'date_move': form.date_move.data,
            'price': float(form.price.data),
            'code': form.code.data or 0,
            'owner_id': session.get('user_id')
        }
        response = api_client.create_moviment(data)
        if response.status_code == 201:
            flash('Moviment created', 'success')
            return redirect(url_for('moviments.list'))
        flash('Error creating moviment', 'error')
    return render_template('moviments/form.html', form=form, title='Create Moviment')


@bp.route('/<int:moviment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(moviment_id):
    form = MovimentForm()
    if request.method == 'GET':
        from gehenna_web.services.api_client import api
        response = api.get(f'/stocks/moviment/{moviment_id}')
        if response.status_code == 200:
            moviment = response.json()
            form.name.data = moviment.get('name')
            form.tipo.data = moviment.get('tipo')
            form.date_move.data = moviment.get('date_move')
            price_val = moviment.get('price')
            if price_val is not None:
                form.price.data = float(price_val)
            form.code.data = moviment.get('code')

    if form.validate_on_submit():
        data = {
            'name': form.name.data,
            'tipo': form.tipo.data,
            'date_move': form.date_move.data,
            'price': float(form.price.data),
            'code': form.code.data or 0,
            'owner_id': session.get('user_id')
        }
        response = api_client.update_moviment(moviment_id, data)
        if response.status_code == 200:
            flash('Moviment updated', 'success')
            return redirect(url_for('moviments.list'))
        flash('Error updating moviment', 'error')

    return render_template('moviments/form.html', form=form, title='Edit Moviment')


@bp.route('/<int:moviment_id>/delete')
@login_required
def delete(moviment_id):
    response = api_client.delete_moviment(moviment_id)
    if response.status_code == 200:
        flash('Moviment deleted', 'success')
    else:
        flash('Error deleting moviment', 'error')
    return redirect(url_for('moviments.list'))


@bp.route('/<int:moviment_id>')
@login_required
def detail(moviment_id):
    from gehenna_web.services.api_client import api
    response = api.get(f'/stocks/moviment/{moviment_id}')
    moviment = None
    if response.status_code == 200:
        moviment = response.json()
    return render_template('moviments/detail.html', moviment=moviment)


@bp.route('/statistics')
@login_required
def statistics():
    owner_id = session.get('user_id')
    response = api_client.get_statistics(owner_id=owner_id)
    stats = {}
    if response.status_code == 200:
        stats = response.json()
    return render_template('moviments/statistics.html', stats=stats)