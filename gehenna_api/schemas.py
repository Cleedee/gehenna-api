from pydantic import BaseModel


class CardSchema(BaseModel):
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
