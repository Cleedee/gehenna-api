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
        data = _parse_tournament_form(request.form)
        if data:
            # ── Merge form participants with existing ones ──────────────
            form_participants = {
                p['player_name']: p
                for p in data.get('participants', [])
            }
            removed = set(request.form.getlist('p_remove[]'))

            merged_participants = []
            for existing in tournament.get('participants', []):
                if existing['player_name'] in removed:
                    continue
                p = existing.copy()
                form_p = form_participants.get(p['player_name'])
                if form_p:
                    p['deck_name'] = form_p.get('deck_name', '')
                    p['clan'] = form_p.get('clan', '')
                    p['archetype'] = form_p.get('archetype', '')
                merged_participants.append(p)

            # Also add any form-only participants (new players)
            existing_names = {p['player_name'] for p in merged_participants}
            for fp in data.get('participants', []):
                if fp['player_name'] not in existing_names:
                    merged_participants.append(fp)

            data['participants'] = merged_participants

            # Build name → index mapping from the MERGED list
            name_to_idx = {}
            for idx, p in enumerate(merged_participants):
                name_to_idx[p['player_name']] = idx + 1

            # Build DB id → name from existing data
            id_to_name = {}
            for p in tournament.get('participants', []):
                id_to_name[p['id']] = p['player_name']

            # Convert existing rounds to use merged participant indices
            existing_rounds = []
            for r in tournament.get('rounds', []):
                r_results = []
                for res in r.get('results', []):
                    p_name = id_to_name.get(res['participant_id'])
                    form_idx = name_to_idx.get(p_name, 1) if p_name else 1
                    r_results.append({
                        'table_number': res['table_number'],
                        'seat_position': res['seat_position'],
                        'participant_id': form_idx,
                        'vps': res.get('vps', 0),
                        'gw': res.get('gw', False),
                        'final_rank': res.get('final_rank'),
                    })
                existing_rounds.append({
                    'round_number': r['round_number'],
                    'is_final': r.get('is_final', False),
                    'results': r_results,
                })
            data['rounds'] = existing_rounds

            # Pop date — Pydantic v2.7 has a bug with Optional[date] = None
            # that rejects ANY value (even valid date strings). Since the
            # edit form doesn't change the date, omit it entirely.
            data.pop('date', None)

            resp = api_client.update_tournament(tournament_id, data)
            if resp.status_code != 200:
                flash(f'API error ({resp.status_code}): {resp.text[:200]}', 'danger')
            else:
                flash('Tournament updated!', 'success')
                return redirect(url_for('tournaments.detail', tournament_id=tournament_id))
        else:
            flash('Please fill in required fields', 'danger')

    clans = api_client.get_tournament_clans()
    return render_template('tournaments/form.html', tournament=tournament, clans=clans)


@bp.route('/<int:tournament_id>/delete', methods=['POST'])
@login_required
def delete(tournament_id):
    api_client.delete_tournament(tournament_id)
    flash('Tournament deleted', 'success')
    return redirect(url_for('tournaments.list_tournaments'))


# ── Round management ──────────────────────────────────────────────────


@bp.route('/<int:tournament_id>/rounds/add', methods=['GET', 'POST'])
@login_required
def add_round(tournament_id):
    """Add a new round with matches to a tournament."""
    response = api_client.get_tournament(tournament_id)
    if response.status_code != 200:
        flash('Tournament not found', 'danger')
        return redirect(url_for('tournaments.list_tournaments'))

    tournament = response.json()
    participants = tournament.get('participants', [])

    if request.method == 'POST':
        round_number = request.form.get('round_number', type=int)
        is_final = request.form.get('is_final') == 'on'

        if not round_number:
            flash('Round number is required', 'danger')
        else:
            # Build mapping: form index → participant DB id
            idx_to_pid = {}
            for idx, p in enumerate(participants):
                idx_to_pid[idx + 1] = p['id']

            # Parse tables from form (participant_id = form index 1-based)
            tables = _parse_round_tables(request.form, len(participants))
            round_data = {
                'round_number': round_number,
                'is_final': is_final,
                'results': [],
            }
            for table in tables:
                for result in table['results']:
                    # Convert form index → database ID for the API
                    result['participant_id'] = idx_to_pid.get(
                        result['participant_id'],
                        result['participant_id'],
                    )
                    round_data['results'].append(result)

            resp = api_client.create_tournament_round(tournament_id, round_data)
            if resp.status_code == 201:
                flash(f'Round {round_number} added successfully!', 'success')
                return redirect(url_for('tournaments.detail', tournament_id=tournament_id))
            else:
                flash(f'Error creating round: {resp.text}', 'danger')

    # Pre-compute table distribution for the form
    table_sizes = _distribute_players(len(participants))
    return render_template(
        'tournaments/round_form.html',
        tournament=tournament,
        participants=participants,
        table_sizes=table_sizes,
        round=None,
        results_by_table={},
    )


@bp.route('/<int:tournament_id>/rounds/<int:round_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_round(tournament_id, round_id):
    """Edit an existing round's matches and results."""
    response = api_client.get_tournament(tournament_id)
    if response.status_code != 200:
        flash('Tournament not found', 'danger')
        return redirect(url_for('tournaments.list_tournaments'))

    tournament = response.json()
    participants = tournament.get('participants', [])

    # Find the round
    round_data = None
    for r in tournament.get('rounds', []):
        if r.get('id') == round_id:
            round_data = r
            break

    if not round_data:
        flash('Round not found', 'danger')
        return redirect(url_for('tournaments.detail', tournament_id=tournament_id))

    if request.method == 'POST':
        round_number = request.form.get('round_number', type=int)
        is_final = request.form.get('is_final') == 'on'

        if not round_number:
            flash('Round number is required', 'danger')
        else:
            tables = _parse_round_tables(request.form, len(participants))
            round_update = {
                'round_number': round_number,
                'is_final': is_final,
                'results': [],
            }
            for table in tables:
                for result in table['results']:
                    round_update['results'].append(result)

            # Recreate the round by deleting old and creating new
            # We use the main tournament update endpoint
            resp = api_client.get_tournament(tournament_id)
            if resp.status_code == 200:
                current = resp.json()

                # Build mapping: participant DB id → form index (1-based)
                pid_to_idx = {}
                for idx, p in enumerate(current.get('participants', [])):
                    pid_to_idx[p['id']] = idx + 1

                # Remove this round from the list
                other_rounds = [
                    r for r in current.get('rounds', [])
                    if r.get('id') != round_id
                ]
                # Build the full update payload
                # Only send participants + rounds; basic fields are omitted
                # (they default to None in TournamentUpdate and won't be changed)
                update_data = {
                    'participants': [
                        {
                            'player_name': p['player_name'],
                            'deck_name': p.get('deck_name', ''),
                            'clan': p.get('clan', ''),
                            'archetype': p.get('archetype', ''),
                        }
                        for p in current.get('participants', [])
                    ],
                    'rounds': [],
                }
                # Add other rounds, converting participant DB ids to form indices
                for r in other_rounds:
                    r_results = []
                    for res in r.get('results', []):
                        r_results.append({
                            'table_number': res['table_number'],
                            'seat_position': res['seat_position'],
                            'participant_id': pid_to_idx.get(res['participant_id'], 1),
                            'vps': res.get('vps', 0),
                            'gw': res.get('gw', False),
                            'final_rank': res.get('final_rank'),
                            'qualification_order': res.get('qualification_order'),
                        })
                    update_data['rounds'].append({
                        'round_number': r['round_number'],
                        'is_final': r.get('is_final', False),
                        'results': r_results,
                    })
                # Add the updated round (already has form indices)
                update_data['rounds'].append(round_update)

                upd_resp = api_client.update_tournament(tournament_id, update_data)
                if upd_resp.status_code == 200:
                    flash(f'Round {round_number} updated!', 'success')
                    return redirect(url_for('tournaments.detail', tournament_id=tournament_id))
                else:
                    flash(f'Error updating round: {upd_resp.text}', 'danger')
            else:
                flash('Could not reload tournament data', 'danger')

    # Organize existing results into tables for display
    table_sizes = _distribute_players(len(participants))
    results_by_table: dict[int, list] = {}
    for res in round_data.get('results', []):
        tn = res.get('table_number', 1)
        if tn not in results_by_table:
            results_by_table[tn] = []
        results_by_table[tn].append(res)

    return render_template(
        'tournaments/round_form.html',
        tournament=tournament,
        participants=participants,
        table_sizes=table_sizes,
        round=round_data,
        results_by_table=results_by_table,
    )


@bp.route('/<int:tournament_id>/rounds/<int:round_id>/delete', methods=['POST'])
@login_required
def delete_round(tournament_id, round_id):
    """Delete a round from a tournament."""
    response = api_client.get_tournament(tournament_id)
    if response.status_code != 200:
        flash('Tournament not found', 'danger')
        return redirect(url_for('tournaments.list_tournaments'))

    current = response.json()

    # Build mapping: participant DB id → form index (1-based)
    pid_to_idx = {}
    for idx, p in enumerate(current.get('participants', [])):
        pid_to_idx[p['id']] = idx + 1

    other_rounds = [
        r for r in current.get('rounds', [])
        if r.get('id') != round_id
    ]

    update_data = {
        'participants': [
            {
                'player_name': p['player_name'],
                'deck_name': p.get('deck_name', ''),
                'clan': p.get('clan', ''),
                'archetype': p.get('archetype', ''),
            }
            for p in current.get('participants', [])
        ],
        'rounds': [],
    }

    for r in other_rounds:
        r_results = []
        for res in r.get('results', []):
            r_results.append({
                'table_number': res['table_number'],
                'seat_position': res['seat_position'],
                'participant_id': pid_to_idx.get(res['participant_id'], 1),
                'vps': res.get('vps', 0),
                'gw': res.get('gw', False),
                'final_rank': res.get('final_rank'),
            })
        update_data['rounds'].append({
            'round_number': r['round_number'],
            'is_final': r.get('is_final', False),
            'results': r_results,
        })

    upd_resp = api_client.update_tournament(tournament_id, update_data)
    if upd_resp.status_code == 200:
        flash('Round deleted!', 'success')
    else:
        flash(f'Error deleting round: {upd_resp.text}', 'danger')

    return redirect(url_for('tournaments.detail', tournament_id=tournament_id))


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
    """Parse the tournament creation form into the API JSON format.
    Now only handles basic info + participants (rounds are managed separately).
    """
    tournament = {
        'name': form.get('name', '').strip(),
        'date': form.get('date', ''),
        'location': form.get('location', '').strip(),
        'format': form.get('format', '').strip(),
        'total_players': int(form.get('total_players', 0)),
        'notes': form.get('notes', '').strip(),
        'participants': [],
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

    return tournament


# ── Round & Match helpers ─────────────────────────────────────────────


def _distribute_players(total_players: int) -> list[int]:
    """Distribute players into tables of 4-5 players each.
    Returns a list of table sizes.
    """
    if total_players <= 5:
        return [total_players]
    max_tables = total_players // 4
    min_tables = (total_players + 4) // 5
    for num_tables in range(min_tables, max_tables + 1):
        base = total_players // num_tables
        rem = total_players % num_tables
        sizes = []
        ok = True
        for i in range(num_tables):
            size = base + (1 if i < rem else 0)
            if size < 4 or size > 5:
                ok = False
                break
            sizes.append(size)
        if ok:
            return sizes
    return [total_players]


def _parse_round_tables(form, num_participants: int) -> list[dict]:
    """Parse submitted table/result data from a round form.
    Uses a hidden 'num_results' field to know how many result rows to expect.
    Returns a list of tables, each with 'table_number' and 'results'.
    """
    num_results = form.get('num_results', type=int)
    if num_results is None:
        # Fallback: iterate until we find a gap
        num_results = 0
        while form.get(f'result_{num_results}_participant', type=int) is not None:
            num_results += 1

    tables: dict[int, list] = {}
    for i in range(num_results):
        participant_idx = form.get(f'result_{i}_participant', type=int)
        if participant_idx is None or participant_idx < 1:
            # Empty or unselected row — skip but continue
            continue

        table_num = form.get(f'result_{i}_table', 1, type=int)
        seat = form.get(f'result_{i}_seat', type=int)
        vps = form.get(f'result_{i}_vps', 0, type=float)
        gw = form.get(f'result_{i}_gw') == 'on'
        final_rank = form.get(f'result_{i}_rank', type=int)
        qual = form.get(f'result_{i}_qual', type=int)

        if seat is None:
            continue

        # participant_idx is 1-based, must be <= num_participants
        if participant_idx > num_participants:
            continue

        if table_num not in tables:
            tables[table_num] = {
                'table_number': table_num,
                'results': [],
            }

        tables[table_num]['results'].append({
            'table_number': table_num,
            'seat_position': seat,
            'participant_id': participant_idx,
            'vps': vps,
            'gw': gw,
            'final_rank': final_rank,
            'qualification_order': qual,
        })

    return list(tables.values())
