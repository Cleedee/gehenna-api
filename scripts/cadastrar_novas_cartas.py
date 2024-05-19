import json

from sqlalchemy import select

from gehenna_api.database import get_session
from gehenna_api.models.card import Card
from gehenna_api.utils.vdb import (
    converte_disciplinas_biblioteca,
    converte_disciplinas_cripta,
)


def criar_carta_biblioteca(data, codevdb) -> Card:
    dados = data[codevdb]
    custo = (
        dados['Blood Cost'] or dados['Pool Cost'] or dados['Conviction Cost']
    )
    carta = Card(
        name=dados['Name'],
        tipo=dados['Type'],
        disciplines=converte_disciplinas_biblioteca(dados['Discipline']),
        clan=dados['Clan'],
        cost=custo,
        attributes='',
        text=dados['Card Text'],
        codevdb=codevdb,
        code=0,
    )
    return carta


def criar_carta_cripta(data, codevdb) -> Card:
    key = codevdb
    carta = Card(
        name=data[key]['Name'],
        tipo='Vampire',
        disciplines=converte_disciplinas_cripta(data[key]['Disciplines']),
        clan=data[key]['Clan'],
        cost='',
        capacity=data[key]['Capacity'],
        group=data[key]['Group'],
        attributes='',
        text=data[key]['Card Text'],
        title=data[key]['Title'],
        sect=data[key]['Sect'],
        codevdb=key,
        avancado=False if data[key]['Adv'] == '' else data[key]['Adv'][0],
        code=0,
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
            print(carta)


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
        #        print(data['100741'])
        cadastrar_carta(data, criar_carta_cripta)


if __name__ == '__main__':
    importar_cartas_de_biblioteca()
