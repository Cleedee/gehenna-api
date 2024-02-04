
from sqlalchemy import select
from gehenna_api.models.auth import User
from gehenna_api.models.moviment import Moviment
from gehenna_api.services.base import BaseDataManager, BaseService


class StockService(BaseService):
    
    def get_card_quantity(card_id: int, username: str) -> int:
        return StockDataManager(self.session).get_card_quantity(card_id, username)

class StockDataManager(BaseDataManager):
    
    def get_card_quantity(card_id: int, username: str) -> int:
        stmt = select(User).where(User.username == username)
        user = self.get_one(stmt)
        stmt = select(Moviment).where(
            Moviment.owner_id == user.id, 
            Moviment.card_id == card_id,
            Moviment.tipo == 'E'
        )
        return 1
