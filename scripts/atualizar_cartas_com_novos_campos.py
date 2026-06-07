import json
from sqlalchemy import select
from gehenna_api.database import get_session
from gehenna_api.models.card import Card


def _json_dumps(val) -> str:
    if val is None or val == '' or val == {} or val == []:
        return ''
    return json.dumps(val, ensure_ascii=False)


def atualizar_cartas():
    session = next(get_session())

    with open('scripts/cardbase_crypt.json') as f:
        crypt_data = json.load(f)
    with open('scripts/cardbase_lib.json') as f:
        lib_data = json.load(f)

    total = 0
    for codevdb_str, dados in crypt_data.items():
        codevdb = int(codevdb_str)
        carta = session.scalar(
            select(Card).where(Card.codevdb == codevdb)
        )
        if carta is None:
            continue
        carta.blood = 0
        carta.pool = 0
        carta.conviction = 0
        carta.burn = ''
        carta.requirement = ''
        carta.ascii = dados.get('ascii') or ''
        carta.artist = _json_dumps(dados.get('artist'))
        carta.banned = dados.get('banned') or ''
        carta.twd = dados.get('twd') or 0
        carta.set_info = _json_dumps(dados.get('set'))
        carta.path = dados.get('path') or ''
        carta.trifle = False
        carta.rulings = _json_dumps(dados.get('rulings'))
        carta.aka = dados.get('aka') or ''
        total += 1

    for codevdb_str, dados in lib_data.items():
        codevdb = int(codevdb_str)
        carta = session.scalar(
            select(Card).where(Card.codevdb == codevdb)
        )
        if carta is None:
            continue
        carta.blood = dados.get('blood') or 0
        carta.pool = dados.get('pool') or 0
        carta.conviction = dados.get('conviction') or 0
        carta.burn = dados.get('burn') or ''
        carta.requirement = dados.get('requirement') or ''
        carta.ascii = dados.get('ascii') or ''
        carta.artist = _json_dumps(dados.get('artist'))
        carta.banned = dados.get('banned') or ''
        carta.twd = dados.get('twd') or 0
        carta.set_info = _json_dumps(dados.get('set'))
        carta.path = dados.get('path') or ''
        carta.trifle = dados.get('trifle') or False
        carta.rulings = _json_dumps(dados.get('rulings'))
        carta.aka = dados.get('aka') or ''
        total += 1

    session.commit()
    print(f'Atualizadas {total} cartas')


if __name__ == '__main__':
    atualizar_cartas()
