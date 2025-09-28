'''Database connection and session management.'''

import os
from typing import Any
from collections.abc import Generator

from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine

# Database URL from environment variable or default for development
DATABASE_URL = os.getenv(
    'DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/porcaro'
)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    '''Create database tables.'''
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, Any, None]:
    '''Get database session.'''
    with Session(engine) as session:
        yield session
