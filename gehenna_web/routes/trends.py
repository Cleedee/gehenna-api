from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from functools import wraps

from gehenna_web.services import api_client

bp = Blueprint('trends', __name__, url_prefix='/trends')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/recommendations')
@login_required
def recommendations():
    limit = request.args.get('limit', 20, type=int)
    format = request.args.get('format')
    year = request.args.get('year', type=int)

    cards = []
    gaps = []
    total_trending = 0
    example_decks = []

    response = api_client.get_trend_recommendations(
        session.get('username'),
        limit=limit,
        format=format,
        year=year
    )

    if response.status_code == 200:
        data = response.json()
        cards = data.get('cards', [])
        gaps = data.get('gaps', [])
        total_trending = data.get('total_trending', 0)
        example_decks = data.get('example_decks', [])

    return render_template(
        'trends/recommendations.html',
        cards=cards,
        gaps=gaps,
        total_trending=total_trending,
        example_decks=example_decks,
        limit=limit,
        format=format,
        year=year
    )