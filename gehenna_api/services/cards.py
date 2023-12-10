from typing import List

from sqlalchemy import select

from gehenna_api.models.card import Card
from gehenna_api.schemas import CardPublic, CardSchema
from gehenna_api.services.base import BaseDataManager, BaseService


class CardService(BaseService):
    def get_card(self, card_id: int) -> CardPublic:
        return CardDataManager(self.session).get_card(card_id)

    def get_cards(self) -> List[CardPublic]:
        return CardDataManager(self.session).get_cards()

    def get_cards_like_name(self, name) -> List[CardPublic]:
        return CardDataManager(self.session).get_cards_like_name(name)

    def get_cards_by_name(self, name) -> CardPublic | None:
        return CardDataManager(self.session).get_card_by_name(name)

    def add_card(self, card: CardSchema) -> None:
        CardDataManager(self.session).add_card(card)


class CardDataManager(BaseDataManager):
    def get_card(self, card_id: int) -> CardPublic:
        stmt = select(Card).where(Card.id == card_id)
        model = self.get_one(stmt)
        return CardPublic(**model.to_dict())

    def get_cards(self) -> List[CardPublic]:
        schemas: List[CardPublic] = list()
        stmt = select(Card)
        for model in self.get_all(stmt):
            schemas += [CardPublic(**model.to_dict())]

        return schemas

    def get_cards_like_name(self, name: str) -> List[CardPublic]:
        schemas: List[CardPublic] = list()
        stmt = select(Card).where(Card.name.like(f'%{name}%'))
        for model in self.get_all(stmt):
            schemas += [CardPublic(**model.to_dict())]
        return schemas

    def get_card_by_name(self, name: str) -> CardPublic | None:
        stmt = select(Card).where(Card.name == name)
        model = self.get_one(stmt)
        return CardPublic(**model.to_dict()) if model else None

    def add_card(self, card: CardSchema) -> None:
        self.add_one(card)

    def update_card(self, id: int, card: CardSchema) -> None:
        card_db = self.get_card(id)
        if not card_db:
            pass
        card_db.name = card.name
        card_db.tipo = card.tipo
        card_db.attributes = card.attributes
        card_db.capacity = card.capacity
        card_db.clan = card.clan
        card_db.cost = card.cost
        card_db.disciplines = card.disciplines
        card_db.text = card.text
        card_db.sect = card.sect
        card_db.title = card.title
        card_db.group = card.group
