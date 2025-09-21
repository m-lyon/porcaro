'''Session management service.'''

import uuid
import shutil
import logging
import tempfile
from typing import TypeVar
from pathlib import Path

from pydantic import BaseModel

from porcaro.api.models import AudioClip
from porcaro.api.models import LabelingSession
from porcaro.api.models import LabelingSessionData
from porcaro.api.services.labeled_data_service import labeled_data_service

logger = logging.getLogger(__name__)


T = TypeVar('T', bound=BaseModel)


def update_model(container: dict[str, T], model_id: str, updates: dict) -> T | None:
    '''Updates a Pydantic model with new data.'''
    if model_id not in container:
        return None

    model = container[model_id]
    for key, value in updates.items():
        if hasattr(model, key):
            setattr(model, key, value)

    return model


class SessionStore:
    '''In-memory store for labeling sessions.'''

    def __init__(self) -> None:
        '''Initialize the session store.'''
        self._sessions: dict[str, LabelingSession] = {}
        self._session_data: dict[str, LabelingSessionData] = {}
        self._temp_dirs: dict[str, Path] = {}  # Track temp directories for cleanup

    def create_session(self, filename: str) -> LabelingSession:
        '''Create a new labeling session.'''
        session_id = str(uuid.uuid4())

        # Create temporary directory for this session
        temp_dir = Path(tempfile.mkdtemp(prefix=f'porcaro_session_{session_id[:8]}_'))
        self._temp_dirs[session_id] = temp_dir

        session = LabelingSession(session_id=session_id, filename=filename)
        session_data = LabelingSessionData(temp_dir=temp_dir)

        self._sessions[session_id] = session
        self._session_data[session_id] = session_data

        logger.info(f'Created session {session_id} for file {filename}')
        return session

    def get_session(self, session_id: str) -> LabelingSession | None:
        '''Get session by ID.'''
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, updates: dict) -> LabelingSession | None:
        '''Update session with new data.'''
        return update_model(self._sessions, session_id, updates)

    def delete_session(self, session_id: str) -> bool:
        '''Delete a session and clean up resources.'''
        if session_id not in self._sessions:
            return False

        # Clean up temporary directory
        if session_id in self._temp_dirs:
            temp_dir = self._temp_dirs[session_id]
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            del self._temp_dirs[session_id]

        # Clean up labeled data - import here to avoid circular imports
        try:
            labeled_data_service.remove_session(session_id)
        except Exception:
            logger.exception(f'Error removing labeled data for session {session_id}')

        # Remove from stores
        del self._sessions[session_id]
        del self._session_data[session_id]

        logger.info(f'Deleted session {session_id}')
        return True

    def get_session_data(self, session_id: str) -> LabelingSessionData | None:
        '''Get session data (clips, audio, etc.).'''
        return self._session_data.get(session_id)

    def update_session_data(
        self, session_id: str, data: dict
    ) -> LabelingSessionData | None:
        '''Update session data.'''
        return update_model(self._session_data, session_id, data)

    def add_clip(self, session_id: str, clip: AudioClip) -> bool:
        '''Add a clip to the session.'''
        if session_id not in self._session_data:
            return False

        self._session_data[session_id].clips[clip.clip_id] = clip
        return True

    def get_clip(self, session_id: str, clip_id: str) -> AudioClip | None:
        '''Get a specific clip from the session.'''
        session_data = self._session_data.get(session_id)
        if not session_data:
            return None

        return session_data.clips.get(clip_id)

    def get_all_clips(self, session_id: str) -> dict[str, AudioClip]:
        '''Get all clips for a session.'''
        session_data = self._session_data.get(session_id)
        if not session_data:
            return {}

        return session_data.clips

    def list_sessions(self) -> dict[str, LabelingSession]:
        '''List all active sessions.'''
        return self._sessions.copy()


# Global session store instance
session_store = SessionStore()
