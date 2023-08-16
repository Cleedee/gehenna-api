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


class Message(BaseModel):
    detail: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
