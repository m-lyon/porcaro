'''Test configuration and fixtures for the database service tests.'''

import tempfile

import pytest
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from pytest_postgresql import factories

from porcaro.api.services.database_service import DatabaseSessionService

# Create PostgreSQL process and client fixtures
postgresql_proc = factories.postgresql_proc(
    port=None, unixsocketdir=tempfile.gettempdir()
)
postgresql = factories.postgresql('postgresql_proc')


@pytest.fixture
def test_db_engine(postgresql):
    '''Create a test database engine using PostgreSQL.'''
    # Get connection info from the postgresql fixture
    user = postgresql.info.user
    host = postgresql.info.host
    port = postgresql.info.port
    dbname = postgresql.info.dbname

    # Create engine with PostgreSQL connection
    database_url = f'postgresql+psycopg://{user}@{host}:{port}/{dbname}'
    engine = create_engine(database_url, echo=False)

    # Create all tables
    SQLModel.metadata.create_all(engine)

    yield engine

    # Clean up - drop all tables
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def test_db_session(test_db_engine):
    '''Create a test database session.'''
    with Session(test_db_engine) as session:
        yield session


@pytest.fixture
def test_db_service(test_db_engine, monkeypatch):
    '''Create a test database service with patched get_session.'''

    # Mock the get_session function to use our test engine
    def mock_get_session():
        with Session(test_db_engine) as session:
            yield session

    # Patch the get_session import in the database service module
    monkeypatch.setattr(
        'porcaro.api.services.database_service.get_session', mock_get_session
    )

    # Create service instance
    service = DatabaseSessionService()
    return service
