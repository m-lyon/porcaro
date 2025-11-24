import os
from pathlib import Path

from porcaro.api.database.models import LabelingSession


def get_session_directory(session: LabelingSession | str) -> Path:
    '''Get the directory path for a session's data.'''
    session_dir = Path(os.getenv('PORCARO_SESSION_DIR', 'data/sessions'))
    if isinstance(session, str):
        return session_dir.joinpath(session)
    return session_dir.joinpath(session.id)


def get_upload_filepath(session: LabelingSession) -> Path:
    '''Get the file path of the uploaded audio file for a session.'''
    return get_session_directory(session).joinpath(session.filename)


def get_drum_track_filepath(session: LabelingSession) -> Path:
    '''Get the file path of the drum-isolated track for a session.'''
    upload_path = get_upload_filepath(session)
    return upload_path.with_name(f'{upload_path.stem}_drums.wav')


def get_track_filepath(session: LabelingSession | str) -> Path:
    '''Get the file path of the processed track for a session.'''
    return get_session_directory(session).joinpath('track.npy')
