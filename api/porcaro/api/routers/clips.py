'''API router for clip management endpoints.'''

import logging

from fastapi import Query
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import Response

from porcaro.api.models import AudioClip
from porcaro.api.models import ClipListResponse
from porcaro.api.services.audio_service import audio_clip_to_wav_bytes
from porcaro.api.services.audio_service import get_playback_audio_data
from porcaro.api.services.session_service import session_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/{session_id}/clips', response_model=ClipListResponse)
async def get_clips(
    session_id: str,
    page: int = Query(1, ge=1, description='Page number'),
    page_size: int = Query(20, ge=1, le=100, description='Number of clips per page'),
    labeled: bool | None = Query(None, description='Filter by labeled status'),
):
    '''Get a paginated list of clips for a session.'''
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    if not session.processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Session audio has not been processed yet',
        )

    session_data = session_store.get_session_data(session_id)
    if not session_data or 'clips' not in session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='No clips found for session'
        )

    clips = list(session_data['clips'].values())

    # Filter by labeled status if requested
    if labeled is not None:
        clips = [clip for clip in clips if (clip.user_label is not None) == labeled]

    # Sort by clip_id for consistent pagination
    clips.sort(key=lambda x: x.clip_id)

    # Pagination
    total = len(clips)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_clips = clips[start_idx:end_idx]

    return ClipListResponse(
        clips=page_clips,
        total=total,
        page=page,
        page_size=page_size,
        has_next=end_idx < total,
    )


@router.get('/{session_id}/clips/{clip_id}', response_model=AudioClip)
async def get_clip(session_id: str, clip_id: str):
    '''Get a specific clip by ID.'''
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    clip = session_store.get_clip(session_id, clip_id)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Clip not found'
        )

    return clip


@router.get('/{session_id}/clips/{clip_id}/audio')
async def get_clip_audio(session_id: str, clip_id: str):
    '''Stream the audio data for a specific clip as WAV.'''
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    clip = session_store.get_clip(session_id, clip_id)
    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Clip not found'
        )

    session_data = session_store.get_session_data(session_id)
    if not session_data or 'dataframe' not in session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Audio data not found for session',
        )

    try:
        # Extract clip index from clip_id (format: {session_id}_{index})
        clip_index = int(clip_id.split('_')[-1])

        # Get audio data from DataFrame
        df = session_data['dataframe']
        audio_data = get_playback_audio_data(df, clip_index)

        # Convert to WAV bytes
        wav_bytes = audio_clip_to_wav_bytes(audio_data, clip.sample_rate)

        return Response(
            content=wav_bytes,
            media_type='audio/wav',
            headers={
                'Content-Disposition': f'inline; filename="{clip_id}.wav"',
                'Cache-Control': 'no-cache',
            },
        )

    except (ValueError, IndexError) as e:
        logger.error(f'Error parsing clip ID {clip_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid clip ID format'
        ) from e
    except Exception as e:
        logger.error(f'Error streaming audio for clip {clip_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to stream audio',
        ) from e
