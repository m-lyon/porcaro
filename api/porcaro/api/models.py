'''Pydantic models for the data labeling API.'''

from enum import Enum
from typing import Any
from datetime import datetime
from collections.abc import Sequence

from pydantic import Field
from pydantic import BaseModel

from porcaro.api.database.models import AudioClip
from porcaro.api.database.models import DrumLabel
from porcaro.api.database.models import AudioClipList
from porcaro.api.database.models import AudioClipModel
from porcaro.api.database.models import TimeSignatureModel
from porcaro.api.database.models import LabelingSessionModel
from porcaro.api.database.models import SessionMetadataModel


class TimeSignatureResponse(TimeSignatureModel):
    '''Time signature response model.'''


class SessionMetadataResponse(SessionMetadataModel):
    '''Session metadata response model.'''


class ProcessingResponse(BaseModel):
    '''Processing metadata response model.'''

    session_id: str = Field(..., description='Unique session identifier')
    task_id: str = Field(..., description='Celery task identifier')
    progress_percentage: int = Field(..., description='Processing progress percentage')
    current_state: str = Field(..., description='Current processing state')
    current_status: str = Field(..., description='Current processing status')


class LabelingSessionResponse(LabelingSessionModel):
    '''Labeling session response model.'''

    id: str = Field(..., description='Unique session identifier')

    time_signature: TimeSignatureResponse | None = Field(
        default=None, description='Time signature information'
    )
    session_metadata: SessionMetadataResponse | None = Field(
        default=None, description='Session metadata information'
    )


class DeviceEnum(str, Enum):
    '''Enumeration of supported processing devices.'''

    CPU = 'cpu'
    GPU = 'cuda'


class ProcessAudioRequest(BaseModel):
    '''Request model for processing audio.'''

    time_signature: TimeSignatureModel = Field(..., description='Time signature')
    start_beat: float = Field(default=1, ge=0, description='Starting beat offset')
    offset: float = Field(default=0.0, ge=0, description='Offset in seconds')
    duration: float | None = Field(
        default=None, gt=0, description='Duration to process'
    )
    resolution: int = Field(default=16, description='Window size resolution')
    device: DeviceEnum = Field(default=DeviceEnum.CPU, description='Processing device')


class LabelClipRequest(BaseModel):
    '''Request model for labeling a clip.'''

    labels: list[DrumLabel] = Field(..., description='User-assigned labels')


class AudioClipResponse(AudioClipModel):
    '''Audio clip response model.'''

    id: str = Field(..., description='Unique clip identifier')


class AudioClipListResponse(AudioClipList):
    '''Response model for listing clips.'''

    clips: Sequence[AudioClipResponse] = Field(..., description='List of audio clips')


class RemoveClipLabelResponse(BaseModel):
    '''Response model for removing a clip label.'''

    clip_id: str = Field(..., description='ID of the clip')
    previous_labels: list[DrumLabel] | None = Field(
        ..., description='Labels before removal'
    )
    success: bool = Field(..., description='Whether the label removal was successful')


class LabeledDataStatistics(BaseModel):
    '''Statistics about labeled data in a session.'''

    total_labeled_clips: int = Field(..., description='Total number of labeled clips')
    clips_by_label: dict[DrumLabel, int] = Field(
        ..., description='Number of clips per label'
    )


class LabeledClipsResponse(BaseModel):
    '''Response model for all labeled clips in a session.'''

    clips: list[AudioClip] = Field(..., description='List of labeled clips')


class AllLabledClipsResponse(BaseModel):
    '''Response model for all labeled clips in a session.'''

    clips: list[AudioClipResponse] = Field(..., description='List of labeled clips')


class SessionProgressResponse(BaseModel):
    '''Response model for session progress.'''

    session_id: str
    total_clips: int
    labeled_clips: int
    progress_percentage: float = Field(..., description='Percentage of clips labeled')
    remaining_clips: int = Field(..., description='Number of unlabeled clips')


class ExportLabeledDataResponse(BaseModel):
    '''Response model for data export.'''

    session_id: str
    export_format: str
    data: Any = Field(..., description='Exported data')
    created_at: datetime


class ProcessAudioSessionResponse(BaseModel):
    '''Response model for processing audio session.'''

    total_clips: int = Field(..., description='Total number of clips generated')
    bpm: float = Field(..., description='Beats per minute of the audio')
    duration: float = Field(..., description='Duration of the audio in seconds')


class DeleteSessionResponse(BaseModel):
    '''Response model for deleting a session.'''

    success: bool = Field(
        ..., description='Whether the session was successfully deleted'
    )
    session_id: str = Field(..., description='ID of the deleted session')
