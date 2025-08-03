'''Module for calculating fixed window sizes.'''

import logging

import numpy as np
import pandas as pd
import librosa

from porcaro.utils import SongData
from porcaro.processing.utils import get_note_duration

logger = logging.getLogger(__name__)


def get_fixed_window_size(
    resolution: int | float | None,
    song_data: SongData,
    onsets: np.ndarray,
) -> int:
    '''Get the fixed window size based on resolution, bpm, sample rate, and onsets.

    Args:
        resolution (int | float | None): Window size resolution. Integer value
            represents the size in terms of note duration. Must be one of 4, 8, 16, or
            32. A float value represents the size in seconds. A None value means
            that the window size will be calculated using the 25% quantile of all time
            differences between each detected drum hit.
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
