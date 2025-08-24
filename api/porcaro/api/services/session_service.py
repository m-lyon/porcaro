'''Session management service.'''

import uuid
import logging
from typing import Dict, Optional
from pathlib import Path
import tempfile
import shutil

from porcaro.api.models import LabelingSession, AudioClip

logger = logging.getLogger(__name__)


class SessionStore:
    '''In-memory store for labeling sessions.'''

    def __init__(self):
        self._sessions: Dict[str, LabelingSession] = {}
        self._session_data: Dict[str, Dict] = {}  # Store clips and other session data
        self._temp_dirs: Dict[str, Path] = {}  # Track temp directories for cleanup

    def create_session(self, filename: str) -> LabelingSession:
        '''Create a new labeling session.'''
        session_id = str(uuid.uuid4())

        # Create temporary directory for this session
        temp_dir = Path(tempfile.mkdtemp(prefix=f'porcaro_session_{session_id[:8]}_'))
        self._temp_dirs[session_id] = temp_dir

        session = LabelingSession(session_id=session_id, filename=filename)

        self._sessions[session_id] = session
        self._session_data[session_id] = {
            'clips': {},
            'audio_data': None,
            'song_data': None,
            'temp_dir': temp_dir,
        }

        logger.info(f'Created session {session_id} for file {filename}')
        return session

    def get_session(self, session_id: str) -> Optional[LabelingSession]:
        '''Get session by ID.'''
        return self._sessions.get(session_id)

    def update_session(
        self, session_id: str, updates: dict
    ) -> Optional[LabelingSession]:
        '''Update session with new data.'''
        if session_id not in self._sessions:
            return None

        session = self._sessions[session_id]
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        return session

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

        # Remove from stores
        del self._sessions[session_id]
        del self._session_data[session_id]

        logger.info(f'Deleted session {session_id}')
        return True

    def get_session_data(self, session_id: str) -> Optional[Dict]:
        '''Get session data (clips, audio, etc.).'''
        return self._session_data.get(session_id)

    def update_session_data(self, session_id: str, data: dict) -> bool:
        '''Update session data.'''
        if session_id not in self._session_data:
            return False

        self._session_data[session_id].update(data)
        return True

    def add_clip(self, session_id: str, clip: AudioClip) -> bool:
        '''Add a clip to the session.'''
        if session_id not in self._session_data:
            return False

        self._session_data[session_id]['clips'][clip.clip_id] = clip
        return True

    def get_clip(self, session_id: str, clip_id: str) -> Optional[AudioClip]:
        '''Get a specific clip from the session.'''
        session_data = self._session_data.get(session_id)
        if not session_data:
            return None

        return session_data['clips'].get(clip_id)

    def get_all_clips(self, session_id: str) -> Dict[str, AudioClip]:
        '''Get all clips for a session.'''
        session_data = self._session_data.get(session_id)
        if not session_data:
            return {}

        return session_data['clips']

    def list_sessions(self) -> Dict[str, LabelingSession]:
        '''List all active sessions.'''
        return self._sessions.copy()


# Global session store instance
session_store = SessionStore()
