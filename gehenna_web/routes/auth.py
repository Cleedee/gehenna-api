from flask import Blueprint, Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

from gehenna_web.services import api_client

bp = Blueprint('auth', __name__, url_prefix='/auth')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        result = api_client.login(username, password)
        if result:
            session['access_token'] = result.get('access_token')
            session['username'] = result.get('username')
            session['user_id'] = result.get('id')
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials', 'error')
    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': form.password.data
        }
        response = api_client.create_user(data)
        if response.status_code == 201:
            flash('Account created, please login', 'success')
            return redirect(url_for('auth.login'))
        flash('Registration failed', 'error')
    return render_template('auth/register.html', form=form)


@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function