'''Module for calculating fixed window sizes.'''

import logging

import numpy as np
import pandas as pd
import librosa

from porcaro.utils import SongData
from porcaro.processing.duration import get_note_duration

logger = logging.getLogger(__name__)


def get_onsets_window_size(
    resolution: int | float | None,
    song_data: SongData,
    onsets: np.ndarray,
) -> int:
    '''Get the fixed window size based on resolution, bpm, sample rate, and onsets.

    Args:
        resolution (int | float | None): Window size resolution.
            Integer value: window size in terms of note duration. Must be one of
                - 4 (quarter note)
                - 8 (eighth note)
                - 16 (sixteenth note)
                - 32 (thirty-second note)
            Float value: window size in seconds. `None` means that the window size will
                be calculated using the 25% quantile of all time differences between
                each detected drum hit.
        song_data (SongData): Song metadata including bpm, sample rate, and duration.
        onsets (np.ndarray): Array of onset samples.
    '''
    assert isinstance(resolution, int | float | type(None)), (
        'resolution must be either an integer, a float, or None.'
    )
    if isinstance(resolution, float):
        return librosa.time_to_samples(resolution, sr=song_data.sample_rate)  # type: ignore
    if resolution is None:
        return int(pd.Series(onsets).diff().quantile(q=0.1))
    if isinstance(resolution, int):
        duration = get_note_duration(resolution, song_data.bpm)
        return librosa.time_to_samples(duration, sr=song_data.sample_rate)  # type: ignore


def get_windowed_sample(
    track: np.ndarray,
    sample_rate: int | float,
    peak_time: float,
    window_size: float,
) -> np.ndarray:
    '''Get a fixed-size windowed sample from the audio track centered around the peak.

    Args:
        track (np.ndarray): The audio data of the drum track.
        sample_rate (int | float): The sample rate of the audio track.
        peak_time (float): The time of the peak in seconds.
        window_size (float): The size of the window for each audio clip in seconds.

    Returns:
        np.ndarray: The windowed audio sample.
    '''
    half_window = window_size / 2
    start_sample = max(
        0, int(librosa.time_to_samples(peak_time - half_window, sr=sample_rate))
    )
    end_sample = min(
        track.shape[0],
        int(librosa.time_to_samples(peak_time + half_window, sr=sample_rate)),
    )

    # If the window is smaller than the desired size, pad it with zeros
    if end_sample - start_sample < window_size:
        windowed_sample = np.zeros(
            int(librosa.time_to_samples(window_size, sr=sample_rate))
        )
        windowed_sample[: end_sample - start_sample] = track[start_sample:end_sample]
    else:
        windowed_sample = track[start_sample:end_sample]

    return windowed_sample
