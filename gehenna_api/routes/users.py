from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from gehenna_api.database import create_session
from gehenna_api.models.auth import User
from gehenna_api.schemas import UserList, UserPublic, UserSchema
from gehenna_api.security import get_current_user, get_password_hash
from gehenna_api.services.users import UserService

router = APIRouter(prefix='/users', tags=['users'])


@router.post('/', response_model=UserPublic, status_code=201)
def create_user(user: UserSchema, session: Session = Depends(create_session)):
    db_user = session.scalar(select(User).where(User.email == user.email))
    if db_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        password=hashed_password,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.put('/{user_id}', response_model=UserPublic)
def update_user(
    user_id: int,
    user: UserSchema,
    session: Session = Depends(create_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=400, detail='Not enough permissions')
    current_user.username = user.username
    current_user.password = user.password
    current_user.email = user.email
    session.commit()
    session.refresh(current_user)
    return current_user

@router.get('/', response_model=UserList)
def get_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(create_session)):
    lista = UserService(session).get_users(skip, limit)
    return {'users': lista}
