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


@bp.route('/deck/<deck_id>')
def deck_detail(deck_id):
    response = api_client.get_twda_deck(deck_id)
    deck = None
    if response.status_code == 200:
        deck = response.json()

    return render_template('trends/deck_detail.html', deck=deck, deck_id=deck_id)


@bp.route('/deck/<deck_id>/import', methods=['POST'])
@login_required
def import_deck(deck_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('auth.login'))

    response = api_client.import_twda_deck(deck_id, user_id)

    if response.status_code == 200:
        data = response.json()
        flash(f"Deck imported: {data.get('name')}", 'success')
        return redirect(url_for('decks.my_decks'))
    else:
        flash('Failed to import deck', 'error')
        return redirect(url_for('trends.deck_detail', deck_id=deck_id))


@bp.route('/recommendations')
@login_required
def recommendations():
    limit = request.args.get('limit', 20, type=int)
    format = request.args.get('format')
    year_start = request.args.get('year_start', type=int)
    year_end = request.args.get('year_end', type=int)
    min_completeness = request.args.get('min_completeness', 0.1, type=float)

    decks = []
    total_analyzed = 0
    total_trending = 0

    response = api_client.get_trend_recommendations(
        session.get('username'),
        limit=limit,
        format=format,
        year_start=year_start,
        year_end=year_end,
        min_completeness=min_completeness,
    )

    if response.status_code == 200:
        data = response.json()
        decks = data.get('decks', [])
        total_analyzed = data.get('total_analyzed', 0)
        total_trending = data.get('total_trending', 0)

    return render_template(
        'trends/recommendations.html',
        decks=decks,
        total_analyzed=total_analyzed,
        total_trending=total_trending,
        limit=limit,
        format=format,
        year_start=year_start,
        year_end=year_end,
        min_completeness=min_completeness,
    )


@bp.route('/auto-import', methods=['POST'])
@login_required
def auto_import():
    limit_decks = request.form.get('limit_decks', 5, type=int)
    min_card_overlap = request.form.get('min_card_overlap', 5, type=int)

    username = session.get('username')
    response = api_client.auto_import_decks(username, limit_decks, min_card_overlap)

    if response.status_code == 200:
        data = response.json()
        imported = data.get('decks', [])
        if imported:
            msg = f"Imported {len(imported)} decks: " + ", ".join(
                [d.get('name', '') for d in imported[:3]]
            )
            flash(msg, 'success')
        else:
            flash("No decks to import (increase min_card_overlap)", 'warning')
    else:
        flash('Failed to auto-import decks', 'error')

    return redirect(url_for('decks.my_decks'))