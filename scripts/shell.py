from sqlalchemy import select

from gehenna_api.database import get_session
from gehenna_api.models.card import Card

s = select
g = get_session
c = Card
