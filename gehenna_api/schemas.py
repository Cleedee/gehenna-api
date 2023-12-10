import decimal
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, validator


class UserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr


class UserList(BaseModel):
    users: list[UserPublic]


class CardSchema(BaseModel):
    code: int   # código da carta na base do Gehenna
    name: str
    tipo: str
    disciplines: Optional[str] = ''
    clan: Optional[str] = ''
    cost: Optional[str] = ''
    capacity: Optional[str] = ''
    group: Optional[str] = ''
    attributes: Optional[str] = ''
    text: Optional[str] = ''
    title: Optional[str] = ''
    sect: Optional[str] = ''
    codevdb: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


class CardPublic(CardSchema):
    id: int


class CardList(BaseModel):
    cards: list[CardPublic]


class MovimentSchema(BaseModel):
    name: str
    tipo: str
    owner_id: int
    date_move: date
    price: decimal.Decimal
    code: int
    model_config = ConfigDict(
        from_attributes=True, json_encoders={decimal.Decimal: str}
    )

    @validator('price', pre=True)
    def quantize_two_decimal_places(cls, v: Any):
        return decimal.Decimal(v).quantize(decimal.Decimal('0.01'))


class MovimentPublic(MovimentSchema):
    id: int


class MovimentList(BaseModel):
    moviments: list[MovimentPublic]


class Message(BaseModel):
    detail: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class ItemSchema(BaseModel):
    card_id: int
    moviment_id: int
    quantity: int
    code: int
    model_config = ConfigDict(from_attributes=True)


class ItemPublic(ItemSchema):
    id: int


class ItemDB(ItemSchema):
    id: int


class ItemList(BaseModel):
    items: list[ItemPublic]


class DeckSchema(BaseModel):
    name: str
    description: str
    creator: Optional[str] = ''
    player: Optional[str] = ''
    tipo: str
    created: date
    updated: Optional[datetime] = None
    preconstructed: bool = False
    owner_id: int
    code: int


class DeckPublic(DeckSchema):
    id: int


class DeckList(BaseModel):
    decks: list[DeckPublic]
