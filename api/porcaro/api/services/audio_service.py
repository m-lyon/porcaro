'''Audio processing service using the existing porcaro transcription pipeline.'''

import io
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf

from porcaro.utils import TimeSignature
from porcaro.api.models import AudioClip
from porcaro.api.models import DrumLabel
from porcaro.api.models import SessionMetadata
from porcaro.api.models import TimeSignatureModel
from porcaro.transcription import load_song_data
from porcaro.transcription import get_librosa_onsets
from porcaro.transcription import run_prediction_on_track
from porcaro.processing.window import get_windowed_sample

logger = logging.getLogger(__name__)

LABEL_MAPPING = {label.value: label for label in DrumLabel}
BPM_THRESHOLD = 110  # BPM threshold for onset detection hop length


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
) -> tuple[np.ndarray, pd.DataFrame, SessionMetadata]:
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
        track,
        song_data.sample_rate,
        hop_length=1024 if song_data.bpm < BPM_THRESHOLD else 512,
    )

    # Run prediction
    pred_df = run_prediction_on_track(track, onsets, song_data, resolution)

    # Prepare metadata
    metadata = SessionMetadata(
        bpm=song_data.bpm.bpm,
        sample_rate=song_data.sample_rate,
        duration=song_data.duration,
        total_clips=len(pred_df),
    )

    logger.info(f'Processed {len(pred_df)} clips with BPM {song_data.bpm}')
    return track, pred_df, metadata


def dataframe_to_audio_clips(df: pd.DataFrame, session_id: str) -> list[AudioClip]:
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
            start_sample=int(row['start_sample']),
            start_time=float(row['start_time']),
            end_sample=int(row['end_sample']),
            end_time=float(row['end_time']),
            sample_rate=int(row['sampling_rate']),
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


def get_model_input_audio_data(df: pd.DataFrame, clip_index: int) -> np.ndarray:
    '''Extract audio data for a specific clip from the DataFrame.'''
    if clip_index >= len(df):
        raise IndexError(f'Clip index {clip_index} out of range.')

    row = df.iloc[clip_index]
    return row['audio_clip']


def get_playback_audio_data(
    track: np.ndarray,
    sample_rate: int | float,
    df: pd.DataFrame,
    clip_index: int,
    playback_window: float = 1.0,
) -> np.ndarray:
    '''Extract audio data for a specific clip with padding from the DataFrame.'''
    if clip_index >= len(df):
        raise IndexError(f'Clip index {clip_index} out of range.')
    row = df.iloc[clip_index]
    peak_time = row['peak_time']

    # Extract audio data with padding
    return get_windowed_sample(track, sample_rate, peak_time, playback_window)
