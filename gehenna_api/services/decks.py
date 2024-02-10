from typing import List

from sqlalchemy import select

from gehenna_api.models.deck import Deck
from gehenna_api.schemas import DeckPublic, DeckSchema
from gehenna_api.services.base import BaseDataManager, BaseService


class DeckService(BaseService):
    def get_deck(self, deck_id: int) -> DeckPublic:
        return DeckDataManager(self.session).get_deck(deck_id)

    def get_decks(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[DeckPublic]:
        return DeckDataManager(self.session).get_decks(owner_id, skip, limit)

    def get_decks_by_user(
        self, username, skip: int = 0, limit: int = 100
    ) -> List[DeckPublic]:
        return DeckDataManager(self.session).get_decks_by_user(
            username, skip, limit
        )


class DeckDataManager(BaseDataManager):
    def get_deck(self, deck_id: int) -> DeckPublic:
        stmt = select(Deck).where(Deck.id == deck_id)
        model = self.get_one(stmt)
        return DeckPublic(**model.to_dict())

    def get_decks(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[DeckPublic]:
        schemas: List[DeckPublic] = list()
        stmt = (
            select(Deck)
            .where(Deck.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        for model in self.get_all(stmt):
            schemas += [DeckPublic(**model.to_dict())]
        return schemas

    def get_decks_by_user(
        self, username: str, skip: int = 0, limit: int = 100
    ) -> List[DeckPublic]:
        # TODO
        schemas: List[DeckPublic] = list()
        stmt = select(Deck).offset(skip).limit(limit)
        for model in self.get_all(stmt):
            schemas += [DeckPublic(**model.to_dict())]
        return schemas

    def add_deck(self, deck: DeckSchema) -> None:
        self.add_one(deck)

    def update_deck(self, id: int, deck: DeckSchema) -> None:
        db_deck = self.get_deck(id)
        if not db_deck:
            pass
        db_deck.name = deck.name
        db_deck.description = deck.description
        db_deck.creator = deck.creator
        db_deck.player = deck.player
        db_deck.tipo = deck.tipo
        db_deck.preconstructed = deck.preconstructed
        db_deck.owner_id = deck.owner_id
        db_deck.code = deck.code
