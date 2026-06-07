import json

from sqlalchemy import select

from gehenna_api.database import get_session
from gehenna_api.models.card import Card
from gehenna_api.utils.vdb import (
    converte_disciplinas_biblioteca,
    converte_disciplinas_cripta,
)


def _json_dumps(val) -> str:
    if val is None or val == '' or val == {} or val == []:
        return ''
    return json.dumps(val, ensure_ascii=False)


def criar_carta_biblioteca(data, codevdb) -> Card:
    dados = data[codevdb]
    custo = (
        dados.get('blood') or dados.get('pool') or dados.get('conviction')
    )
    carta = Card(
        name=dados['name'],
        tipo=dados['type'],
        disciplines=converte_disciplinas_biblioteca(dados['discipline']),
        clan=dados['clan'],
        cost=custo,
        attributes='',
        text=dados['text'],
        codevdb=codevdb,
        code=0,
        blood=dados.get('blood') or 0,
        pool=dados.get('pool') or 0,
        conviction=dados.get('conviction') or 0,
        burn=dados.get('burn') or '',
        requirement=dados.get('requirement') or '',
        ascii=dados.get('ascii') or '',
        artist=_json_dumps(dados.get('artist')),
        banned=dados.get('banned') or '',
        twd=dados.get('twd') or 0,
        set_info=_json_dumps(dados.get('set')),
        path=dados.get('path') or '',
        trifle=dados.get('trifle') or False,
        rulings=_json_dumps(dados.get('rulings')),
        aka=dados.get('aka') or '',
    )
    return carta


def criar_carta_cripta(data, codevdb) -> Card:
    key = codevdb
    carta = Card(
        name=data[key]['name'],
        tipo='vampire',
        disciplines=converte_disciplinas_cripta(data[key]['disciplines']),
        clan=data[key]['clan'],
        cost='',
        capacity=data[key]['capacity'],
        group=data[key]['group'],
        attributes='',
        text=data[key]['text'],
        title=data[key]['title'],
        sect=data[key]['sect'],
        codevdb=key,
        avancado=False if data[key]['adv'] == '' else data[key]['adv'][0],
        code=0,
        blood=0,
        pool=0,
        conviction=0,
        burn='',
        requirement='',
        ascii=data[key].get('ascii') or '',
        artist=_json_dumps(data[key].get('artist')),
        banned=data[key].get('banned') or '',
        twd=data[key].get('twd') or 0,
        set_info=_json_dumps(data[key].get('set')),
        path=data[key].get('path') or '',
        trifle=False,
        rulings=_json_dumps(data[key].get('rulings')),
        aka=data[key].get('aka') or '',
    )
    return carta


def cadastrar_carta(data, funcao_criacao_carta):
    session = next(get_session())
    for codevdb in data.keys():
        carta = session.scalar(select(Card).where(Card.codevdb == codevdb))
        if not carta:
            carta = funcao_criacao_carta(data, codevdb)
            session.add(carta)
            print(f'Cadastrando {carta.name}')
        session.commit()


def cadastrar_carta_fake(data, funcao_criacao_carta):
    session = next(get_session())
    for codevdb in data.keys():
        carta = session.scalar(select(Card).where(Card.codevdb == codevdb))
        if not carta:
            carta = funcao_criacao_carta(data, codevdb)
            #print(carta)


# cadastrar cartas de cripta novas
def importar_cartas_de_cripta():
    with open('scripts/cardbase_crypt.json') as json_file:
        data = json.load(json_file)
        # session = next(get_session())
        # print(data['200107'])
        cadastrar_carta(data, criar_carta_cripta)


# cadatrar cartas de biblioteca novas
def importar_cartas_de_biblioteca():
    with open('scripts/cardbase_lib.json') as json_file:
        data = json.load(json_file)
        # print(data['100741'])
        cadastrar_carta(data, criar_carta_biblioteca)


if __name__ == '__main__':
    importar_cartas_de_cripta()
    importar_cartas_de_biblioteca()
