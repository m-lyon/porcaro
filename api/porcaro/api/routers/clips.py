'''API router for clip management endpoints.'''

import logging
from typing import Annotated

from fastapi import Query
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import Response

from porcaro.api.models import AudioClipList
from porcaro.api.models import AudioClipResponse
from porcaro.api.models import AudioClipListResponse
from porcaro.processing.window import get_windowed_sample
from porcaro.api.services.audio_service import audio_clip_to_wav_bytes
from porcaro.api.services.memory_service import in_memory_service
from porcaro.api.services.database_service import database_session_service

logger = logging.getLogger('uvicorn')

router = APIRouter()


@router.get(
    '/{session_id}/clips',
    operation_id='get_clips',
    response_model=AudioClipListResponse,
)
async def get_clips(  # noqa: ANN201
    session_id: str,
    page: Annotated[int, Query(ge=1, description='Page number')] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description='Number of clips per page')
    ] = 20,
    labeled: Annotated[
        bool | None, Query(description='Filter by labeled status')
    ] = None,
):
    '''Get a paginated list of clips for a session.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    if not session.processing_metadata or not session.processing_metadata.processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Session audio has not been processed yet',
        )

    # Get clips from database with pagination
    clips, total = database_session_service.get_clips(session_id, page, page_size)

    # Filter by labeled status if requested
    if labeled is not None:
        clips = [clip for clip in clips if (clip.user_label is not None) == labeled]
        total = len(clips)  # Update total after filtering

    logger.info(f'Returning {len(clips)} clips for session {session_id}')

    return AudioClipList(
        clips=clips,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
    )


@router.get(
    '/{session_id}/clips/{clip_id}',
    operation_id='get_clip',
    response_model=AudioClipResponse,
)
async def get_clip(session_id: str, clip_id: str):  # noqa: ANN201
    '''Get a specific clip by ID.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    clip = database_session_service.get_clip(session_id, clip_id)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Clip not found'
        )

    return clip


@router.get('/{session_id}/clips/{clip_id}/audio', operation_id='get_clip_audio')
async def get_clip_audio(
    session_id: str, clip_id: str, playback_window: float = 1.0
) -> Response:
    '''Stream the audio data for a specific clip as WAV.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )
    if not session.processing_metadata:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Session processing metadata is missing',
        )

    clip = database_session_service.get_clip(session_id, clip_id)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Clip not found'
        )

    track = in_memory_service.get_session_track(session_id)
    sample_rate = session.processing_metadata.song_sample_rate

    # Get audio data from DataFrame
    audio_data = get_windowed_sample(
        track=track,
        sample_rate=sample_rate,
        peak_time=clip.peak_time,
        window_size=playback_window,
    )

    # Convert to WAV bytes
    wav_bytes = audio_clip_to_wav_bytes(audio_data, sample_rate)

    return Response(
        content=wav_bytes,
        media_type='audio/wav',
        headers={
            'Content-Disposition': f'inline; filename="{clip_id}.wav"',
            'Cache-Control': 'no-cache',
        },
    )
