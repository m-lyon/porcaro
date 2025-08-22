'''Provides functions and classes for music grid processing.'''

import logging

import numpy as np
import pandas as pd
import librosa

from porcaro.utils import SongData

logger = logging.getLogger(__name__)


def get_eighth_note_time_grid(
    song_data: SongData,
    drum_start_time: float,
) -> np.ndarray:
    '''Generates an eighth note time grid.

    Args:
        song_data (SongData): The song metadata including bpm, sample rate, and
            duration.
        drum_start_time (float): The time in seconds when the first drum hit occurs.

    Returns:
        np.ndarray: An array of time values for the eighth note grid.

    '''
    eighth_note_start_beat = song_data.time_signature.eighth_note_beat(
        song_data.start_beat
    )
    measure_start_offset = (eighth_note_start_beat - 1) * song_data.bpm.eighth_note
    measure_start = drum_start_time - measure_start_offset
    assert measure_start >= 0, (
        'Measure start cannot be negative. '
        'Check the start_beat and start_onset parameters.'
    )
    return np.arange(measure_start, song_data.duration, song_data.bpm.eighth_note)


def get_eighth_note_grid_from_df(df: pd.DataFrame, song_data: SongData) -> np.ndarray:
    '''Generates an eighth note time grid from a DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing onset information with a 'peak_sample'
            column.
        song_data (SongData): The song metadata including bpm, sample rate, and
            duration.

    Returns:
        np.ndarray: An array of time values for the eighth note grid.

    '''
    # Extract relevant information from the DataFrame
    drum_start_time = librosa.samples_to_time(
        df.peak_sample[0], sr=song_data.sample_rate
    )

    return get_eighth_note_time_grid(song_data, drum_start_time)


def sync_eighth_note_grid_to_onsets(
    grid: np.ndarray, onset_times: pd.Series | np.ndarray, tolerance: float
) -> np.ndarray:
    '''Syncs the eighth note grid to the onsets in the DataFrame.

    This function adjusts the eighth note grid to align with the detected onsets,
    modifying the grid where the onsets match the eighth note interval within a
    certain tolerance (e.g. 32nd note).

    Assumptions:
        - `grid` and `onset_times` are both sorted arrays.
        - there won't be more than one onset within the tolerance for each grid point.
            This algorithm will use the first onset that matches the grid point within
            the tolerance.

    Args:
        grid (np.ndarray): The eighth note grid to sync.
        onset_times (pd.Series | np.ndarray): The onset times to sync the grid to.
        tolerance (float): The tolerance within which to match the onsets to the grid.

    Returns:
        np.ndarray: The synced eighth note grid.

    '''
    # Efficiently sync grid to onsets using sorted arrays
    synced_grid = np.copy(grid)
    onset_times = np.asarray(onset_times)
    onset_idx = 0
    n_onsets = len(onset_times)

    for i, grid_time in enumerate(grid):
        # Advance onset_idx to the first onset >= grid_time - tolerance
        while onset_idx < n_onsets and onset_times[onset_idx] < grid_time - tolerance:
            onset_idx += 1
        # Check if onset_idx is within bounds and within tolerance
        if (
            onset_idx < n_onsets
            and abs(onset_times[onset_idx] - grid_time) <= tolerance
        ):
            synced_grid[i] = onset_times[onset_idx]

    return synced_grid
