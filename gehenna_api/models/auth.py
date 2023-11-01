from sqlalchemy.orm import Mapped, mapped_column

from gehenna_api.models.base import SQLModel


class User(SQLModel):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    password: Mapped[str]
    email: Mapped[str]
