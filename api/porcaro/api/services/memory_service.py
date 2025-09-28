import logging

import numpy as np

from porcaro.api.utils import get_session_directory

logger = logging.getLogger(__name__)


class InMemoryService:
    '''Service for managing in-memory session data.'''

    def __init__(self, max_memory: int = 1024 * 1024 * 1024) -> None:
        '''Initialize the service.'''
        self._in_mem_session_tracks = {}
        self._id_stack = []
        self._max_memory = max_memory

    def set_session_track(self, session_id: str, track: np.ndarray) -> None:
        '''Set in-memory data for a specific session.'''
        file_path = get_session_directory(session_id).joinpath('track.npy')
        if not file_path.exists():
            np.save(file_path, track)
            logger.info(f'Saved processed track to {file_path}')
        else:
            logger.info(
                f'Processed track already exists at {file_path}, not overwriting.'
            )
        self._in_mem_session_tracks[session_id] = track
        self._id_stack.append(session_id)
        self._check_memory_usage()

    def _check_memory_usage(self) -> None:
        '''Check and log current memory usage.'''
        current_memory = sum(
            track.nbytes for track in self._in_mem_session_tracks.values()
        )
        logger.info(f'Current in-memory usage: {current_memory / (1024**2):.2f} MB')
        while current_memory > self._max_memory and self._id_stack:
            oldest_id = self._id_stack.pop(0)
            if oldest_id in self._in_mem_session_tracks:
                freed_memory = self._in_mem_session_tracks[oldest_id].nbytes
                del self._in_mem_session_tracks[oldest_id]
                current_memory -= freed_memory
                logger.info(
                    f'Removed session {oldest_id} from memory, '
                    f'freed {freed_memory / (1024**2):.2f} MB'
                )

    def get_session_track(self, session_id: str) -> np.ndarray:
        '''Get in-memory track data for a specific session.'''
        if session_id not in self._in_mem_session_tracks:
            file_path = get_session_directory(session_id).joinpath('track.npy')
            if file_path.exists():
                self._in_mem_session_tracks[session_id] = np.load(file_path)
                logger.info(f'Loaded processed track from {file_path}')
            else:
                raise FileNotFoundError(f'No processed track found at {file_path}')
        return self._in_mem_session_tracks[session_id]

    def delete_session_track(self, session_id: str) -> None:
        '''Delete in-memory track data for a specific session.'''
        if session_id in self._in_mem_session_tracks:
            del self._in_mem_session_tracks[session_id]


in_memory_service = InMemoryService()
