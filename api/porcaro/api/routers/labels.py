'''API router for labeling endpoints.'''

import logging
import datetime

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import JSONResponse

from porcaro.api.models import AudioClip
from porcaro.api.models import LabelClipRequest
from porcaro.api.models import ExportDataResponse
from porcaro.api.services.session_service import session_store
from porcaro.api.services.labeled_data_service import labeled_data_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/{session_id}/clips/{clip_id}/label', operation_id='label_clip')
async def label_clip(
    session_id: str, clip_id: str, request: LabelClipRequest
) -> AudioClip:
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

    session_data = session_store.get_session_data(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session data not found'
        )

    try:
        # Update clip with user label
        clip.user_label = request.labels
        clip.labeled_at = datetime.datetime.now(tz=datetime.UTC)

        # Update clip in session store
        session_data.clips[clip_id] = clip

        # Save labeled clip to disk immediately
        success = labeled_data_service.save_labeled_clip(session, clip, session_data)
        if not success:
            logger.warning(f'Failed to save labeled clip {clip_id} to disk')
            # Continue execution - we still return the updated clip even if disk save
            # failed

        logger.info(f'Clip {clip_id} labeled with {request.labels} and saved to disk')
        return clip
    except Exception as e:
        logger.exception(f'Error labeling clip {clip_id}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to save label',
        ) from e


@router.delete('/{session_id}/clips/{clip_id}/label', operation_id='remove_clip_label')
async def remove_clip_label(session_id: str, clip_id: str) -> JSONResponse:
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
        if session_data:
            session_data.clips[clip_id] = clip

        # Remove labeled clip from disk
        success = labeled_data_service.remove_labeled_clip(session_id, clip_id)
        if not success:
            logger.warning(f'Failed to remove labeled clip {clip_id} from disk')
            # Continue execution - we still return success even if disk removal failed

        logger.info(f'Removed label from clip {clip_id} and deleted from disk')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Label removed successfully'},
        )

    except Exception as e:
        logger.exception(f'Error removing label from clip {clip_id}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to remove label',
        ) from e


@router.get('/{session_id}/export', operation_id='export_labeled_data')
async def export_labeled_data(session_id: str, fmt: str = 'json') -> ExportDataResponse:
    '''Export all labeled data from a session.'''
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Session not found'
        )

    # Get labeled clips from persistent storage
    labeled_clips_metadata = labeled_data_service.get_labeled_clips_for_session(
        session_id
    )

    if not labeled_clips_metadata:
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
                'total_clips': session.total_clips,
                'labeled_clips': len(labeled_clips_metadata),
                'created_at': session.created_at.isoformat(),
            },
            'clips': [
                {
                    'clip_id': clip_meta['clip_id'],
                    'start_sample': clip_meta['clip_info']['start_sample'],
                    'start_time': clip_meta['clip_info']['start_time'],
                    'end_sample': clip_meta['clip_info']['end_sample'],
                    'end_time': clip_meta['clip_info']['end_time'],
                    'sample_rate': clip_meta['clip_info']['sample_rate'],
                    'peak_sample': clip_meta['clip_info']['peak_sample'],
                    'peak_time': clip_meta['clip_info']['peak_time'],
                    'predicted_labels': clip_meta['clip_info']['predicted_labels'],
                    'user_label': clip_meta['clip_info']['user_label'],
                    'labeled_at': clip_meta['clip_info']['labeled_at'],
                    'model_input_audio_file_path': '/'.join(
                        [
                            'labeled_data',
                            session_id,
                            clip_meta['clip_id'],
                            clip_meta['files']['model_input_audio_file'],
                        ]
                    ),
                }
                for clip_meta in labeled_clips_metadata
            ],
        }

    elif fmt.lower() == 'csv':
        # Export as CSV-compatible structure
        export_data = [
            {
                'clip_id': clip_meta['clip_id'],
                'start_sample': clip_meta['clip_info']['start_sample'],
                'start_time': clip_meta['clip_info']['start_time'],
                'end_sample': clip_meta['clip_info']['end_sample'],
                'end_time': clip_meta['clip_info']['end_time'],
                'peak_time': clip_meta['clip_info']['peak_time'],
                'predicted_labels': ','.join(
                    clip_meta['clip_info']['predicted_labels']
                ),
                'user_label': ','.join(clip_meta['clip_info']['user_label'])
                if clip_meta['clip_info']['user_label']
                else '',
                'labeled_at': clip_meta['clip_info']['labeled_at'],
                'model_input_audio_file_path': '/'.join(
                    [
                        'labeled_data',
                        session_id,
                        clip_meta['clip_id'],
                        clip_meta['files']['model_input_audio_file'],
                    ]
                ),
            }
            for clip_meta in labeled_clips_metadata
        ]

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Unsupported export format. Use "json" or "csv"',
        )

    return ExportDataResponse(
        session_id=session_id,
        export_format=fmt,
        data=export_data,
        created_at=datetime.datetime.now(tz=datetime.UTC),
    )


@router.get('/statistics', operation_id='get_labeled_data_statistics')
async def get_labeled_data_statistics() -> JSONResponse:
    '''Get statistics about all labeled data across all sessions.'''
    try:
        stats = labeled_data_service.get_statistics()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=stats,
        )
    except Exception as e:
        logger.exception('Error getting labeled data statistics')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get statistics',
        ) from e


@router.get('/all_labeled_clips', operation_id='get_all_labeled_clips')
async def get_all_labeled_clips() -> JSONResponse:
    '''Get all labeled clips from all sessions.'''
    try:
        clips = labeled_data_service.get_all_labeled_clips()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'clips': clips, 'total': len(clips)},
        )
    except Exception as e:
        logger.exception('Error getting all labeled clips')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get labeled clips',
        ) from e


@router.delete('/{session_id}/labeled_data', operation_id='remove_session_labeled_data')
async def remove_session_labeled_data(session_id: str) -> JSONResponse:
    '''Remove all labeled data for a specific session.'''
    try:
        success = labeled_data_service.remove_session(session_id)
    except Exception as e:
        logger.exception('Error cleaning up labeled data for session %s', session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to clean up labeled data',
        ) from e

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No labeled data found for session',
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': f'Labeled data for session {session_id} cleaned up successfully'
        },
    )
