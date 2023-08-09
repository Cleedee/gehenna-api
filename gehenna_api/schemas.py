from pydantic import BaseModel


class CardSchema(BaseModel):
    code: int   # código da carta na base do Gehenna
    name: str
    disciplines: str
    clan: str
    cost: str
    capacity: str
    group: str
    attributes: str
    text: str
    title: str
    sect: str


class CardPublic(CardSchema):
    id: int


class CardList(BaseModel):
    cards: list[CardPublic]


class Message(BaseModel):
    detail: str
