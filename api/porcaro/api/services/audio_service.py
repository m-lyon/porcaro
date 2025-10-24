'''Audio processing service using the existing porcaro transcription pipeline.'''

import io
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf

from porcaro.utils import TimeSignature
from porcaro.transcription import load_song_data
from porcaro.transcription import get_librosa_onsets_v1
from porcaro.transcription import run_prediction_on_track_v1
from porcaro.api.database.models import DrumLabel
from porcaro.api.database.models import TimeSignatureModel
from porcaro.api.database.models import ProcessingMetadataModel
from porcaro.models.annoteator.module import WEIGHTS_PATH

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
) -> tuple[np.ndarray, pd.DataFrame, float, ProcessingMetadataModel]:
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
    onsets = get_librosa_onsets_v1(track, song_data.sample_rate, song_data.bpm)

    # Run prediction
    pred_df = run_prediction_on_track_v1(track, onsets, song_data, resolution)

    # Prepare metadata
    bpm = song_data.bpm.bpm
    duration = song_data.duration

    metadata = ProcessingMetadataModel(
        processed=True,
        duration=duration,
        song_sample_rate=song_data.sample_rate,
        onset_algorithm=get_librosa_onsets_v1.__name__,
        prediction_algorithm=run_prediction_on_track_v1.__name__,
        model_weights_path=str(WEIGHTS_PATH),
    )

    logger.info(f'Processed {len(pred_df)} clips with BPM {song_data.bpm}')
    return track, pred_df, bpm, metadata


def audio_clip_to_wav_bytes(audio_data: np.ndarray, sample_rate: int | float) -> bytes:
    '''Convert numpy audio array to WAV bytes.'''
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, int(sample_rate), format='WAV')
    return buffer.getvalue()
