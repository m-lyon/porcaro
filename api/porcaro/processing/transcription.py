'''Module for transcribing drum audio files into a structured format.'''

import logging
from pathlib import Path

import librosa

from porcaro.utils import SongData
from porcaro.utils import TimeSignature
from porcaro.utils.bpm import BPM
from porcaro.processing.onset import get_librosa_onsets
from porcaro.processing.window import get_fixed_window_size
from porcaro.processing.matching import eighth_note_grid_matching
from porcaro.processing.formatting import format_for_prediction
from porcaro.processing.resampling import apply_resampling_to_dataframe
from porcaro.processing.compression import apply_compression_to_dataframe
from porcaro.models.annoteator.prediction import run_prediction

logger = logging.getLogger(__name__)


def transcribe_drum_audio(
    fpath: Path | str,
    time_sig: TimeSignature,
    start_beat: int | float = 1,
    offset: float = 0.0,
    duration: float | None = None,
    resolution: int | float | None = 16,
):
    '''Transcribes an audio file to a drum transcription.

    Args:
        fpath (Path | str): Path to the audio file.
        time_sig (TimeSignature): Time signature of the audio file.
        start_beat (int | float): The beat to start the transcription from.
            Use 1 for the first beat, and decimal values for sub-beats relative to the
            time signature. Default is 1 (first quarter note).
        offset (float): Offset in seconds to start reading the audio file.
        duration (float | None): Duration in seconds to read from the audio file.
            If None, reads until the end of the file.
        resolution (int | float | None): Window size resolution. Integer value
            represents the size in terms of note duration. Must be one of 4, 8, 16, or
            32. A float value represents the size in seconds. A None value means
            that the window size will be calculated using the 25% quantile of all time
            differences between each detected drum hit. Default is 16.

    Returns:

    '''
    # Load the audio file
    track, sample_rate = librosa.load(fpath, offset=offset, duration=duration)
    duration = librosa.get_duration(y=track, sr=sample_rate)
    # Estimate the BPM
    bpm = BPM.from_audio(track, sample_rate)
    logger.info(f'BPM: {bpm}')
    song_data = SongData(bpm, time_sig, duration, sample_rate, start_beat)
    # Get onsets
    onsets = get_librosa_onsets(
        track, song_data.sample_rate, hop_length=1024 if bpm < 110 else 512
    )
    # Get window size
    window_size = get_fixed_window_size(resolution, song_data, onsets)
    # Format data into a DataFrame for prediction
    df = format_for_prediction(track, song_data, onsets, window_size)
    # Apply resampling to the dataframe to ensure the audio clip length is consistent
    # for the model.
    apply_resampling_to_dataframe(df, target_length=8820)
    # Apply compression to the dataframe
    apply_compression_to_dataframe(df)
    # Run prediction
    df = run_prediction(df, song_data.sample_rate)
    # Match notes via eighth note grid algorithm
    eighth_note_grid_matching(df, song_data)
