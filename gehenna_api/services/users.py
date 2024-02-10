from typing import List

from sqlalchemy import select

from gehenna_api.models.auth import User
from gehenna_api.schemas import UserPublic
from gehenna_api.services.base import BaseDataManager, BaseService


class UserService(BaseService):
    def get_user(self, user_id: int) -> UserPublic:
        return UserDataManager(self.session).get_user(user_id)

    def get_user_by_username(self, username: str) -> UserPublic:
        return UserDataManager(self.session).get_user_by_username(username)

    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserPublic]:
        return UserDataManager(self.session).get_users(skip, limit)


class UserDataManager(BaseDataManager):
    def get_user(self, user_id: int) -> UserPublic:
        stmt = select(User).where(User.id == user_id)
        model = self.get_one(stmt)
        return UserPublic(**model.to_dict())

    def get_user_by_username(self, username: str) -> UserPublic:
        stmt = select(User).where(User.username == username)
        model = self.get_one(stmt)
        return UserPublic(**model.to_dict())

    def get_users(self, skip: int = 0, limit: int = 100) -> List[UserPublic]:
        schemas: List[UserPublic] = list()
        stmt = select(User).offset(skip).limit(limit)
        for model in self.get_all(stmt):
            schemas += [UserPublic(**model.to_dict())]
        return schemas
