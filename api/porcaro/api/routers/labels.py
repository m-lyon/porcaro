'''API router for labeling endpoints.'''

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from models import LabelClipRequest, AudioClip, ExportDataResponse
from porcaro.api.services.session_service import session_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/{session_id}/clips/{clip_id}/label', response_model=AudioClip)
async def label_clip(session_id: str, clip_id: str, request: LabelClipRequest):
    '''Submit a label for a specific clip.'''
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

    try:
        # Update clip with user label
        clip.user_label = request.labels
        clip.labeled_at = datetime.now()

        # Update clip in session store
        session_data = session_store.get_session_data(session_id)
        if session_data and 'clips' in session_data:
            session_data['clips'][clip_id] = clip

        logger.info(f'Clip {clip_id} labeled with {request.labels}')
        return clip

    except Exception as e:
        logger.error(f'Error labeling clip {clip_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to save label',
        )


@router.delete('/{session_id}/clips/{clip_id}/label')
async def remove_clip_label(session_id: str, clip_id: str):
    '''Remove the user label from a specific clip.'''
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

    try:
        # Remove user label
        clip.user_label = None
        clip.labeled_at = None

        # Update clip in session store
        session_data = session_store.get_session_data(session_id)
        if session_data and 'clips' in session_data:
            session_data['clips'][clip_id] = clip

        logger.info(f'Removed label from clip {clip_id}')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Label removed successfully'},
        )

    except Exception as e:
        logger.error(f'Error removing label from clip {clip_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to remove label',
        )


@router.get('/{session_id}/export', response_model=ExportDataResponse)
async def export_labeled_data(session_id: str, format: str = 'json'):
    '''Export all labeled data from a session.'''
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    session_data = session_store.get_session_data(session_id)
    if not session_data or 'clips' not in session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='No clips found for session'
        )

    # Get only labeled clips
    clips = session_data['clips']
    labeled_clips = [clip for clip in clips.values() if clip.user_label is not None]

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

    try:
        if format.lower() == 'json':
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
                    'total_clips': session.total_clips,
                    'labeled_clips': len(labeled_clips),
                    'created_at': session.created_at.isoformat(),
                },
                'clips': [
                    {
                        'clip_id': clip.clip_id,
                        'sample_start': clip.sample_start,
                        'sample_end': clip.sample_end,
                        'sample_rate': clip.sample_rate,
                        'peak_sample': clip.peak_sample,
                        'peak_time': clip.peak_time,
                        'predicted_labels': [
                            label.value for label in clip.predicted_labels
                        ],
                        'user_label': [label.value for label in clip.user_label]
                        if clip.user_label
                        else None,
                        'labeled_at': clip.labeled_at.isoformat()
                        if clip.labeled_at
                        else None,
                    }
                    for clip in labeled_clips
                ],
            }

        elif format.lower() == 'csv':
            # Export as CSV-compatible structure
            export_data = [
                {
                    'clip_id': clip.clip_id,
                    'sample_start': clip.sample_start,
                    'sample_end': clip.sample_end,
                    'peak_time': clip.peak_time,
                    'predicted_labels': ','.join(
                        [label.value for label in clip.predicted_labels]
                    ),
                    'user_label': ','.join([label.value for label in clip.user_label])
                    if clip.user_label
                    else '',
                    'labeled_at': clip.labeled_at.isoformat()
                    if clip.labeled_at
                    else None,
                }
                for clip in labeled_clips
            ]

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Unsupported export format. Use "json" or "csv"',
            )

        return ExportDataResponse(
            session_id=session_id,
            export_format=format,
            data=export_data,
            created_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f'Error exporting data for session {session_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to export data',
        )
