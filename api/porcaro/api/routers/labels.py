'''API router for labeling endpoints.'''

import logging
from datetime import datetime

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
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='Session data not found'
            )

        if 'clips' in session_data:
            session_data['clips'][clip_id] = clip

        # Save labeled clip to disk immediately
        success = labeled_data_service.save_labeled_clip(session, clip, session_data)
        if not success:
            logger.warning(f'Failed to save labeled clip {clip_id} to disk')
            # Continue execution - we still return the updated clip even if disk save
            # failed

        logger.info(f'Clip {clip_id} labeled with {request.labels} and saved to disk')
        return clip

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f'Error labeling clip {clip_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to save label',
        ) from e


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
        logger.error(f'Error removing label from clip {clip_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to remove label',
        ) from e


@router.get('/{session_id}/export', response_model=ExportDataResponse)
async def export_labeled_data(session_id: str, format: str = 'json'):
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

        elif format.lower() == 'csv':
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
            export_format=format,
            data=export_data,
            created_at=datetime.now(),
        )

    except Exception as e:
        logger.error(f'Error exporting data for session {session_id}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to export data',
        ) from e


@router.get('/statistics')
async def get_labeled_data_statistics():
    '''Get statistics about all labeled data across all sessions.'''
    try:
        stats = labeled_data_service.get_statistics()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=stats,
        )
    except Exception as e:
        logger.error(f'Error getting labeled data statistics: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get statistics',
        ) from e


@router.get('/all_labeled_clips')
async def get_all_labeled_clips():
    '''Get all labeled clips from all sessions.'''
    try:
        clips = labeled_data_service.get_all_labeled_clips()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'clips': clips, 'total': len(clips)},
        )
    except Exception as e:
        logger.error(f'Error getting all labeled clips: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get labeled clips',
        ) from e


@router.delete('/{session_id}/labeled_data')
async def remove_session_labeled_data(session_id: str):
    '''Remove all labeled data for a specific session.'''
    try:
        success = labeled_data_service.remove_session(session_id)
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    'message': f'Labeled data for session {session_id} '
                    'cleaned up successfully'
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to clean up labeled data',
            )
    except Exception as e:
        logger.error(
            f'Error cleaning up labeled data for session {session_id}: {str(e)}'
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to clean up labeled data',
        ) from e
