'''API router for labeling endpoints.'''

import logging
from datetime import UTC
from datetime import datetime

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status

from porcaro.api.models import LabelClipRequest
from porcaro.api.models import AudioClipResponse
from porcaro.api.models import LabeledClipsResponse
from porcaro.api.models import LabeledDataStatistics
from porcaro.api.models import AllLabledClipsResponse
from porcaro.api.models import RemoveClipLabelResponse
from porcaro.api.models import ExportLabeledDataResponse
from porcaro.api.services.database_service import database_session_service

logger = logging.getLogger('uvicorn')

router = APIRouter()


@router.post(
    '/{session_id}/clips/{clip_id}/label',
    operation_id='label_clip',
    response_model=AudioClipResponse,
)
async def label_clip(session_id: str, clip_id: str, request: LabelClipRequest):  # noqa: ANN201
    '''Submit a label for a specific clip.'''
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

    # Update clip with user label in database
    updated_clip = database_session_service.update_clip_label(
        session_id, clip_id, request.labels
    )

    if not updated_clip:
        logger.error(f'Failed to update label for clip {clip_id}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update clip label',
        )

    logger.info(f'Clip {clip_id} labeled with {request.labels}')
    return updated_clip


@router.delete('/{session_id}/clips/{clip_id}/label', operation_id='remove_clip_label')
async def remove_clip_label(session_id: str, clip_id: str) -> RemoveClipLabelResponse:
    '''Remove the user label from a specific clip.'''
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

    updated_clip = database_session_service.remove_clip_label(session_id, clip_id)

    if not updated_clip:
        logger.error(f'Failed to remove label for clip {clip_id}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to remove clip label',
        )

    logger.info(f'Removed label from clip {clip_id}')
    return RemoveClipLabelResponse(
        clip_id=clip_id, previous_labels=clip.user_label, success=True
    )


@router.get('/{session_id}/export', operation_id='export_labeled_data')
async def export_labeled_data(
    session_id: str, fmt: str = 'json'
) -> ExportLabeledDataResponse:
    '''Export all labeled data from a session.'''
    session = database_session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    # Get labeled clips from database
    total_clips = database_session_service.count_total_clips(session_id)
    labeled_clips = database_session_service.get_labeled_clips(session_id)

    if not labeled_clips:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No labeled clips found in session',
        )

    if session.time_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Session time signature is not set',
        )

    if fmt.lower() == 'json':
        # Export as JSON structure
        export_data = {
            'session_info': {
                'session_id': session_id,
                'filename': session.filename,
                'time_signature': {
                    'numerator': session.time_signature.numerator,
                    'denominator': session.time_signature.denominator,
                },
                'bpm': session.bpm,
                'total_clips': total_clips,
                'labeled_clips': len(labeled_clips),
                'created_at': session.created_at.isoformat(),
            },
            'clips': [
                {
                    'clip_id': clip.id,
                    'start_sample': clip.start_sample,
                    'start_time': clip.start_time,
                    'end_sample': clip.end_sample,
                    'end_time': clip.end_time,
                    'sample_rate': clip.sample_rate,
                    'peak_sample': clip.peak_sample,
                    'peak_time': clip.peak_time,
                    'predicted_labels': clip.predicted_labels,
                    'user_label': clip.user_label if clip.user_label else None,
                    'labeled_at': clip.labeled_at.isoformat()
                    if clip.labeled_at
                    else None,
                }
                for clip in labeled_clips
            ],
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Unsupported export format. Use "json" only.',
        )

    return ExportLabeledDataResponse(
        session_id=session_id,
        export_format=fmt,
        data=export_data,
        created_at=datetime.now(UTC),
    )


@router.get('/statistics', operation_id='get_labeled_data_statistics')
async def get_labeled_data_statistics() -> LabeledDataStatistics:
    '''Get statistics about all labeled data across all sessions.'''
    try:
        # Get all labeled clips from database
        all_clips = database_session_service.get_all_labeled_clips()

        # Calculate statistics
        total_labeled_clips = len(all_clips)
        clips_by_label = {}

        for clip in all_clips:
            if clip.user_label:
                for label in clip.user_label:
                    clips_by_label[label] = clips_by_label.get(label, 0) + 1

        return LabeledDataStatistics(
            total_labeled_clips=total_labeled_clips, clips_by_label=clips_by_label
        )
    except Exception as e:
        logger.exception('Error getting labeled data statistics')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get statistics',
        ) from e


@router.get(
    '/all_labeled_clips',
    operation_id='get_all_labeled_clips',
    response_model=AllLabledClipsResponse,
)
async def get_all_labeled_clips():  # noqa: ANN201
    '''Get all labeled clips from all sessions.'''
    clips = database_session_service.get_all_labeled_clips()
    return LabeledClipsResponse(clips=clips)
