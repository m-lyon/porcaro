'''API router for session management endpoints.'''

import logging
from pathlib import Path

import anyio
from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import JSONResponse

from porcaro.api.models import LabelingSession
from porcaro.api.models import SessionProgress
from porcaro.api.models import ProcessAudioRequest
from porcaro.api.services.audio_service import process_audio_file
from porcaro.api.services.audio_service import dataframe_to_audio_clips
from porcaro.api.services.session_service import session_store

logger = logging.getLogger(__name__)

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
        session = session_store.create_session(file.filename)
    except Exception as e:
        logger.exception('Error creating session from session store')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create session',
        ) from e

    # Save uploaded file to temporary directory
    session_data = session_store.get_session_data(session.session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create session data',
        )
    try:
        file_path = session_data.temp_dir / file.filename

        # Write uploaded file
        async with await anyio.open_file(file_path, 'wb') as buffer:
            content = await file.read()
            await buffer.write(content)

        # Store file path in session data
        session_store.update_session_data(session.session_id, {'file_path': file_path})

        logger.info(f'Created session {session.session_id} with file {file.filename}')
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
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    return session


@router.post('/{session_id}/process', operation_id='process_session_audio')
async def process_session_audio(
    session_id: str, request: ProcessAudioRequest
) -> JSONResponse:
    '''Process the uploaded audio file through the transcription pipeline.'''
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    session_data = session_store.get_session_data(session_id)
    if not session_data or session_data.file_path is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No audio file found for session',
        )

    try:
        logger.info(f'Processing audio for session {session_id}')

        # Process audio through porcaro pipeline
        track, df, metadata = process_audio_file(
            file_path=session_data.file_path,
            time_sig=request.time_signature,
            start_beat=request.start_beat,
            offset=request.offset,
            duration=request.duration,
            resolution=request.resolution,
        )

        # Convert DataFrame to AudioClip models
        clips = dataframe_to_audio_clips(df, session_id)

        # Store clips and data
        session_store.update_session_data(
            session_id,
            {
                'clips': {clip.clip_id: clip for clip in clips},
                'dataframe': df,
                'audio_track': track,
                'metadata': metadata,
            },
        )

        # Update session with processing results
        session_store.update_session(
            session_id,
            {
                'time_signature': request.time_signature,
                'start_beat': request.start_beat,
                'offset': request.offset,
                'duration': request.duration,
                'resolution': request.resolution,
                'bpm': metadata.bpm,
                'total_clips': metadata.total_clips,
                'processed': True,
            },
        )

        logger.info(f'Processing complete for session {session_id}: {len(clips)} clips')

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'message': 'Audio processing completed',
                'total_clips': len(clips),
                'bpm': metadata.bpm,
                'duration': metadata.duration,
            },
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
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    # Count labeled clips
    session_data = session_store.get_session_data(session_id)
    labeled_count = 0

    if session_data:
        labeled_count = sum(
            1 for clip in session_data.clips.values() if clip.user_label is not None
        )

    # Update session with current count
    session_store.update_session(session_id, {'labeled_clips': labeled_count})

    total_clips = session.total_clips
    progress_percentage = (labeled_count / total_clips * 100) if total_clips > 0 else 0

    return SessionProgress(
        session_id=session_id,
        total_clips=total_clips,
        labeled_clips=labeled_count,
        progress_percentage=round(progress_percentage, 2),
        remaining_clips=total_clips - labeled_count,
    )


@router.delete('/{session_id}', operation_id='delete_session')
async def delete_session(session_id: str) -> JSONResponse:
    '''Delete a session and clean up resources.'''
    success = session_store.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'message': 'Session deleted successfully'},
    )


@router.get('/', operation_id='list_sessions')
async def list_sessions() -> list[LabelingSession]:
    '''List all active sessions.'''
    sessions = session_store.list_sessions()
    return list(sessions.values())
