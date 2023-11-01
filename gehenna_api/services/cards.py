from typing import List

from sqlalchemy import select

from gehenna_api.models.card import Card
from gehenna_api.schemas import CardPublic
from gehenna_api.services.base import BaseDataManager, BaseService


class CardService(BaseService):
    def get_card(self, card_id: int) -> CardPublic:
        return CardDataManager(self.session).get_card(card_id)

    def get_cards(self) -> List[CardPublic]:
        return CardDataManager(self.session).get_cards()

    def get_cards_by_name(self, name) -> List[CardPublic]:
        return CardDataManager(self.session).get_cards_by_name(name)


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

    def get_cards_by_name(self, name: str) -> List[CardPublic]:
        schemas: List[CardPublic] = list()
        stmt = select(Card).where(Card.name.like(f'%{name}%'))
        for model in self.get_all(stmt):
            schemas += [CardPublic(**model.to_dict())]
        return schemas
