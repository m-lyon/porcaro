'''Database connection and session management.'''

import os
from typing import Any
from functools import lru_cache
from collections.abc import Generator

from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine


@lru_cache
def get_engine() -> Any:
    '''Get or create the database engine.'''
    database_url = os.getenv('PORCARO_DATABASE_URL')
    if database_url is None:
        raise ValueError('PORCARO_DATABASE_URL environment variable is not set')
    return create_engine(database_url, echo=False)


def create_db_and_tables() -> None:
    '''Create database tables.'''
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session, Any, None]:
    '''Get database session.'''
    with Session(get_engine()) as session:
        yield session
