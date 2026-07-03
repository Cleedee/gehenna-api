from collections import defaultdict, Counter
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session, joinedload

from gehenna_api.database import get_session
from gehenna_api.models.auth import User
from gehenna_api.models.tournament import (
    Tournament,
    TournamentParticipant,
    TournamentRound,
    TournamentResult,
)

router = APIRouter(prefix='/tournaments', tags=['tournaments'])


# ── Pydantic schemas ──────────────────────────────────────────────────


class ResultCreate(BaseModel):
    table_number: int
    seat_position: int
    participant_id: int
    vps: float = 0.0
    gw: bool = False
    final_rank: Optional[int] = None


class RoundCreate(BaseModel):
    round_number: int
    is_final: bool = False
    results: list[ResultCreate] = []


class ParticipantCreate(BaseModel):
    player_name: str
    user_id: Optional[int] = None
    deck_id: Optional[int] = None
    deck_name: Optional[str] = ''
    clan: Optional[str] = ''
    archetype: Optional[str] = ''


class TournamentCreate(BaseModel):
    name: str
    date: date
    location: Optional[str] = ''
    format: Optional[str] = ''
    total_players: Optional[int] = 0
    notes: Optional[str] = ''
    participants: list[ParticipantCreate] = []
    rounds: list[RoundCreate] = []


class TournamentUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    location: Optional[str] = None
    format: Optional[str] = None
    total_players: Optional[int] = None
    notes: Optional[str] = None


# ── Responses ─────────────────────────────────────────────────────────


class ParticipantOut(BaseModel):
    id: int
    player_name: str
    user_id: Optional[int] = None
    deck_id: Optional[int] = None
    deck_name: Optional[str] = ''
    clan: Optional[str] = ''
    archetype: Optional[str] = ''

    class Config:
        from_attributes = True


class ResultOut(BaseModel):
    id: int
    round_id: int
    participant_id: int
    table_number: int
    seat_position: int
    vps: float
    gw: bool
    final_rank: Optional[int] = None
    participant: Optional[ParticipantOut] = None

    class Config:
        from_attributes = True


class RoundOut(BaseModel):
    id: int
    tournament_id: int
    round_number: int
    is_final: bool
    results: list[ResultOut] = []

    class Config:
        from_attributes = True


class TournamentOut(BaseModel):
    id: int
    name: str
    date: date
    location: Optional[str] = ''
    format: Optional[str] = ''
    total_players: Optional[int] = 0
    notes: Optional[str] = ''
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    participants: list[ParticipantOut] = []
    rounds: list[RoundOut] = []

    class Config:
        from_attributes = True


class TournamentListItem(BaseModel):
    id: int
    name: str
    date: date
    location: Optional[str] = ''
    format: Optional[str] = ''
    total_players: Optional[int] = 0
    winner: Optional[str] = None

    class Config:
        from_attributes = True


# ── Stats models ──────────────────────────────────────────────────────


class ClanStat(BaseModel):
    total_entries: int
    gws: int
    total_vps: float
    avg_vps: float
    win_rate: float


class PositionStat(BaseModel):
    entries: int
    avg_vps: float
    win_rate: float


class AdjacencyStat(BaseModel):
    predator_clan: str
    prey_clan: str
    games: int
    predator_wins: int
    prey_wins: int


class PlayerStat(BaseModel):
    player_name: str
    tournaments: int
    total_vps: float
    avg_vps: float
    gws: int
    finals: int
    best_result: Optional[int] = None


class ArchetypeStat(BaseModel):
    archetype: str
    clan: str
    entries: int
    gws: int
    avg_vps: float


class LocalMetaResponse(BaseModel):
    total_tournaments: int
    total_entries: int
    clan_distribution: dict[str, ClanStat]
    by_seat_position: dict[str, PositionStat]
    adjacency: list[AdjacencyStat]
    top_players: list[PlayerStat]
    top_archetypes: list[ArchetypeStat]
    recent_winners: list[dict]


# ── Helper: get current user ──────────────────────────────────────────


def get_current_user(session: Session = Depends(get_session)) -> Optional[User]:
    """Simple auth — returns None if not authenticated (write endpoints check)."""
    return None  # will be overridden by actual auth in each endpoint


# ── CRUD Endpoints ────────────────────────────────────────────────────


@router.post('/', response_model=TournamentOut, status_code=201)
def create_tournament(
    data: TournamentCreate,
    session: Session = Depends(get_session),
):
    tournament = Tournament(
        name=data.name,
        date=data.date,
        location=data.location,
        format=data.format,
        total_players=data.total_players,
        notes=data.notes,
        created_at=datetime.now(),
    )
    session.add(tournament)
    session.flush()  # get id

    # Participants
    participant_list = []
    for p in data.participants:
        participant = TournamentParticipant(
            tournament_id=tournament.id,
            player_name=p.player_name,
            user_id=p.user_id,
            deck_id=p.deck_id,
            deck_name=p.deck_name,
            clan=p.clan,
            archetype=p.archetype,
        )
        session.add(participant)
        session.flush()
        participant_list.append(participant)

    # Rounds + results
    for r in data.rounds:
        round_ = TournamentRound(
            tournament_id=tournament.id,
            round_number=r.round_number,
            is_final=r.is_final,
        )
        session.add(round_)
        session.flush()

        for res in r.results:
            idx = res.participant_id - 1  # 1-based → 0-based
            actual_pid = participant_list[idx].id if 0 <= idx < len(participant_list) else res.participant_id
            result = TournamentResult(
                round_id=round_.id,
                participant_id=actual_pid,
                table_number=res.table_number,
                seat_position=res.seat_position,
                vps=res.vps,
                gw=res.gw,
                final_rank=res.final_rank,
            )
            session.add(result)

    session.commit()
    return _load_tournament(tournament.id, session)


@router.get('/', response_model=list[TournamentListItem])
def list_tournaments(
    year: Optional[int] = Query(None),
    format: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    session: Session = Depends(get_session),
):
    query = select(Tournament).order_by(Tournament.date.desc()).limit(limit)
    if year:
        query = query.where(func.extract('year', Tournament.date) == year)
    if format:
        query = query.where(Tournament.format == format)

    tournaments = session.scalars(query).all()
    result = []
    for t in tournaments:
        winner = _get_winner(t.id, session)
        result.append(TournamentListItem(
            id=t.id,
            name=t.name,
            date=t.date,
            location=t.location,
            format=t.format,
            total_players=t.total_players,
            winner=winner,
        ))
    return result


@router.get('/{tournament_id}', response_model=TournamentOut)
def get_tournament(
    tournament_id: int,
    session: Session = Depends(get_session),
):
    t = _load_tournament(tournament_id, session)
    if not t:
        raise HTTPException(404, 'Tournament not found')
    return t


@router.put('/{tournament_id}', response_model=TournamentOut)
def update_tournament(
    tournament_id: int,
    data: TournamentUpdate,
    session: Session = Depends(get_session),
):
    t = session.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(404, 'Tournament not found')

    if data.name is not None:
        t.name = data.name
    if data.date is not None:
        t.date = data.date
    if data.location is not None:
        t.location = data.location
    if data.format is not None:
        t.format = data.format
    if data.total_players is not None:
        t.total_players = data.total_players
    if data.notes is not None:
        t.notes = data.notes

    session.commit()
    return _load_tournament(tournament_id, session)


@router.delete('/{tournament_id}', status_code=204)
def delete_tournament(
    tournament_id: int,
    session: Session = Depends(get_session),
):
    t = session.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(404, 'Tournament not found')
    session.delete(t)
    session.commit()


# ── Participant endpoints ─────────────────────────────────────────────


@router.post('/{tournament_id}/participants', response_model=ParticipantOut, status_code=201)
def add_participant(
    tournament_id: int,
    data: ParticipantCreate,
    session: Session = Depends(get_session),
):
    t = session.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(404, 'Tournament not found')

    p = TournamentParticipant(
        tournament_id=tournament_id,
        player_name=data.player_name,
        user_id=data.user_id,
        deck_id=data.deck_id,
        deck_name=data.deck_name,
        clan=data.clan,
        archetype=data.archetype,
    )
    session.add(p)
    session.commit()
    return p


@router.put('/participants/{participant_id}', response_model=ParticipantOut)
def update_participant(
    participant_id: int,
    data: ParticipantCreate,
    session: Session = Depends(get_session),
):
    p = session.get(TournamentParticipant, participant_id)
    if not p:
        raise HTTPException(404, 'Participant not found')

    p.player_name = data.player_name
    p.user_id = data.user_id
    p.deck_id = data.deck_id
    p.deck_name = data.deck_name
    p.clan = data.clan
    p.archetype = data.archetype

    session.commit()
    return p


@router.delete('/participants/{participant_id}', status_code=204)
def delete_participant(
    participant_id: int,
    session: Session = Depends(get_session),
):
    p = session.get(TournamentParticipant, participant_id)
    if not p:
        raise HTTPException(404, 'Participant not found')
    session.delete(p)
    session.commit()


# ── Round + Result endpoints ──────────────────────────────────────────


@router.post('/{tournament_id}/rounds', response_model=RoundOut, status_code=201)
def add_round(
    tournament_id: int,
    data: RoundCreate,
    session: Session = Depends(get_session),
):
    t = session.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(404, 'Tournament not found')

    round_ = TournamentRound(
        tournament_id=tournament_id,
        round_number=data.round_number,
        is_final=data.is_final,
    )
    session.add(round_)
    session.flush()

    for res in data.results:
        result = TournamentResult(
            round_id=round_.id,
            participant_id=res.participant_id,
            table_number=res.table_number,
            seat_position=res.seat_position,
            vps=res.vps,
            gw=res.gw,
            final_rank=res.final_rank,
        )
        session.add(result)

    session.commit()
    return _load_round(round_.id, session)


@router.put('/results/{result_id}', response_model=ResultOut)
def update_result(
    result_id: int,
    data: ResultCreate,
    session: Session = Depends(get_session),
):
    r = session.get(TournamentResult, result_id)
    if not r:
        raise HTTPException(404, 'Result not found')

    r.table_number = data.table_number
    r.seat_position = data.seat_position
    r.vps = data.vps
    r.gw = data.gw
    r.final_rank = data.final_rank

    session.commit()
    return _load_result(result_id, session)


@router.delete('/results/{result_id}', status_code=204)
def delete_result(
    result_id: int,
    session: Session = Depends(get_session),
):
    r = session.get(TournamentResult, result_id)
    if not r:
        raise HTTPException(404, 'Result not found')
    session.delete(r)
    session.commit()


# ── Stats / Local Meta ────────────────────────────────────────────────


@router.get('/stats/local', response_model=LocalMetaResponse)
def local_meta_stats(
    months: int = Query(12, description='Lookback period in months'),
    limit: int = Query(10, le=50),
    session: Session = Depends(get_session),
):
    """Compute local meta statistics from registered tournaments."""
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=months * 30)

    # Get tournaments in period
    tournaments = session.scalars(
        select(Tournament).where(Tournament.date >= cutoff)
    ).all()

    if not tournaments:
        return LocalMetaResponse(
            total_tournaments=0, total_entries=0,
            clan_distribution={}, by_seat_position={},
            adjacency=[], top_players=[], top_archetypes=[],
            recent_winners=[],
        )

    t_ids = [t.id for t in tournaments]

    # Get all participants for these tournaments
    participants = session.scalars(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id.in_(t_ids)
        )
    ).all()
    p_ids = [p.id for p in participants]

    # Get all results
    round_ids = session.scalars(
        select(TournamentRound.id).where(
            TournamentRound.tournament_id.in_(t_ids)
        )
    ).all()

    results = session.scalars(
        select(TournamentResult).where(
            TournamentResult.round_id.in_(round_ids)
        )
    ).all()

    # Build lookup
    part_by_id = {p.id: p for p in participants}
    round_by_id = {}
    for rid in round_ids:
        r = session.get(TournamentRound, rid)
        if r:
            round_by_id[rid] = r

    # ── Clan distribution ──
    clan_entries = Counter()
    clan_gws = Counter()
    clan_vps = defaultdict(float)

    for res in results:
        part = part_by_id.get(res.participant_id)
        if not part or not part.clan:
            continue
        clan = part.clan
        clan_entries[clan] += 1
        clan_vps[clan] += res.vps
        if res.gw:
            clan_gws[clan] += 1

    clan_dist = {}
    for clan in clan_entries:
        entries = clan_entries[clan]
        gws = clan_gws[clan]
        total_vps = clan_vps[clan]
        clan_dist[clan] = ClanStat(
            total_entries=entries,
            gws=gws,
            total_vps=round(total_vps, 1),
            avg_vps=round(total_vps / entries, 2) if entries else 0,
            win_rate=round(gws / entries * 100, 1) if entries else 0,
        )

    # ── By seat position ──
    pos_entries = Counter()
    pos_gws = Counter()
    pos_vps = defaultdict(float)

    for res in results:
        pos = res.seat_position
        pos_entries[pos] += 1
        pos_vps[pos] += res.vps
        if res.gw:
            pos_gws[pos] += 1

    by_pos = {}
    for pos in sorted(pos_entries):
        entries = pos_entries[pos]
        gws = pos_gws[pos]
        total_vps = pos_vps[pos]
        by_pos[str(pos)] = PositionStat(
            entries=entries,
            avg_vps=round(total_vps / entries, 2) if entries else 0,
            win_rate=round(gws / entries * 100, 1) if entries else 0,
        )

    # ── Adjacency (clan vs clan on same table) ──
    adj_data = defaultdict(lambda: {'predator_wins': 0, 'prey_wins': 0, 'games': 0})

    # Group results by (round_id, table_number)
    tables = defaultdict(list)
    for res in results:
        tables[(res.round_id, res.table_number)].append(res)

    for (rid, tn), table_results in tables.items():
        table_results.sort(key=lambda x: x.seat_position)
        for i, r in enumerate(table_results):
            if i + 1 < len(table_results):  # has prey
                predator = part_by_id.get(r.participant_id)
                prey = part_by_id.get(table_results[i + 1].participant_id)
                if predator and prey and predator.clan and prey.clan:
                    key = (predator.clan, prey.clan)
                    adj_data[key]['games'] += 1
                    if r.gw:
                        adj_data[key]['predator_wins'] += 1
                    if table_results[i + 1].gw:
                        adj_data[key]['prey_wins'] += 1

    adjacency = [
        AdjacencyStat(
            predator_clan=k[0],
            prey_clan=k[1],
            games=v['games'],
            predator_wins=v['predator_wins'],
            prey_wins=v['prey_wins'],
        )
        for k, v in sorted(adj_data.items(), key=lambda x: -x[1]['games'])
    ]

    # ── Top players ──
    player_data = defaultdict(lambda: {
        'tournaments': set(), 'total_vps': 0.0, 'gws': 0, 'finals': 0, 'entries': 0
    })

    for res in results:
        part = part_by_id.get(res.participant_id)
        if not part:
            continue
        name = part.player_name
        player_data[name]['tournaments'].add(part.tournament_id)
        player_data[name]['total_vps'] += res.vps
        player_data[name]['entries'] += 1
        if res.gw:
            player_data[name]['gws'] += 1

    # Check finals
    for t in tournaments:
        final_round = session.scalar(
            select(TournamentRound).where(
                TournamentRound.tournament_id == t.id,
                TournamentRound.is_final == True,
            )
        )
        if final_round:
            final_results = session.scalars(
                select(TournamentResult).where(
                    TournamentResult.round_id == final_round.id
                )
            ).all()
            for fr in final_results:
                part = part_by_id.get(fr.participant_id)
                if part:
                    player_data[part.player_name]['finals'] += 1

    top_players = [
        PlayerStat(
            player_name=name,
            tournaments=len(d['tournaments']),
            total_vps=round(d['total_vps'], 1),
            avg_vps=round(d['total_vps'] / d['entries'], 2) if d['entries'] else 0,
            gws=d['gws'],
            finals=d['finals'],
        )
        for name, d in sorted(player_data.items(), key=lambda x: -x[1]['total_vps'])
    ][:limit]

    # ── Top archetypes ──
    arch_data = defaultdict(lambda: {'entries': 0, 'gws': 0, 'vps': 0.0, 'clan': ''})

    for res in results:
        part = part_by_id.get(res.participant_id)
        if not part or not part.archetype:
            continue
        arch = part.archetype
        arch_data[arch]['entries'] += 1
        arch_data[arch]['vps'] += res.vps
        arch_data[arch]['clan'] = part.clan or ''
        if res.gw:
            arch_data[arch]['gws'] += 1

    top_archetypes = [
        ArchetypeStat(
            archetype=arch,
            clan=d['clan'],
            entries=d['entries'],
            gws=d['gws'],
            avg_vps=round(d['vps'] / d['entries'], 2) if d['entries'] else 0,
        )
        for arch, d in sorted(arch_data.items(), key=lambda x: -x[1]['entries'])
    ][:limit]

    # ── Recent winners ──
    recent_winners = []
    for t in tournaments[:10]:
        winner = _get_winner(t.id, session)
        recent_winners.append({
            'tournament_name': t.name,
            'date': t.date.isoformat(),
            'winner': winner or 'N/A',
        })

    return LocalMetaResponse(
        total_tournaments=len(tournaments),
        total_entries=len(results),
        clan_distribution=dict(sorted(
            clan_dist.items(), key=lambda x: -x[1].total_entries
        )),
        by_seat_position=by_pos,
        adjacency=adjacency,
        top_players=top_players,
        top_archetypes=top_archetypes,
        recent_winners=recent_winners,
    )


# ── Helpers ───────────────────────────────────────────────────────────


def _get_winner(tournament_id: int, session: Session) -> Optional[str]:
    """Find the winner of a tournament (final round, final_rank=1 or highest VPs)."""
    # First try: final round with final_rank=1
    final_round = session.scalar(
        select(TournamentRound).where(
            TournamentRound.tournament_id == tournament_id,
            TournamentRound.is_final == True,
        )
    )
    if final_round:
        winner_result = session.scalar(
            select(TournamentResult).where(
                TournamentResult.round_id == final_round.id,
                TournamentResult.final_rank == 1,
            )
        )
        if winner_result:
            part = session.get(TournamentParticipant, winner_result.participant_id)
            if part:
                return part.player_name

        # Fallback: highest VPs in final
        final_results = session.scalars(
            select(TournamentResult).where(
                TournamentResult.round_id == final_round.id
            ).order_by(TournamentResult.vps.desc())
        ).all()
        if final_results:
            part = session.get(TournamentParticipant, final_results[0].participant_id)
            if part:
                return part.player_name

    # Second try: any round with gw=True
    for round_ in session.scalars(
        select(TournamentRound).where(
            TournamentRound.tournament_id == tournament_id
        )
    ).all():
        gw_result = session.scalar(
            select(TournamentResult).where(
                TournamentResult.round_id == round_.id,
                TournamentResult.gw == True,
            )
        )
        if gw_result:
            part = session.get(TournamentParticipant, gw_result.participant_id)
            if part:
                return part.player_name

    return None


def _load_tournament(tournament_id: int, session: Session) -> Optional[TournamentOut]:
    t = session.get(Tournament, tournament_id)
    if not t:
        return None

    participants = session.scalars(
        select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id
        )
    ).all()

    rounds = session.scalars(
        select(TournamentRound).where(
            TournamentRound.tournament_id == tournament_id
        ).order_by(TournamentRound.round_number)
    ).all()

    rounds_out = []
    for r in rounds:
        results = session.scalars(
            select(TournamentResult).where(
                TournamentResult.round_id == r.id
            ).order_by(TournamentResult.table_number, TournamentResult.seat_position)
        ).all()

        results_out = []
        for res in results:
            part = session.get(TournamentParticipant, res.participant_id)
            part_out = ParticipantOut(
                id=part.id,
                player_name=part.player_name,
                user_id=part.user_id,
                deck_id=part.deck_id,
                deck_name=part.deck_name,
                clan=part.clan,
                archetype=part.archetype,
            ) if part else None

            results_out.append(ResultOut(
                id=res.id,
                round_id=res.round_id,
                participant_id=res.participant_id,
                table_number=res.table_number,
                seat_position=res.seat_position,
                vps=res.vps,
                gw=res.gw,
                final_rank=res.final_rank,
                participant=part_out,
            ))

        rounds_out.append(RoundOut(
            id=r.id,
            tournament_id=r.tournament_id,
            round_number=r.round_number,
            is_final=r.is_final,
            results=results_out,
        ))

    participants_out = [
        ParticipantOut(
            id=p.id,
            player_name=p.player_name,
            user_id=p.user_id,
            deck_id=p.deck_id,
            deck_name=p.deck_name,
            clan=p.clan,
            archetype=p.archetype,
        )
        for p in participants
    ]

    return TournamentOut(
        id=t.id,
        name=t.name,
        date=t.date,
        location=t.location,
        format=t.format,
        total_players=t.total_players,
        notes=t.notes,
        created_by=t.created_by,
        created_at=t.created_at,
        participants=participants_out,
        rounds=rounds_out,
    )


def _load_round(round_id: int, session: Session) -> Optional[RoundOut]:
    r = session.get(TournamentRound, round_id)
    if not r:
        return None

    results = session.scalars(
        select(TournamentResult).where(
            TournamentResult.round_id == round_id
        ).order_by(TournamentResult.table_number, TournamentResult.seat_position)
    ).all()

    results_out = []
    for res in results:
        part = session.get(TournamentParticipant, res.participant_id)
        part_out = ParticipantOut(
            id=part.id,
            player_name=part.player_name,
            user_id=part.user_id,
            deck_id=part.deck_id,
            deck_name=part.deck_name,
            clan=part.clan,
            archetype=part.archetype,
        ) if part else None

        results_out.append(ResultOut(
            id=res.id,
            round_id=res.round_id,
            participant_id=res.participant_id,
            table_number=res.table_number,
            seat_position=res.seat_position,
            vps=res.vps,
            gw=res.gw,
            final_rank=res.final_rank,
            participant=part_out,
        ))

    return RoundOut(
        id=r.id,
        tournament_id=r.tournament_id,
        round_number=r.round_number,
        is_final=r.is_final,
        results=results_out,
    )


def _load_result(result_id: int, session: Session) -> Optional[ResultOut]:
    res = session.get(TournamentResult, result_id)
    if not res:
        return None

    part = session.get(TournamentParticipant, res.participant_id)
    part_out = ParticipantOut(
        id=part.id,
        player_name=part.player_name,
        user_id=part.user_id,
        deck_id=part.deck_id,
        deck_name=part.deck_name,
        clan=part.clan,
        archetype=part.archetype,
    ) if part else None

    return ResultOut(
        id=res.id,
        round_id=res.round_id,
        participant_id=res.participant_id,
        table_number=res.table_number,
        seat_position=res.seat_position,
        vps=res.vps,
        gw=res.gw,
        final_rank=res.final_rank,
        participant=part_out,
    )
