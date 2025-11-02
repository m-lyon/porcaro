import logging

from celery import Task

from porcaro.api.utils import get_upload_filepath
from porcaro.api.utils import get_drum_track_filepath
from porcaro.api.celery_app import celery_app
from porcaro.api.services.audio_service import predict_from_drum_track
from porcaro.api.services.audio_service import create_drum_isolated_track
from porcaro.api.services.memory_service import in_memory_service
from porcaro.api.services.database_service import database_session_service

logger = logging.getLogger(__name__)


class TaskError(Exception):
    '''Custom exception for task errors.'''


@celery_app.task(bind=True)
def process_audio_task(self: Task, session_id: str, request_data: dict) -> dict:
    '''Celery task to process audio file.'''
    try:
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting audio processing...'},
        )

        # Get session and file path
        session = database_session_service.get_session(session_id)
        if not session:
            raise TaskError(f'Session {session_id} not found')  # noqa: TRY301

        file_path = get_upload_filepath(session)
        if not file_path.exists():
            raise TaskError(f'Audio file not found for session {session_id}')  # noqa: TRY301

        logger.info(f'Processing audio for session {session_id}')

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Extracting drum track...'},
        )

        # Create drum-isolated track
        drum_file_path = get_drum_track_filepath(session)
        create_drum_isolated_track(
            file_path=file_path,
            output_path=drum_file_path,
            device=request_data['device'],
            offset=request_data['offset'],
            duration=request_data['duration'],
        )

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Running transcription...'},
        )

        # Process audio through porcaro pipeline
        track, df, bpm, metadata = predict_from_drum_track(
            file_path=drum_file_path,
            time_sig=request_data['time_signature'],
            start_beat=request_data['start_beat'],
            offset=request_data['offset'],
            duration=request_data['duration'],
            resolution=request_data['resolution'],
        )

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 95,
                'total': 100,
                'status': 'Saving results to database...',
            },
        )

        # Save processed data in memory for quick access
        in_memory_service.set_session_track(session_id, track)

        # Save clips to database
        num_clips = database_session_service.save_clips_from_dataframe(session_id, df)

        # Update session with processing results
        database_session_service.update_session(
            session_id,
            {
                'time_signature': request_data['time_signature'],
                'start_beat': request_data['start_beat'],
                'offset': request_data['offset'],
                'resolution': request_data['resolution'],
                'bpm': bpm,
                'session_metadata': metadata,
            },
        )

        logger.info(f'Processing complete for session {session_id}: {num_clips} clips')

        return {
            'session_id': session_id,
            'total_clips': num_clips,
            'bpm': bpm,
            'duration': metadata.duration,
            'status': 'completed',
        }

    except Exception as e:
        logger.exception(f'Error processing audio for session {session_id}')
        self.update_state(
            state='FAILURE', meta={'status': str(e), 'session_id': session_id}
        )
        raise
