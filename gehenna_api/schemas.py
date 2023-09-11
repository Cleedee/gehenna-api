import decimal
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


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
    model_config = ConfigDict(from_attributes=True)


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
