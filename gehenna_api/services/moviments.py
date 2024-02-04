

from typing import List

from sqlalchemy import select
from gehenna_api.models.moviment import Moviment
from gehenna_api.schemas import MovimentPublic, MovimentSchema
from gehenna_api.services.base import BaseDataManager, BaseService


class MovimentService(BaseService):
    
    def get_moviment(self, moviment_id) -> MovimentPublic:
        return MovimentDataManager(self.session).get_moviment(moviment_id)

    def get_by_owner(self, owner_id) -> List[MovimentPublic]:
        return MovimentDataManager(self.session).get_by_owner(owner_id)

    def add_moviment(self, moviment: MovimentSchema) -> None:
        moviment_model = Moviment(
            name = moviment.name,
            tipo = moviment.tipo,
            date_move = moviment.date_move,
            price = moviment.price,
            owner_id = moviment.owner_id,
            code = moviment.code
        )
        MovimentDataManager(self.session).add_moviment(moviment_model)

    def delete_moviment(self, moviment_id: int) -> None:
        moviment = self.get_moviment(moviment_id)
        MovimentDataManager(self.session).delete_moviment(moviment)

class MovimentDataManager(BaseDataManager):

    def get_moviment(self, moviment_id: int) -> MovimentPublic:
        stmt = select(Moviment).where(Moviment.id == moviment_id)
        model = self.get_one(stmt)
        return MovimentPublic(**model.to_dict())

    def get_by_owner(self, owner_id: int) -> List[MovimentPublic]:
        schemas: List[MovimentPublic] = list()
        stmt = select(Moviment).where(Moviment.owner_id == owner_id)
        for model in self.get_all(stmt):
            schemas += [MovimentPublic(**model.to_dict())]
        return schemas

    def add_moviment(self, moviment: Moviment) -> None:
        self.add_one(moviment)

    def delete_moviment(self, moviment: Moviment) -> None:
        self.delete_one(moviment)
