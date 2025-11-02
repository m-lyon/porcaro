'''API router for session management endpoints.'''

import logging
from pathlib import Path

import anyio
from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import HTTPException
from fastapi import status

from porcaro.api.tasks import process_audio_task
from porcaro.api.utils import get_upload_filepath
from porcaro.api.models import ProcessingResponse
from porcaro.api.models import ProcessAudioRequest
from porcaro.api.models import DeleteSessionResponse
from porcaro.api.models import LabelingSessionResponse
from porcaro.api.models import SessionProgressResponse
from porcaro.api.services.database_service import database_session_service

logger = logging.getLogger('uvicorn')

router = APIRouter()


@router.post('/', operation_id='create_session', response_model=LabelingSessionResponse)
async def create_session(file: UploadFile):  # noqa: ANN201
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
        file_path = get_upload_filepath(session)

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


@router.get(
    '/{session_id}', operation_id='get_session', response_model=LabelingSessionResponse
)
async def get_session(session_id: str):  # noqa: ANN201
    '''Get session information by ID.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    return session


@router.get(
    '/', operation_id='get_sessions', response_model=list[LabelingSessionResponse]
)
async def get_sessions():  # noqa: ANN201
    '''List all existing labeling sessions.'''
    sessions = database_session_service.get_sessions()
    return sessions


@router.post('/{session_id}/process', operation_id='start_session_processing')
async def start_session_processing(
    session_id: str, request: ProcessAudioRequest
) -> ProcessingResponse:
    '''Start processing the uploaded audio file using Celery.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    file_path = get_upload_filepath(session)
    if not file_path.exists():
        logger.error(f'Audio file not found for session {session_id}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No audio file found for session',
        )

    # Start Celery task
    task = process_audio_task.delay(session_id, request.model_dump())

    logger.info(
        f'Started background processing for session {session_id}, task_id: {task.id}'
    )

    return ProcessingResponse(
        session_id=session_id,
        task_id=task.id,
        progress_percentage=0,
        current_state='PENDING',
        current_status='Task has been queued',
    )


@router.get(
    '/{session_id}/process/{task_id}/status', operation_id='get_processing_status'
)
async def get_processing_status(session_id: str, task_id: str) -> ProcessingResponse:
    '''Get the current processing status for a session task.'''
    task_result = process_audio_task.AsyncResult(task_id)
    # TODO: test what exception is raised when given invalid task_id

    # Initialize defaults
    progress_percentage = 0
    current_status = 'Unknown status'

    if task_result.status == 'PENDING':
        current_status = 'Task is waiting to be processed'
    elif task_result.status == 'PROGRESS':
        progress_percentage = task_result.info['current']
        current_status = task_result.info['status']
    elif task_result.status == 'SUCCESS':
        progress_percentage = 100
        current_status = (
            f"Completed! Processed {task_result.result['total_clips']} clips"
        )
    elif task_result.status == 'FAILURE':
        current_status = task_result.info['status']

    response = ProcessingResponse(
        session_id=session_id,
        task_id=task_id,
        progress_percentage=progress_percentage,
        current_state=task_result.status,
        current_status=current_status,
    )

    return response


@router.get('/{session_id}/progress', operation_id='get_session_progress')
async def get_session_progress(session_id: str) -> SessionProgressResponse:
    '''Get the labeling progress for a session.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    total_clips = database_session_service.count_total_clips(session_id)
    labeled_clips = database_session_service.count_labeled_clips(session_id)
    progress_percentage = (labeled_clips / total_clips * 100) if total_clips > 0 else 0

    return SessionProgressResponse(
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
