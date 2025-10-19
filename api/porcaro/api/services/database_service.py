'''Database service layer for session and clip management.'''

import shutil
import logging
from typing import Any
from pathlib import Path
from datetime import UTC
from datetime import datetime
from collections.abc import Sequence

import numpy as np
import pandas as pd
from sqlmodel import Session
from sqlmodel import col
from sqlmodel import select

from porcaro.api.utils import get_clip_filepath
from porcaro.api.utils import get_session_directory
from porcaro.api.database.models import AudioClip
from porcaro.api.database.models import DrumLabel
from porcaro.api.database.models import TimeSignature
from porcaro.api.database.models import LabelingSession
from porcaro.api.database.models import ProcessingMetadata
from porcaro.api.database.models import TimeSignatureModel
from porcaro.api.database.models import ProcessingMetadataModel
from porcaro.api.database.connection import get_session

logger = logging.getLogger('uvicorn')


LABEL_MAPPING = {label.value: label for label in DrumLabel}


class DatabaseSessionService:
    '''Database-backed session management service.'''

    def __init__(self) -> None:
        '''Initialize the service.'''

    # --- Session Management ---
    def create_session(self, filename: str) -> LabelingSession:
        '''Create a new labeling session.'''
        # Create database session
        with next(get_session()) as db_session:
            labeling_session = LabelingSession(filename=filename)
            db_session.add(labeling_session)
            db_session.commit()
            db_session.refresh(labeling_session)

        logger.info(f'Created session {labeling_session.id} for file {filename}')

        # Create directory for this session
        get_session_directory(labeling_session).mkdir(parents=True, exist_ok=True)

        return labeling_session

    def get_session(self, session_id: str) -> LabelingSession | None:
        '''Get session by ID.'''
        with next(get_session()) as db_session:
            statement = select(LabelingSession).where(LabelingSession.id == session_id)
            labeling_session = db_session.exec(statement).first()
            return labeling_session

    def update_session(
        self, session_id: str, updates: dict[str, Any]
    ) -> LabelingSession | None:
        '''Update session with new data.'''
        with next(get_session()) as db_session:
            statement = select(LabelingSession).where(LabelingSession.id == session_id)
            labeling_session = db_session.exec(statement).first()

            if not labeling_session:
                return None

            # Handle time signature updates separately
            if 'time_signature' in updates:
                self._update_session_time_signature(
                    db_session, labeling_session, updates.pop('time_signature')
                )

            # Handle processing updates separately
            if 'processing_metadata' in updates:
                self._update_session_processing_metadata(
                    db_session,
                    labeling_session,
                    updates.pop('processing_metadata'),
                )

            # Update other fields
            for key, value in updates.items():
                setattr(labeling_session, key, value)

            db_session.add(labeling_session)
            db_session.commit()
            db_session.refresh(labeling_session)

            return labeling_session

    @staticmethod
    def _update_session_time_signature(
        db_session: Session,
        labeling_session: LabelingSession,
        ts_data: TimeSignatureModel,
    ) -> None:
        '''Update or create time signature for a session.'''
        if not isinstance(ts_data, TimeSignatureModel):
            raise TypeError('time_signature must be a TimeSignatureModel instance')

        # Create or get time signature
        ts_statement = select(TimeSignature).where(
            TimeSignature.numerator == ts_data.numerator,
            TimeSignature.denominator == ts_data.denominator,
        )
        time_sig = db_session.exec(ts_statement).first()

        if not time_sig:
            time_sig = TimeSignature(**ts_data.model_dump())
            db_session.add(time_sig)
            db_session.commit()
            db_session.refresh(time_sig)

        labeling_session.time_signature = time_sig

    @staticmethod
    def _update_session_processing_metadata(
        db_session: Session,
        labeling_session: LabelingSession,
        metadata: ProcessingMetadataModel,
    ) -> None:
        '''Update or create processing metadata for a session.'''
        if not isinstance(metadata, ProcessingMetadataModel):
            raise TypeError(
                'processing_metadata must be a ProcessingMetadataModel instance'
            )

        # Get existing metadata or create new
        statement = select(ProcessingMetadata).where(
            ProcessingMetadata.id == labeling_session.id
        )
        proc_metadata = db_session.exec(statement).first()

        if not proc_metadata:
            proc_metadata = ProcessingMetadata(
                id=labeling_session.id, **metadata.model_dump()
            )
        else:
            for key, value in metadata.model_dump().items():
                setattr(proc_metadata, key, value)
        db_session.add(proc_metadata)
        db_session.commit()
        db_session.refresh(proc_metadata)

        labeling_session.processing_metadata = proc_metadata

    def delete_session(self, session_id: str) -> bool:
        '''Delete a session and clean up resources.'''
        with next(get_session()) as db_session:
            # Delete session (cascades to clips & metadata)
            statement = select(LabelingSession).where(LabelingSession.id == session_id)
            labeling_session = db_session.exec(statement).first()

            if not labeling_session:
                return False

            # Remove session directory
            session_dir = get_session_directory(labeling_session)
            if session_dir.exists():
                shutil.rmtree(session_dir)

            # Delete from database
            db_session.delete(labeling_session)
            db_session.commit()

        logger.info(f'Deleted session {session_id}')
        return True

    # --- Clip Management ---
    def save_clips_from_dataframe(self, session_id: str, df: pd.DataFrame) -> int:
        '''Save clips to database.'''
        created_files = []
        with next(get_session()) as db_session:
            try:
                for _, row in df.iterrows():
                    predicted_labels = []
                    if 'hits' in row and isinstance(row['hits'], list):
                        predicted_labels = [
                            LABEL_MAPPING[label]
                            for label in row['hits']
                            if label in LABEL_MAPPING
                        ]
                    clip = AudioClip(
                        start_sample=int(row['start_sample']),
                        start_time=float(row['start_time']),
                        end_sample=int(row['end_sample']),
                        end_time=float(row['end_time']),
                        sample_rate=int(row['sampling_rate']),
                        peak_sample=int(row['peak_sample']),
                        peak_time=float(row['peak_time']),
                        predicted_labels=predicted_labels,
                        session_id=session_id,
                    )
                    file_path = get_clip_filepath(clip)
                    np.save(file_path, row['audio_clip'])
                    created_files.append(file_path)
                    clip.audio_file_path = str(file_path)
                    db_session.add(clip)
                db_session.commit()
            except Exception:
                # Clean up any files that were created
                for file_path in created_files:
                    try:
                        if file_path.exists():
                            file_path.unlink()
                            logger.debug(f'Cleaned up file: {file_path}')
                    except (
                        FileNotFoundError,
                        PermissionError,
                        OSError,
                    ) as cleanup_error:
                        logger.warning(
                            f'Failed to cleanup file {file_path}: {cleanup_error}'
                        )
                logger.exception(f'Error saving clips for session {session_id}')
                raise
        return len(df)

    def save_clips(self, session_id: str, clips: list[AudioClip]) -> int:
        '''Save clips to database from a dictionary.'''
        with next(get_session()) as db_session:
            try:
                for clip in clips:
                    # Set the session_id if not already set
                    clip.session_id = session_id
                    db_session.add(clip)
                db_session.commit()
            except Exception:
                logger.exception(f'Error saving clips for session {session_id}')
                raise
        return len(clips)

    def get_clips(
        self, session_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[AudioClip], int]:
        '''Get clips for a session with pagination.'''
        with next(get_session()) as db_session:
            # Get total count
            count_statement = select(AudioClip).where(
                AudioClip.session_id == session_id
            )
            total = len(db_session.exec(count_statement).all())

            # Get paginated clips
            statement = (
                select(AudioClip)
                .where(AudioClip.session_id == session_id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            clips = db_session.exec(statement).all()
            return clips, total

    def get_clip(self, session_id: str, clip_id: str) -> AudioClip | None:
        '''Get a specific clip.'''
        with next(get_session()) as db_session:
            statement = select(AudioClip).where(
                AudioClip.session_id == session_id,
                AudioClip.id == clip_id,
            )
            clip = db_session.exec(statement).first()
            return clip

    def delete_clip(self, session_id: str, clip_id: str) -> bool:
        '''Delete a specific clip and its associated audio file.'''
        with next(get_session()) as db_session:
            statement = select(AudioClip).where(
                AudioClip.session_id == session_id,
                AudioClip.id == clip_id,
            )
            clip = db_session.exec(statement).first()

            if not clip:
                return False

            # Delete associated audio file if it exists
            if clip.audio_file_path:
                file_path = Path(clip.audio_file_path)
                try:
                    if file_path.exists():
                        file_path.unlink()
                        logger.debug(f'Deleted audio file: {file_path}')
                except (FileNotFoundError, PermissionError, OSError) as e:
                    logger.warning(f'Failed to delete audio file {file_path}: {e}')

            # Delete clip from database
            db_session.delete(clip)
            db_session.commit()

            logger.info(f'Deleted clip {clip_id} from session {session_id}')
            return True

    def count_total_clips(self, session_id: str) -> int:
        '''Get the total number of clips for a session.'''
        with next(get_session()) as db_session:
            statement = select(AudioClip).where(AudioClip.session_id == session_id)
            count = len(db_session.exec(statement).all())
            return count or 0

    # --- Label Management ---
    def count_labeled_clips(self, session_id: str) -> int:
        '''Get the number of clips that have a user-assigned label for a session.'''
        with next(get_session()) as db_session:
            statement = (
                select(AudioClip)
                .where(AudioClip.session_id == session_id)
                .where(col(AudioClip.user_label) != None)  # noqa: E711
            )
            count = len(db_session.exec(statement).all())
            return count or 0

    def update_clip_label(
        self, session_id: str, clip_id: str, labels: list[DrumLabel]
    ) -> AudioClip | None:
        '''Update clip label.'''
        with next(get_session()) as db_session:
            statement = select(AudioClip).where(
                AudioClip.session_id == session_id,
                AudioClip.id == clip_id,
            )
            clip = db_session.exec(statement).first()

            if not clip:
                return None

            clip.user_label = labels
            clip.labeled_at = datetime.now(UTC)

            db_session.add(clip)
            db_session.commit()
            db_session.refresh(clip)

            return clip

    def remove_clip_label(self, session_id: str, clip_id: str) -> AudioClip | None:
        '''Remove clip label.'''
        with next(get_session()) as db_session:
            statement = select(AudioClip).where(
                AudioClip.session_id == session_id,
                AudioClip.id == clip_id,
            )
            clip = db_session.exec(statement).first()

            if not clip:
                return None

            clip.user_label = None
            clip.labeled_at = None

            db_session.add(clip)
            db_session.commit()
            db_session.refresh(clip)

            return clip

    def get_labeled_clips(self, session_id: str) -> list[AudioClip]:
        '''Get all labeled clips for a session.'''
        with next(get_session()) as db_session:
            statement = select(AudioClip).where(AudioClip.session_id == session_id)
            clips = db_session.exec(statement).all()

            # Filter clips that have actual user labels (not None or empty)
            labeled_clips = [
                clip
                for clip in clips
                if clip.user_label is not None and len(clip.user_label) > 0
            ]

            return labeled_clips

    def get_all_labeled_clips(self) -> list[AudioClip]:
        '''Get all labeled clips from all sessions.'''
        with next(get_session()) as db_session:
            statement = select(AudioClip)
            db_clips = db_session.exec(statement).all()

            # Filter clips that have actual user labels (not None or empty)
            return [
                clip
                for clip in db_clips
                if clip.user_label is not None and len(clip.user_label) > 0
            ]


# Create a global instance
database_session_service = DatabaseSessionService()
