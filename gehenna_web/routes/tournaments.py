from flask import Blueprint, flash, redirect, render_template, request, session, url_for, jsonify
from flask import make_response
from functools import wraps

from gehenna_web.services import api_client

bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def _make_cache_headers(response):
    """Add no-cache headers to prevent stale data."""
    if not isinstance(response, type(make_response(''))):
        return response
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@bp.route('/')
@login_required
def list_tournaments():
    year = request.args.get('year', type=int)
    format = request.args.get('format')
    limit = request.args.get('limit', 50, type=int)

    response = api_client.get_tournaments(year=year, format=format, limit=limit)
    tournaments = []
    if response.status_code == 200:
        tournaments = response.json()

    resp = make_response(render_template(
        'tournaments/list.html',
        tournaments=tournaments,
        year=year,
        format=format,
    ))
    return _make_cache_headers(resp)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_tournament():
    if request.method == 'POST':
        data = _parse_tournament_form(request.form)
        if data:
            response = api_client.create_tournament(data)
            if response.status_code == 201:
                t = response.json()
                flash(f'Tournament "{t["name"]}" created successfully!', 'success')
                return redirect(url_for('tournaments.detail', tournament_id=t['id']))
            else:
                flash(f'Error creating tournament: {response.text}', 'danger')
        else:
            flash('Please fill in required fields', 'danger')

    clans = api_client.get_tournament_clans()
    return render_template('tournaments/form.html', tournament=None, clans=clans)


@bp.route('/<int:tournament_id>')
@login_required
def detail(tournament_id):
    response = api_client.get_tournament(tournament_id)
    if response.status_code != 200:
        flash('Tournament not found', 'danger')
        return redirect(url_for('tournaments.list_tournaments'))

    data = response.json()
    resp = make_response(render_template('tournaments/detail.html', tournament=data))
    return _make_cache_headers(resp)


@bp.route('/<int:tournament_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_tournament(tournament_id):
    response = api_client.get_tournament(tournament_id)
    if response.status_code != 200:
        flash('Tournament not found', 'danger')
        return redirect(url_for('tournaments.list_tournaments'))

    tournament = response.json()

    if request.method == 'POST':
        # Update basic info
        update_data = {
            'name': request.form.get('name'),
            'date': request.form.get('date'),
            'location': request.form.get('location', ''),
            'format': request.form.get('format', ''),
            'total_players': int(request.form.get('total_players', 0)),
            'notes': request.form.get('notes', ''),
        }
        api_client.update_tournament(tournament_id, update_data)
        flash('Tournament updated!', 'success')
        return redirect(url_for('tournaments.detail', tournament_id=tournament_id))

    clans = api_client.get_tournament_clans()
    return render_template('tournaments/form.html', tournament=tournament, clans=clans)


@bp.route('/<int:tournament_id>/delete', methods=['POST'])
@login_required
def delete(tournament_id):
    api_client.delete_tournament(tournament_id)
    flash('Tournament deleted', 'success')
    return redirect(url_for('tournaments.list_tournaments'))


@bp.route('/local-meta')
@login_required
def local_meta():
    months = request.args.get('months', 12, type=int)
    limit = request.args.get('limit', 10, type=int)

    response = api_client.get_local_meta_stats(months=months, limit=limit)
    stats = {}
    if response.status_code == 200:
        stats = response.json()

    resp = make_response(render_template(
        'tournaments/local_meta.html',
        stats=stats,
        months=months,
        limit=limit,
    ))
    return _make_cache_headers(resp)


# ── Form parsing helper ───────────────────────────────────────────────


def _parse_tournament_form(form):
    """Parse the tournament creation form into the API JSON format."""
    tournament = {
        'name': form.get('name', '').strip(),
        'date': form.get('date', ''),
        'location': form.get('location', '').strip(),
        'format': form.get('format', '').strip(),
        'total_players': int(form.get('total_players', 0)),
        'notes': form.get('notes', '').strip(),
        'participants': [],
        'rounds': [],
    }

    if not tournament['name'] or not tournament['date']:
        return None

    # Parse participants (prefix = "p_NAME", "p_DECKNAME", "p_CLAN", "p_ARCHETYPE")
    p_names = form.getlist('p_name[]')
    p_decks = form.getlist('p_deckname[]')
    p_clans = form.getlist('p_clan[]')
    p_archetypes = form.getlist('p_archetype[]')

    seen = set()
    for i, name in enumerate(p_names):
        name = name.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        tournament['participants'].append({
            'player_name': name,
            'deck_name': p_decks[i].strip() if i < len(p_decks) else '',
            'clan': p_clans[i].strip() if i < len(p_clans) else '',
            'archetype': p_archetypes[i].strip() if i < len(p_archetypes) else '',
        })

    if not tournament['participants']:
        return None

    # Parse rounds (prefix = "r_NUMBER", "r_IS_FINAL", "r_TABLE_...")
    i = 0
    while True:
        r_num = form.get(f'r_{i}_number', type=int)
        if r_num is None:
            break

        is_final = form.get(f'r_{i}_final') == 'on'
        round_data = {
            'round_number': r_num,
            'is_final': is_final,
            'results': [],
        }

        # Parse results for this round
        j = 0
        while True:
            seat = form.get(f'r_{i}_result_{j}_seat', type=int)
            if seat is None:
                break

            pidx = form.get(f'r_{i}_result_{j}_participant', type=int)
            if pidx is not None and pidx < len(tournament['participants']):
                round_data['results'].append({
                    'table_number': form.get(f'r_{i}_result_{j}_table', 1, type=int),
                    'seat_position': seat,
                    'participant_id': pidx,  # 1-indexed, resolved to DB id by API
                    'vps': form.get(f'r_{i}_result_{j}_vps', 0, type=float),
                    'gw': form.get(f'r_{i}_result_{j}_gw') == 'on',
                    'final_rank': form.get(f'r_{i}_result_{j}_rank', type=int),
                })
            j += 1

        tournament['rounds'].append(round_data)
        i += 1

    return tournament
