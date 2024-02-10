from sqlalchemy import func, select

from gehenna_api.models.auth import User
from gehenna_api.models.moviment import Moviment
from gehenna_api.schemas import Scalar
from gehenna_api.services.base import BaseDataManager, BaseService


class StockService(BaseService):
    def get_card_quantity(self, card_id: int, username: str) -> Scalar:
        return StockDataManager(self.session).get_card_quantity(
            card_id, username
        )


class StockDataManager(BaseDataManager):
    def get_card_quantity(self, card_id: int, username: str) -> Scalar:
        stmt = select(User).where(User.username == username)
        user = self.get_one(stmt)
        stmt = select(Moviment).where(
            Moviment.owner_id == user.id, Moviment.tipo == 'E'
        )
        count_q = stmt.statement.with_only_columns([func.count()]).order_by(
            None
        )
        count = stmt.session.execute(count_q).scalar()
        return Scalar(quantity=count)
