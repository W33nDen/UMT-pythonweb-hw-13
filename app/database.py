from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base class for project models.
    """
    pass


db_url = get_settings().database_url
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator for database session local context.

    Yields:
        Generator[Session, None, None]: Database session instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

