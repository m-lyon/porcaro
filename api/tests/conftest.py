'''Test configuration and fixtures for the database service tests.'''

import pytest
from dotenv import find_dotenv
from dotenv import load_dotenv
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import create_engine
from pytest_postgresql import factories
from fastapi.testclient import TestClient

from porcaro.api.server import create_app
from porcaro.api.database.models import AudioClip
from porcaro.api.database.models import DrumLabel
from porcaro.api.database.models import TimeSignature
from porcaro.api.database.models import LabelingSession
from porcaro.api.database.models import SessionMetadata
from porcaro.api.services.database_service import DatabaseSessionService

# Create PostgreSQL process and client fixtures
postgresql_proc = factories.postgresql_proc(port=None)
postgresql = factories.postgresql('postgresql_proc')


@pytest.fixture(scope='session', autouse=True)
def load_env() -> None:
    env_file = find_dotenv('.env.test')
    load_dotenv(env_file)


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
    '''Create a database session for direct database operations in tests.'''
    with Session(test_db_engine) as session:
        yield session


@pytest.fixture
def test_db_service(test_db_engine, mocker, tmp_path):
    '''Create a test database service with patched get_session.'''

    # Mock the get_session function to use our test engine
    def mock_get_session():
        with Session(test_db_engine) as session:
            yield session

    mocker.patch('porcaro.api.services.database_service.get_session', mock_get_session)
    mocker.patch(
        'porcaro.api.services.database_service.get_session_directory',
        return_value=tmp_path,
    )

    # Create service instance
    service = DatabaseSessionService()
    return service


@pytest.fixture
def client(test_db_engine, mocker):
    def mock_get_session():
        with Session(test_db_engine) as session:
            yield session

    # Mock the get_session function to use our test engine
    mocker.patch('porcaro.api.services.database_service.get_session', mock_get_session)
    app = create_app(create_tables=False)
    return TestClient(app)


@pytest.fixture
def client_single_session(client, mocker, tmp_path):
    mocker.patch(
        'porcaro.api.services.database_service.get_session_directory',
        return_value=tmp_path,
    )
    track_path = tmp_path / 'track.npy'
    mocker.patch(
        'porcaro.api.services.memory_service.get_track_filepath',
        return_value=track_path,
    )
    upload_path = tmp_path / 'test.wav'
    mocker.patch(
        'porcaro.api.routers.sessions.get_upload_filepath',
        return_value=upload_path,
    )

    return client, (upload_path, track_path)


@pytest.fixture
def make_clips():
    def _make_clips(session_id):
        return [
            AudioClip(
                start_sample=0,
                start_time=0.0,
                end_sample=1000,
                end_time=1.0,
                sample_rate=44100,
                peak_sample=500,
                peak_time=0.5,
                predicted_labels=[DrumLabel.KICK_DRUM],
                user_label=[DrumLabel.KICK_DRUM],
                session_id=session_id,
            ),
            AudioClip(
                start_sample=1000,
                start_time=1.0,
                end_sample=2000,
                end_time=2.0,
                sample_rate=44100,
                peak_sample=1500,
                peak_time=1.5,
                predicted_labels=[DrumLabel.SNARE_DRUM],
                session_id=session_id,
            ),
        ]

    return _make_clips


@pytest.fixture
def sample_session(test_db_session):
    '''Create a sample session for testing.'''
    session = LabelingSession(id='test-id', filename='test.wav')
    test_db_session.add(session)
    test_db_session.commit()
    test_db_session.refresh(session)
    return session


@pytest.fixture
def sample_session_expanded(test_db_session, make_clips):
    '''Create a sample session for testing with expanded clips.'''
    session = LabelingSession(id='expanded', filename='expanded.wav')
    processing_metadata = SessionMetadata(
        id='expanded',
        processed=True,
        duration=10.0,
        song_sample_rate=44100.0,
        onset_algorithm='test_onset',
        prediction_algorithm='test_prediction',
        model_weights_path='test_weights.pt',
    )
    time_signature = TimeSignature(numerator=4, denominator=4)
    session.time_signature = time_signature
    test_db_session.add(session)
    test_db_session.add(processing_metadata)
    clips = make_clips(session.id)
    test_db_session.add_all(clips)
    test_db_session.commit()
    test_db_session.refresh(session)
    return session


@pytest.fixture
def multi_sample_expanded_sessions(test_db_session, make_clips):
    '''Create multiple sample sessions for testing with expanded clips.'''
    sessions = []
    time_signature = TimeSignature(numerator=4, denominator=4)
    test_db_session.add(time_signature)
    for i in range(3):
        session = LabelingSession(id=f'expanded-{i}', filename=f'expanded-{i}.wav')
        processing_metadata = SessionMetadata(
            id=f'expanded-{i}',
            processed=True,
            duration=10.0 + i,
            song_sample_rate=44100.0,
            onset_algorithm='test_onset',
            prediction_algorithm='test_prediction',
            model_weights_path='test_weights.pt',
        )
        session.time_signature = time_signature
        test_db_session.add(session)
        test_db_session.add(processing_metadata)
        clips = make_clips(session.id)
        test_db_session.add_all(clips)
        sessions.append(session)
    test_db_session.commit()
    for session in sessions:
        test_db_session.refresh(session)
    return sessions
