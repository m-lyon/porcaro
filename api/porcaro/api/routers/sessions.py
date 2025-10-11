'''API router for session management endpoints.'''

import logging
from pathlib import Path

import anyio
from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import HTTPException
from fastapi import status

from porcaro.api.utils import get_filepath_from_session
from porcaro.api.models import SessionProgress
from porcaro.api.models import ProcessAudioRequest
from porcaro.api.models import DeleteSessionResponse
from porcaro.api.models import ProcessAudioSessionResponse
from porcaro.api.database.models import LabelingSession
from porcaro.api.services.audio_service import process_audio_file
from porcaro.api.services.memory_service import in_memory_service
from porcaro.api.services.database_service import database_session_service

logger = logging.getLogger('uvicorn')

router = APIRouter()


@router.post('/', operation_id='create_session')
async def create_session(file: UploadFile) -> LabelingSession:
    '''Create a new labeling session by uploading an audio file.'''
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='No filename provided'
        )

    # Validate file format (basic check)
    allowed_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unsupported file format. Allowed: {", ".join(allowed_extensions)}',
        )
    try:
        # Create session
        session = database_session_service.create_session(file.filename)
    except Exception as e:
        logger.exception('Error creating session from database service')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create session',
        ) from e

    # Save uploaded file to disk
    try:
        file_path = get_filepath_from_session(session)

        # Write uploaded file
        async with await anyio.open_file(file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)

        logger.info(f'Saved {file.filename} to disk')
        return session

    except Exception as e:
        logger.exception('Error creating session')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create session',
        ) from e


@router.get('/{session_id}', operation_id='get_session')
async def get_session(session_id: str) -> LabelingSession:
    '''Get session information by ID.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    return session


@router.post('/{session_id}/process', operation_id='process_session_audio')
async def process_session_audio(
    session_id: str, request: ProcessAudioRequest
) -> ProcessAudioSessionResponse:
    '''Process the uploaded audio file through the transcription pipeline.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    file_path = get_filepath_from_session(session)
    if not file_path.exists():
        logger.error(f'Audio file not found for session {session_id}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No audio file found for session',
        )

    try:
        logger.info(f'Processing audio for session {session_id}')

        # Process audio through porcaro pipeline
        track, df, bpm, metadata = process_audio_file(
            file_path=file_path,
            time_sig=request.time_signature,
            start_beat=request.start_beat,
            offset=request.offset,
            duration=request.duration,
            resolution=request.resolution,
        )

        # Save processed data in memory for quick access
        in_memory_service.set_session_track(session_id, track)

        # Save clips to database
        num_clips = database_session_service.save_clips_from_dataframe(session_id, df)

        # Update session with processing results
        database_session_service.update_session(
            session_id,
            {
                'time_signature': request.time_signature,
                'start_beat': request.start_beat,
                'offset': request.offset,
                'resolution': request.resolution,
                'bpm': bpm,
                'processing_metadata': metadata,
            },
        )

        logger.info(f'Processing complete for session {session_id}: {num_clips} clips')

        return ProcessAudioSessionResponse(
            total_clips=num_clips, bpm=bpm, duration=metadata.duration
        )

    except Exception as e:
        logger.exception(f'Error processing audio for session {session_id}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to process audio: {e!s}',
        ) from e


@router.get('/{session_id}/progress', operation_id='get_session_progress')
async def get_session_progress(session_id: str) -> SessionProgress:
    '''Get the labeling progress for a session.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    total_clips = database_session_service.count_total_clips(session_id)
    labeled_clips = database_session_service.count_labeled_clips(session_id)
    progress_percentage = (labeled_clips / total_clips * 100) if total_clips > 0 else 0

    return SessionProgress(
        session_id=session_id,
        total_clips=total_clips,
        labeled_clips=labeled_clips,
        progress_percentage=round(progress_percentage, 2),
        remaining_clips=total_clips - labeled_clips,
    )


@router.delete('/{session_id}', operation_id='delete_session')
async def delete_session(session_id: str) -> DeleteSessionResponse:
    '''Delete a session and clean up resources.'''
    success = database_session_service.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    return DeleteSessionResponse(success=True, session_id=session_id)
