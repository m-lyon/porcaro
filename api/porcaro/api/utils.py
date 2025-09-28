from pathlib import Path

from porcaro.api.database.models import AudioClip
from porcaro.api.database.models import LabelingSession

SESSIONS_DATA_DIR = Path('data/sessions')


def get_session_directory(session: LabelingSession | str) -> Path:
    '''Get the directory path for a session's data.'''
    if isinstance(session, str):
        return SESSIONS_DATA_DIR.joinpath(session)
    return SESSIONS_DATA_DIR.joinpath(session.id)


def get_filepath_from_session(session: LabelingSession) -> Path:
    '''Get the file path of the uploaded audio file for a session.'''
    return get_session_directory(session).joinpath(session.filename)


def get_clip_filepath(clip: AudioClip) -> Path:
    '''Get the file path for a specific audio clip.'''
    session_dir = get_session_directory(clip.session_id)
    clip_dir = session_dir.joinpath('clips')
    if not clip_dir.exists():
        clip_dir.mkdir(parents=True)
    return clip_dir.joinpath(f'{clip.id}.npy')
