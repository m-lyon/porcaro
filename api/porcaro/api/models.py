'''Pydantic models for the data labeling API.'''

from typing import Any
from datetime import datetime
from collections.abc import Sequence

from pydantic import Field
from pydantic import BaseModel

from porcaro.api.database.models import AudioClip
from porcaro.api.database.models import DrumLabel
from porcaro.api.database.models import TimeSignatureModel


class ProcessAudioRequest(BaseModel):
    '''Request model for processing audio.'''

    time_signature: TimeSignatureModel = Field(..., description='Time signature')
    start_beat: float = Field(default=1, ge=0, description='Starting beat offset')
    offset: float = Field(default=0.0, ge=0, description='Offset in seconds')
    duration: float | None = Field(
        default=None, gt=0, description='Duration to process'
    )
    resolution: int = Field(default=16, description='Window size resolution')


class LabelClipRequest(BaseModel):
    '''Request model for labeling a clip.'''

    labels: list[DrumLabel] = Field(..., description='User-assigned labels')


class ClipListResponse(BaseModel):
    '''Response model for listing clips.'''

    clips: Sequence[AudioClip]
    total: int = Field(..., description='Total number of clips')
    page: int = Field(..., description='Current page')
    page_size: int = Field(..., description='Page size')
    has_next: bool = Field(..., description='Whether there are more pages')


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


class AllLabledClips(BaseModel):
    '''Response model for all labeled clips in a session.'''

    clips: list[AudioClip] = Field(..., description='List of labeled clips')


class SessionProgress(BaseModel):
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
