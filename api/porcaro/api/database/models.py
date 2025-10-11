'''SQLModel database models for the data labeling API.'''

import uuid
from enum import Enum
from typing import Any
from datetime import UTC
from datetime import datetime

from sqlmodel import JSON
from sqlmodel import ARRAY
from sqlmodel import Enum as SqlEnum
from sqlmodel import Field
from sqlmodel import Column
from sqlmodel import SQLModel
from sqlmodel import Relationship
from sqlmodel import UniqueConstraint


class DrumLabel(str, Enum):
    '''Enum for drum labels used in the model.'''

    KICK_DRUM = 'KD'
    SNARE_DRUM = 'SD'
    SNARE_DRUM_XSTICK = 'SDX'
    HI_HAT = 'HH'
    HI_HAT_OPEN = 'HHO'
    HI_HAT_CLOSED = 'HHC'
    RIDE_CYMBAL = 'RC'
    TOM_TOM = 'TT'
    FLOOR_TOM = 'TTF'
    MID_TOM = 'TTM'
    HIGH_TOM = 'TTH'
    CRASH_CYMBAL = 'CC'


class TimeSignatureModel(SQLModel):
    '''Time signature model.'''

    numerator: int = Field(..., ge=1, description='Numerator of time signature')
    denominator: int = Field(..., ge=1, description='Denominator of time signature')


class TimeSignature(TimeSignatureModel, table=True):
    '''Time signature database model.'''

    __table_args__ = (UniqueConstraint('numerator', 'denominator'),)

    id: str = Field(default=None, primary_key=True)

    def __init__(self, **data: Any):
        '''Custom initializer to set ID based on numerator and denominator.'''
        super().__init__(**data)
        if not self.id:  # if not supplied, generate it
            self.id = f'{self.numerator}-{self.denominator}'


class ProcessingMetadataModel(SQLModel):
    '''Processing metadata model.'''

    processed: bool = Field(..., description='Whether processing is complete')
    duration: float = Field(..., description='Duration of the audio in seconds')
    song_sample_rate: float = Field(
        ...,
        description='Sample rate of the original audio, '
        'this can differ from audio clip sample rates due to preprocessing',
    )
    onset_algorithm: str = Field(..., description='Onset detection algorithm used')
    prediction_algorithm: str = Field(..., description='Prediction algorithm used')
    model_weights_path: str = Field(..., description='Path to the model weights used')


class ProcessingMetadata(ProcessingMetadataModel, table=True):
    '''Processing metadata database model.'''

    id: str = Field(
        primary_key=True,
        foreign_key='labelingsession.id',
        unique=True,
        description='Session this metadata belongs to',
    )

    # Relationships
    session: 'LabelingSession' = Relationship(back_populates='processing_metadata')


class AudioClip(SQLModel, table=True):
    '''Audio clip database model.'''

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description='Unique clip identifier',
    )
    start_sample: int = Field(description='Start sample in the original audio')
    start_time: float = Field(description='Start time in seconds')
    end_sample: int = Field(description='End sample in the original audio')
    end_time: float = Field(description='End time in seconds')
    sample_rate: int = Field(description='Sample rate of the audio')
    peak_sample: int = Field(description='Sample where the peak occurs')
    peak_time: float = Field(description='Time in seconds where the peak occurs')
    predicted_labels: list[DrumLabel] = Field(
        sa_column=Column(ARRAY(SqlEnum(DrumLabel))),
        description='ML model predictions',
    )
    user_label: list[DrumLabel] | None = Field(
        sa_column=Column(ARRAY(SqlEnum(DrumLabel))),
        default=None,
        description='User-assigned label',
    )
    confidence_scores: dict | None = Field(
        sa_column=Column(JSON),
        default=None,  # saved as 'null' in the DB if not set
        description='Model confidence scores',
    )
    labeled_at: datetime | None = Field(
        default=None, description='When the clip was labeled'
    )
    audio_file_path: str | None = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description='Path to the stored audio file',
    )

    # Foreign keys
    session_id: str = Field(
        foreign_key='labelingsession.id', description='Session this clip belongs to'
    )

    # Relationships
    session: 'LabelingSession' = Relationship(back_populates='clips')


class LabelingSession(SQLModel, table=True):
    '''Labeling session database model.'''

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description='Unique session identifier',
    )
    filename: str = Field(description='Original audio filename')
    start_beat: float = Field(default=1, description='Starting beat offset')
    offset: float = Field(default=0.0, description='Offset in seconds')
    duration: float | None = Field(
        default=None, description='Duration to process in seconds'
    )
    resolution: int | None = Field(default=16, description='Window size resolution')
    bpm: float | None = Field(default=None, description='Detected BPM')
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description='Session creation time',
    )

    # Foreign keys
    time_signature_id: str | None = Field(
        default=None,
        foreign_key='timesignature.id',
        description='Time signature ID',
    )

    # Relationships
    time_signature: TimeSignature | None = Relationship(
        sa_relationship_kwargs={'lazy': 'selectin'}
    )
    clips: list['AudioClip'] = Relationship(
        back_populates='session', cascade_delete=True
    )
    processing_metadata: ProcessingMetadata | None = Relationship(
        back_populates='session',
        cascade_delete=True,
        sa_relationship_kwargs={'lazy': 'selectin'},
    )
