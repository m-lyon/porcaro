'''Pydantic models for the data labeling API.'''

from typing import List, Dict, Any
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class DrumLabel(str, Enum):
    '''Enum for drum labels used in the model.'''

    KICK_DRUM = 'KD'
    SNARE_DRUM = 'SD'
    HI_HAT = 'HH'
    RIDE_CYMBAL = 'RC'
    TOM_TOM = 'TT'
    CRASH_CYMBAL = 'CC'


class TimeSignatureModel(BaseModel):
    '''Time signature model.'''

    numerator: int = Field(..., ge=1, description='Numerator of time signature')
    denominator: int = Field(..., ge=1, description='Denominator of time signature')


class AudioClip(BaseModel):
    '''Model for an audio clip to be labeled.'''

    clip_id: str = Field(..., description='Unique identifier for the clip')
    sample_start: int = Field(..., description='Start sample in the original audio')
    sample_end: int = Field(..., description='End sample in the original audio')
    sample_rate: int = Field(..., description='Sample rate of the audio')
    peak_sample: int = Field(..., description='Sample where the peak occurs')
    peak_time: float = Field(..., description='Time in seconds where the peak occurs')
    predicted_labels: List[DrumLabel] = Field(
        default=[], description='ML model predictions'
    )
    user_label: List[DrumLabel] | None = Field(
        default=None, description='User-assigned label'
    )
    confidence_scores: Dict[str, float] | None = Field(
        default=None, description='Model confidence scores'
    )
    labeled_at: datetime | None = Field(
        default=None, description='When the clip was labeled'
    )

    class Config:
        use_enum_values = True


class LabelingSession(BaseModel):
    '''Model for a labeling session.'''

    session_id: str = Field(..., description='Unique session identifier')
    filename: str = Field(..., description='Original audio filename')
    time_signature: TimeSignatureModel | None = Field(
        default=None, description='Time signature of the audio'
    )
    start_beat: float = Field(default=1, description='Starting beat offset')
    offset: float = Field(default=0.0, description='Offset in seconds')
    duration: float | None = Field(
        default=None, description='Duration to process in seconds'
    )
    resolution: int | None = Field(default=16, description='Window size resolution')
    bpm: float | None = Field(default=None, description='Detected BPM')
    total_clips: int = Field(default=0, description='Total number of clips')
    labeled_clips: int = Field(default=0, description='Number of labeled clips')
    created_at: datetime = Field(
        default_factory=datetime.now, description='Session creation time'
    )
    processed: bool = Field(
        default=False, description='Whether audio processing is complete'
    )


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

    labels: List[DrumLabel] = Field(..., description='User-assigned labels')


class ClipListResponse(BaseModel):
    '''Response model for listing clips.'''

    clips: List[AudioClip]
    total: int = Field(..., description='Total number of clips')
    page: int = Field(..., description='Current page')
    page_size: int = Field(..., description='Page size')
    has_next: bool = Field(..., description='Whether there are more pages')


class SessionProgressResponse(BaseModel):
    '''Response model for session progress.'''

    session_id: str
    total_clips: int
    labeled_clips: int
    progress_percentage: float = Field(..., description='Percentage of clips labeled')
    remaining_clips: int = Field(..., description='Number of unlabeled clips')


class ExportDataResponse(BaseModel):
    '''Response model for data export.'''

    session_id: str
    export_format: str
    data: Any = Field(..., description='Exported data')
    created_at: datetime
