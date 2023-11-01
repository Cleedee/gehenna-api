from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gehenna_api.config import config

# engine = create_engine(Settings().DATABASE_URL)


# def get_session():
#    with Session(engine) as session:
#        yield session


SessionFactory = sessionmaker(
    bind=create_engine(config.database.dsn),
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def create_session() -> Iterator[Session]:
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
