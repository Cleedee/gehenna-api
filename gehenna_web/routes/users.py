from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

from gehenna_web.routes.auth import login_required
from gehenna_web.services import api_client

bp = Blueprint('users', __name__, url_prefix='/users')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password')
    submit = SubmitField('Save')


@bp.route('/')
@login_required
def list():
    response = api_client.get_users()
    users = []
    if response.status_code == 200:
        data = response.json()
        users = data.get('users', [])
    return render_template('users/list.html', users=users)


@bp.route('/<username>')
def profile(username):
    response = api_client.get_user(username)
    user = None
    if response.status_code == 200:
        user = response.json()
    return render_template('users/profile.html', user=user)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = UserForm()
    if form.validate_on_submit():
        data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': form.password.data
        }
        response = api_client.create_user(data)
        if response.status_code == 201:
            flash('User created', 'success')
            return redirect(url_for('users.list'))
        flash('Error creating user', 'error')
    return render_template('users/form.html', form=form, title='Create User')


@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(user_id):
    form = UserForm()
    if request.method == 'GET':
        response = api_client.get_user_by_id(user_id)
        if response.status_code == 200:
            user = response.json()
            form.username.data = user.get('username')
            form.email.data = user.get('email')

    if form.validate_on_submit():
        data = {
            'username': form.username.data,
            'email': form.email.data
        }
        if form.password.data:
            data['password'] = form.password.data
        response = api_client.update_user(user_id, data)
        if response.status_code == 200:
            flash('User updated', 'success')
            return redirect(url_for('users.list'))
        flash('Error updating user', 'error')

    return render_template('users/form.html', form=form, title='Edit User')