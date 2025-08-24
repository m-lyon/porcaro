'''Audio processing service using the existing porcaro transcription pipeline.'''

import logging
import soundfile as sf
from pathlib import Path
from typing import List, Tuple
import io

import numpy as np
import pandas as pd

from porcaro.transcription import (
    load_song_data,
    get_librosa_onsets,
    run_prediction_on_track,
)
from porcaro.utils import TimeSignature
from porcaro.api.models import AudioClip, DrumLabel, TimeSignatureModel

logger = logging.getLogger(__name__)

LABEL_MAPPING = {label.value: label for label in DrumLabel}


def convert_time_signature(ts_model: TimeSignatureModel) -> TimeSignature:
    '''Convert API time signature model to porcaro TimeSignature.'''
    return TimeSignature(ts_model.numerator, ts_model.denominator)


def process_audio_file(
    file_path: Path,
    time_sig: TimeSignatureModel,
    start_beat: float = 1,
    offset: float = 0.0,
    duration: float | None = None,
    resolution: int = 16,
) -> Tuple[np.ndarray, pd.DataFrame, dict]:
    '''Process audio file through the porcaro transcription pipeline.

    Returns:
        Tuple of (audio_track, prediction_dataframe, song_metadata)
    '''
    logger.info(f'Processing audio file: {file_path}')

    # Convert to porcaro TimeSignature
    porcaro_time_sig = convert_time_signature(time_sig)

    # Load song data
    track, song_data = load_song_data(
        fpath=file_path,
        time_sig=porcaro_time_sig,
        start_beat=start_beat,
        offset=offset,
        duration=duration,
    )

    # Get onsets
    onsets = get_librosa_onsets(
        track, song_data.sample_rate, hop_length=1024 if song_data.bpm < 110 else 512
    )

    # Run prediction
    df = run_prediction_on_track(track, onsets, song_data, resolution)

    # Prepare metadata
    metadata = {
        'bpm': song_data.bpm.bpm,  # Access the underlying float value
        'sample_rate': int(song_data.sample_rate),
        'duration': song_data.duration,
        'total_clips': len(df),
    }

    logger.info(f'Processed {len(df)} clips with BPM {song_data.bpm}')
    return track, df, metadata


def dataframe_to_audio_clips(df: pd.DataFrame, session_id: str) -> List[AudioClip]:
    '''Convert prediction DataFrame to AudioClip models.'''
    clips = []

    for idx, row in df.iterrows():
        clip_id = f'{session_id}_{idx}'

        # Convert model predictions to our enum labels
        predicted_labels = []
        if 'hits' in row and isinstance(row['hits'], list):
            predicted_labels = [
                LABEL_MAPPING[label] for label in row['hits'] if label in LABEL_MAPPING
            ]

        clip = AudioClip(
            clip_id=clip_id,
            sample_start=int(row['sample_start']),
            sample_end=int(row['sample_end']),
            sample_rate=int(
                row['sampling_rate']
            ),  # Note: column is 'sampling_rate' not 'sample_rate'
            peak_sample=int(row['peak_sample']),
            peak_time=float(row['peak_time']),
            predicted_labels=predicted_labels,
        )

        clips.append(clip)

    return clips


def audio_clip_to_wav_bytes(audio_data: np.ndarray, sample_rate: int | float) -> bytes:
    '''Convert numpy audio array to WAV bytes.'''
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    return buffer.getvalue()


def get_clip_audio_data(df: pd.DataFrame, clip_index: int) -> np.ndarray:
    '''Extract audio data for a specific clip from the DataFrame.'''
    if clip_index >= len(df):
        raise IndexError(f'Clip index {clip_index} out of range.')

    row = df.iloc[clip_index]
    return row['audio_clip']
