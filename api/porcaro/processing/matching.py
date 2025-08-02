from porcaro.processing.grid import (
    EighthNote,
    get_eighth_note_grid_from_df,
    sync_eighth_note_grid_to_onsets,
)
from porcaro.processing.utils import SongData
import pandas as pd
import numpy as np


def eighth_note_grid_matching(
    df: pd.DataFrame,
    song_data: SongData,
):
    '''Matches notes to measures using the eighth note grid algorithm.

    This function is a placeholder for the actual implementation of the
    eighth note grid matching logic.

    Returns:
        None
    '''
    # Placeholder for the actual implementation
    grid = get_eighth_note_grid_from_df(df, song_data)
    grid = sync_eighth_note_grid_to_onsets(
        grid, df.peak_time, song_data.bpm.thirty_second_note
    )


def match_by_eighth_notes(
    grid: np.ndarray, onset_times: pd.Series | np.ndarray, tolerance: float
):
    for i in range(len(grid) - 1):
        eighth_note = EighthNote(grid[i], grid[i + 1])
        # find any notes within the start and end time
        matched_notes = _get_matched_notes_from_eighth_note(
            onset_times, eighth_note, tolerance
        )


def _get_notes_within_tolerance(
    onset_times: pd.Series | np.ndarray,
    eighth_note: EighthNote,
    tolerance: float,
) -> tuple[pd.Series | np.ndarray, np.intp, np.intp]:
    '''Finds notes within a certain tolerance of a given time range.

    Args:
        onset_times (pd.Series | np.ndarray): The onset times to search.
        start_time (float): The start time of the range.
        end_time (float): The end time of the range.
        tolerance (float): The tolerance within which to find notes.

    Returns:
        pd.Series | np.ndarray: The notes found within the tolerance.
    '''
    onset_times = np.asarray(onset_times)
    # Find the first onset that is within the tolerance of the start time
    start_idx = np.searchsorted(
        onset_times, eighth_note.start_time - tolerance, side='left'
    )
    # Find the last onset that is within the tolerance of the end time
    end_idx = np.searchsorted(
        onset_times, eighth_note.end_time + tolerance, side='right'
    )
    # Return the notes within the tolerance
    return onset_times[start_idx:end_idx], start_idx, end_idx


def _get_matched_notes_from_eighth_note(
    onset_times: pd.Series | np.ndarray,
    start_time: float,
    end_time: float,
    tolerance: float,
) -> list[dict[str, float | str]]:
    matching_notes, start_idx, end_idx = _get_notes_within_tolerance(
        onset_times, start_time, end_time, tolerance
    )
    notes = []
    if len(matching_notes) == 0:
        notes.append({'type': 'rest', 'duration': 0.5})
        return notes
    if len(matching_notes) == 1:
        notes.append(
            {
                'type': 'hit',
                'index': start_idx,
                'duration': 0.5,
            }
        )
        return notes
