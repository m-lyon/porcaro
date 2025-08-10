'''Module for matching notes to measures using the eighth note grid algorithm.'''

import numpy as np
import pandas as pd
from music21 import duration

from porcaro.utils import SongData
from porcaro.processing.grid import EighthNoteSubdivisions
from porcaro.processing.grid import EighthNoteTupletSubdivisions
from porcaro.processing.grid import get_eighth_note_grid_from_df
from porcaro.processing.grid import sync_eighth_note_grid_to_onsets
from porcaro.utils.time_signature import TimeSignature


def eighth_note_grid_matching(
    df: pd.DataFrame,
    song_data: SongData,
) -> tuple[list[duration.Duration], list[str]]:
    '''Matches notes to measures using the eighth note grid algorithm.

    This function is a placeholder for the actual implementation of the
    eighth note grid matching logic.

    Returns:
        list[duration.Duration]: List of matched durations.
        list[str]: List of matched note types.

    '''
    # Placeholder for the actual implementation
    grid = get_eighth_note_grid_from_df(df, song_data)
    grid = sync_eighth_note_grid_to_onsets(
        grid, df.peak_time, song_data.bpm.thirty_second_note
    )
    note_predictions = df[['peak_time', 'hit_type']].copy()
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
) -> tuple[list[duration.Duration], list[str]]:
    '''Matches notes to the eighth note grid.

    Args:
        grid (np.ndarray): The eighth note grid.
        note_predictions (pd.DataFrame): DataFrame containing the note predictions.
            Must contain 'peak_time' and 'hit_type' columns.
        time_sig (TimeSignature): The time signature of the song.
        tolerance (float): The tolerance within which to match notes.

    Returns:
        list[duration.Duration]: List of matched durations.
        list[str]: List of matched note types.

    '''
    # NOTE: if the grid is previously synced to the onsets, then the tolerance
    # should be 0, as this tolerance is already accounted for in the grid.
    assert {'peak_time', 'hit_type'}.issubset(note_predictions.columns), (
        'note_predictions must contain "peak_time" and "hit_type" columns.'
    )
    matched_durations: list[duration.Duration] = []
    matched_notes: list[str] = []
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
            Must contain 'peak_time' and 'hit_type' columns.
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
    end_idx = np.searchsorted(onset_times, end_time + tolerance, side='right')
    # Return the notes within the tolerance
    return note_predictions[start_idx:end_idx].copy()


# def match_by_eighth_notes(
#     grid: np.ndarray, onset_times: pd.Series | np.ndarray, tolerance: float
# ):
#     for i in range(len(grid) - 1):
#         eighth_note = EighthNote(grid[i], grid[i + 1])
#         # find any notes within the start and end time
#         matched_notes = _get_matched_notes_from_eighth_note(
#             onset_times, eighth_note, tolerance
#         )


# def _get_notes_within_tolerance(
#     onset_times: pd.Series | np.ndarray,
#     eighth_note: EighthNote,
#     tolerance: float,
# ) -> tuple[pd.Series | np.ndarray, np.intp, np.intp]:
#     '''Finds notes within a certain tolerance of a given time range.

#     Args:
#         onset_times (pd.Series | np.ndarray): The onset times to search.
#         start_time (float): The start time of the range.
#         end_time (float): The end time of the range.
#         tolerance (float): The tolerance within which to find notes.

#     Returns:
#         pd.Series | np.ndarray: The notes found within the tolerance.

#     '''
#     onset_times = np.asarray(onset_times)
#     # Find the first onset that is within the tolerance of the start time
#     start_idx = np.searchsorted(
#         onset_times, eighth_note.start_time - tolerance, side='left'
#     )
#     # Find the last onset that is within the tolerance of the end time
#     end_idx = np.searchsorted(
#         onset_times, eighth_note.end_time + tolerance, side='right'
#     )
#     # Return the notes within the tolerance
#     return onset_times[start_idx:end_idx], start_idx, end_idx


# def _get_matched_notes_from_eighth_note(
#     onset_times: pd.Series | np.ndarray,
#     start_time: float,
#     end_time: float,
#     tolerance: float,
# ) -> list[dict[str, float | str]]:
#     matching_notes, start_idx, end_idx = _get_notes_within_tolerance(
#         onset_times, start_time, end_time, tolerance
#     )
#     notes = []
#     if len(matching_notes) == 0:
#         notes.append({'type': 'rest', 'duration': 0.5})
#         return notes
#     if len(matching_notes) == 1:
#         notes.append(
#             {
#                 'type': 'hit',
#                 'index': start_idx,
#                 'duration': 0.5,
#             }
#         )
#         return notes
