'''Audio processing service using the existing porcaro transcription pipeline.'''

import io
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf

from porcaro.utils import TimeSignature
from porcaro.extraction import extract_drum_track_v1
from porcaro.transcription import load_song_data
from porcaro.transcription import get_librosa_onsets_v1
from porcaro.transcription import run_prediction_on_track_v1
from porcaro.api.database.models import DrumLabel
from porcaro.api.database.models import TimeSignatureModel
from porcaro.api.database.models import SessionMetadataModel
from porcaro.models.annoteator.module import WEIGHTS_PATH

logger = logging.getLogger('uvicorn')

LABEL_MAPPING = {label.value: label for label in DrumLabel}


def convert_time_signature(ts_model: TimeSignatureModel) -> TimeSignature:
    '''Convert API time signature model to porcaro TimeSignature.'''
    return TimeSignature(ts_model.numerator, ts_model.denominator)


def create_drum_isolated_track(
    file_path: Path,
    output_path: Path | None = None,
    device: str = 'cpu',
    offset: float = 0.0,
    duration: float | None = None,
) -> tuple[np.ndarray, int]:
    '''Create a drum-isolated audio track from the input file.

    Args:
        file_path (Path): Path to the audio file.
        output_path (Path | None): Path to save the drum-isolated track. If None,
            the track is not saved to disk. Default is None.
        device (str): Device to use for processing. Default is "cpu".
        offset (float): Offset in seconds to start reading the audio file.
        duration (float | None): Duration in seconds to read from the audio file.
            If None, reads until the end of the file.

    Returns:
        tuple[np.ndarray, int]: A tuple containing the drum-isolated audio data
            as a numpy array and the sample rate.
    '''
    logger.info(f'Creating drum-isolated track from file: {file_path}')

    track, sample_rate = extract_drum_track_v1(
        fpath=file_path,
        device=device,
        progress_bar=False,
        offset=offset,
        duration=duration,
    )

    if output_path:
        sf.write(output_path, track.T, sample_rate)
        logger.info(f'Drum-isolated track saved to: {output_path}')

    return track, sample_rate


def predict_from_drum_track(
    file_path: Path,
    time_sig: TimeSignatureModel,
    start_beat: float = 1,
    offset: float = 0.0,
    duration: float | None = None,
    resolution: int = 16,
) -> tuple[np.ndarray, pd.DataFrame, float, SessionMetadataModel]:
    '''Process audio file through the porcaro transcription pipeline.

    Args:
        file_path (Path): Path to the audio file.
        time_sig (TimeSignatureModel): Time signature model.
        start_beat (float): The beat to start the transcription from.
            Use 1 for the first beat, and decimal values for sub-beats relative to the
            time signature. Default is 1 (first quarter note).
        offset (float): Offset in seconds to start reading the audio file.
        duration (float | None): Duration in seconds to read from the audio file.
            If None, reads until the end of the file.
        resolution (int): Window size resolution. Integer value
            represents the size in terms of note duration. Must be one of 4, 8, 16, or
            32. Default is 16 (sixteenth note).

    Returns:
        tuple[np.ndarray, pd.DataFrame, float, SessionMetadataModel]: A tuple
            containing the audio data as a numpy array, a DataFrame with predicted
            drum hits, the estimated BPM, and processing metadata.
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

    metadata = SessionMetadataModel(
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
