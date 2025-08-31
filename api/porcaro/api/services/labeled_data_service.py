'''Service for managing persistent labeled data storage.'''

import json
import shutil
import logging
from typing import Any
from pathlib import Path
from datetime import datetime

import numpy as np

from porcaro.api.models import AudioClip
from porcaro.api.models import LabelingSession
from porcaro.api.models import LabelingSessionData
from porcaro.api.services.audio_service import get_model_input_audio_data

logger = logging.getLogger(__name__)

# Default directory for storing labeled data
DEFAULT_LABELED_DATA_DIR = Path('labeled_data')


class LabeledDataService:
    '''Service for managing persistent storage of labeled clip data.'''

    METADATA_FILENAME = 'metadata.json'

    def __init__(self, base_dir: Path = DEFAULT_LABELED_DATA_DIR):
        '''Initialize the service with a base directory for storage.

        Args:
            base_dir: Base directory for storing labeled data
        '''
        self.base_dir = base_dir
        self.base_dir.mkdir(exist_ok=True)
        logger.info(f'LabeledDataService initialized with base directory: {base_dir}')

    def _get_session_dir(self, session_id: str) -> Path:
        '''Get the directory for a specific session.'''
        return self.base_dir / session_id

    def _get_clip_dir(self, session_id: str, clip_id: str) -> Path:
        '''Get the directory for a specific clip.'''
        return self._get_session_dir(session_id) / clip_id

    def _get_metadata_file(self, session_id: str, clip_id: str) -> Path:
        '''Get the metadata file path for a clip.'''
        return self._get_clip_dir(session_id, clip_id) / self.METADATA_FILENAME

    def _get_audio_file(self, session_id: str, clip_id: str) -> Path:
        '''Get the audio file path for a clip.'''
        return self._get_clip_dir(session_id, clip_id) / f'{clip_id}.npy'

    def save_labeled_clip(
        self,
        session: LabelingSession,
        clip: AudioClip,
        session_data: LabelingSessionData,
    ) -> bool:
        '''Save a labeled clip to disk with all metadata and audio data.

        Args:
            session: The labeling session
            clip: The labeled audio clip
            session_data: Session data containing dataframe with audio clips

        Returns:
            bool: True if saved successfully, False otherwise
        '''
        try:
            clip_dir = self._get_clip_dir(session.session_id, clip.clip_id)
            clip_dir.mkdir(parents=True, exist_ok=True)

            # Extract clip index from clip_id (format: {session_id}_{index})
            clip_index = int(clip.clip_id.split('_')[-1])

            # Get audio data from DataFrame
            if session_data.dataframe is None:
                logger.error(
                    f'No dataframe found in session data for {session.session_id}'
                )
                return False

            audio_data = get_model_input_audio_data(session_data.dataframe, clip_index)

            # Save audio data
            audio_file = self._get_audio_file(session.session_id, clip.clip_id)
            np.save(audio_file, audio_data)

            # Prepare metadata
            metadata = {
                'clip_id': clip.clip_id,
                'session_info': {
                    'session_id': session.session_id,
                    'filename': session.filename,
                    'time_signature': {
                        'numerator': session.time_signature.numerator,
                        'denominator': session.time_signature.denominator,
                    }
                    if session.time_signature
                    else None,
                    'bpm': session.bpm,
                    'created_at': session.created_at.isoformat(),
                },
                'clip_info': {
                    'start_sample': clip.start_sample,
                    'start_time': clip.start_time,
                    'end_sample': clip.end_sample,
                    'end_time': clip.end_time,
                    'sample_rate': clip.sample_rate,
                    'peak_sample': clip.peak_sample,
                    'peak_time': clip.peak_time,
                    'predicted_labels': [
                        label.value if hasattr(label, 'value') else str(label)
                        for label in clip.predicted_labels
                    ],
                    'user_label': [
                        label.value if hasattr(label, 'value') else str(label)
                        for label in clip.user_label
                    ]
                    if clip.user_label
                    else None,
                    'confidence_scores': clip.confidence_scores,
                    'labeled_at': clip.labeled_at.isoformat()
                    if clip.labeled_at
                    else None,
                },
                'files': {
                    'model_input_audio_file': audio_file.name,
                },
                'saved_at': datetime.now().isoformat(),
            }

            # Save metadata
            metadata_file = self._get_metadata_file(session.session_id, clip.clip_id)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f'Saved labeled clip {clip.clip_id} to {clip_dir}')
            return True

        except Exception as e:
            logger.error(f'Error saving labeled clip {clip.clip_id}: {str(e)}')
            return False

    def remove_labeled_clip(self, session_id: str, clip_id: str) -> bool:
        '''Remove a labeled clip from disk storage.

        Args:
            session_id: The session ID
            clip_id: The clip ID

        Returns:
            bool: True if removed successfully, False otherwise
        '''
        try:
            clip_dir = self._get_clip_dir(session_id, clip_id)

            if not clip_dir.exists():
                logger.warning(f'Clip directory does not exist: {clip_dir}')
                return True  # Already removed or never existed

            # Remove the entire clip directory
            shutil.rmtree(clip_dir)
            logger.info(f'Removed labeled clip {clip_id} from {clip_dir}')
            return True

        except Exception as e:
            logger.error(f'Error removing labeled clip {clip_id}: {str(e)}')
            return False

    def get_labeled_clips_for_session(self, session_id: str) -> list[dict[str, Any]]:
        '''Get all labeled clips for a session from disk storage.

        Args:
            session_id: The session ID

        Returns:
            List of metadata dictionaries for all labeled clips
        '''
        try:
            session_dir = self._get_session_dir(session_id)

            if not session_dir.exists():
                return []

            labeled_clips = []

            # Iterate through clip directories
            for clip_dir in session_dir.iterdir():
                if not clip_dir.is_dir():
                    continue

                metadata_file = clip_dir / self.METADATA_FILENAME
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        labeled_clips.append(metadata)
                    except json.JSONDecodeError as e:
                        logger.error(
                            f'Error reading metadata file {metadata_file}: {str(e)}'
                        )
                        continue

            return labeled_clips

        except Exception as e:
            logger.error(
                f'Error getting labeled clips for session {session_id}: {str(e)}'
            )
            return []

    def remove_session(self, session_id: str) -> bool:
        '''Remove all labeled data for a session.

        Args:
            session_id: The session ID

        Returns:
            bool: True if removed successfully, False otherwise
        '''
        try:
            session_dir = self._get_session_dir(session_id)

            if not session_dir.exists():
                return True  # Already removed or never existed

            shutil.rmtree(session_dir)
            logger.info(f'Removed labeled data for session {session_id}')
            return True

        except Exception as e:
            logger.error(f'Error removing session {session_id}: {str(e)}')
            return False

    def get_all_labeled_clips(self) -> list[dict[str, Any]]:
        '''Get all labeled clips from all sessions.

        Returns:
            List of metadata dictionaries for all labeled clips
        '''
        all_clips = []

        try:
            if not self.base_dir.exists():
                return all_clips

            # Iterate through session directories
            for session_dir in self.base_dir.iterdir():
                if not session_dir.is_dir():
                    continue

                session_clips = self.get_labeled_clips_for_session(session_dir.name)
                all_clips.extend(session_clips)

        except Exception as e:
            logger.error(f'Error getting all labeled clips: {str(e)}')

        return all_clips

    def get_statistics(self) -> dict[str, Any]:
        '''Get statistics about labeled data.

        Returns:
            Dictionary containing statistics
        '''
        try:
            stats = {
                'total_sessions': 0,
                'total_labeled_clips': 0,
                'clips_by_label': {},
                'sessions': [],
            }

            if not self.base_dir.exists():
                return stats

            for session_dir in self.base_dir.iterdir():
                if not session_dir.is_dir():
                    continue

                stats['total_sessions'] += 1
                session_clips = self.get_labeled_clips_for_session(session_dir.name)
                session_clip_count = len(session_clips)
                stats['total_labeled_clips'] += session_clip_count

                session_info = {
                    'session_id': session_dir.name,
                    'clip_count': session_clip_count,
                }

                if session_clips:
                    # Get session metadata from first clip
                    first_clip = session_clips[0]
                    if 'session_info' in first_clip:
                        session_info.update(first_clip['session_info'])

                stats['sessions'].append(session_info)

                # Count clips by label
                for clip_metadata in session_clips:
                    user_labels = clip_metadata.get('clip_info', {}).get(
                        'user_label', []
                    )
                    if user_labels:
                        for label in user_labels:
                            stats['clips_by_label'][label] = (
                                stats['clips_by_label'].get(label, 0) + 1
                            )

            return stats

        except Exception as e:
            logger.error(f'Error getting statistics: {str(e)}')
            return {'error': str(e)}


# Global instance
labeled_data_service = LabeledDataService()
