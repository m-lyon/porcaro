'''Module for matching notes to measures using the eighth note grid algorithm.'''

import numpy as np
import pandas as pd
from music21 import duration

from porcaro.utils import SongData
from porcaro.processing.grid import get_eighth_note_grid_from_df
from porcaro.processing.grid import sync_eighth_note_grid_to_onsets
from porcaro.utils.time_signature import TimeSignature
from porcaro.processing.subdivision import EighthNoteSubdivisions
from porcaro.processing.subdivision import EighthNoteTupletSubdivisions


def eighth_note_grid_matching(
    df: pd.DataFrame,
    song_data: SongData,
) -> tuple[list[duration.Duration], list[str | list[str]]]:
    '''Matches notes to measures using the eighth note grid algorithm.

    This function is a placeholder for the actual implementation of the
    eighth note grid matching logic.

    Returns:
        list[duration.Duration]: List of matched durations.
        list[str | list[str]]: List of matched note types.

    '''
    grid = get_eighth_note_grid_from_df(df, song_data)
    grid = sync_eighth_note_grid_to_onsets(
        grid, df.peak_time, song_data.bpm.thirty_second_note
    )
    note_predictions = df[['peak_time', 'hits']].copy()
    # tolerance is set to 0.0 as the grid is already synced to the onsets
    matched_durations, matched_notes = match_by_eighth_notes(
        grid, note_predictions, time_sig=song_data.time_signature, tolerance=0.0
    )
    return matched_durations, matched_notes


def match_by_eighth_notes(
    grid: np.ndarray,
    note_predictions: pd.DataFrame,
    time_sig: TimeSignature,
    tolerance: float,
) -> tuple[list[duration.Duration], list[str | list[str]]]:
    '''Matches notes to the eighth note grid.

    Args:
        grid (np.ndarray): The eighth note grid.
        note_predictions (pd.DataFrame): DataFrame containing the note predictions.
            Must contain 'peak_time' and 'hits' columns.
        time_sig (TimeSignature): The time signature of the song.
        tolerance (float): The tolerance within which to match notes.

    Returns:
        list[duration.Duration]: List of matched durations.
        list[str | list[str]]: List of matched note types.

    '''
    # NOTE: if the grid is previously synced to the onsets, then the tolerance
    # should be 0, as this tolerance is already accounted for in the grid.
    assert {'peak_time', 'hits'}.issubset(note_predictions.columns), (
        'note_predictions must contain "peak_time" and "hits" columns.'
    )
    matched_durations: list[duration.Duration] = []
    matched_notes: list[str | list[str]] = []
    for i in range(0, len(grid) - 1, 2):
        start_time, middle_time, end_time = grid[i], grid[i + 1], grid[i + 2]
        # get notes within the tolerance of the start and end time
        first_matching_notes = get_notes_within_tolerance(
            note_predictions, start_time, middle_time, tolerance
        )
        second_matching_notes = get_notes_within_tolerance(
            note_predictions, middle_time, end_time, tolerance
        )

        first_match = EighthNoteSubdivisions.match(
            start_time, middle_time, time_sig, first_matching_notes
        )
        second_match = EighthNoteSubdivisions.match(
            middle_time, end_time, time_sig, second_matching_notes
        )
        tuplet_match = EighthNoteTupletSubdivisions.match(
            start_time,
            end_time,
            time_sig,
            pd.concat(
                [first_matching_notes, second_matching_notes], axis=0, ignore_index=True
            ),
        )

        if tuplet_match is not None:
            best_match = min(first_match + second_match, tuplet_match)
        else:
            best_match = first_match + second_match
        matched_durations.extend(best_match.durations)
        matched_notes.extend(best_match.notes)

    return matched_durations, matched_notes


def get_notes_within_tolerance(
    note_predictions: pd.DataFrame,
    start_time: float,
    end_time: float,
    tolerance: float,
) -> pd.DataFrame:
    '''Finds notes within a certain tolerance of a given time range.

    Args:
        note_predictions (pd.DataFrame): DataFrame containing the note predictions.
            Must contain 'peak_time' and 'hits' columns.
        start_time (float): The start time of the range.
        end_time (float): The end time of the range.
        tolerance (float): The tolerance within which to find notes.

    Returns:
        pd.DataFrame: The notes found within the tolerance.

    '''
    onset_times = np.asarray(note_predictions['peak_time'])
    # Find the first onset that is within the tolerance of the start time
    start_idx = np.searchsorted(onset_times, start_time - tolerance, side='left')
    # Find the last onset that is within the tolerance of the end time
    end_idx = np.searchsorted(onset_times, end_time + tolerance, side='left')
    # Return the notes within the tolerance
    return note_predictions[start_idx:end_idx].copy()
