from dataclasses import dataclass

import librosa
import numpy as np
import pandas as pd
from music21 import duration


from porcaro.processing.bpm import BPM
from porcaro.processing.utils import SongData, TimeSignature


def get_eighth_note_time_grid(
    song_data: SongData,
    start_time: float,
) -> np.ndarray:
    '''Generates an eighth note time grid.

    Args:
        duration (float): The duration of the audio in seconds.
        bpm (BPM): The BPM of the audio.
        start_time (float): The start time of the beat in seconds. This is the time
            that the grid is aligned to.
        start_beat (float): The beat number, relative to the time signature,
        that the `start_time` corresponds to. This is used to calculate where (in time)
        the grid starts.
        time_sig (TimeSignature): The time signature of the audio.

    Returns:
        np.ndarray: An array of time values for the eighth note grid.
    '''
    eighth_note_start_beat = song_data.time_signature.eighth_note_beat(
        song_data.start_beat
    )
    measure_start_offset = (eighth_note_start_beat - 1) * song_data.bpm.eighth_note
    measure_start = start_time - measure_start_offset
    assert measure_start >= 0, (
        'Measure start cannot be negative. '
        'Check the start_beat and start_onset parameters.'
    )
    return np.arange(measure_start, song_data.duration, song_data.bpm.eighth_note)


def get_eighth_note_grid_from_df(df: pd.DataFrame, song_data: SongData) -> np.ndarray:
    '''Generates an eighth note time grid from a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame containing audio segment information.
        sample_rate (int | float): The sample rate of the audio.
        bpm (BPM): The BPM of the audio.
        time_sig (TimeSignature): The time signature of the audio.

    Returns:
        np.ndarray: An array of time values for the eighth note grid.
    '''
    # Extract relevant information from the DataFrame
    start_time = librosa.samples_to_time(df.peak_sample[0], sr=song_data.sample_rate)

    return get_eighth_note_time_grid(song_data, start_time)


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


class Duration:
    '''Factory class for creating music21 Duration objects based on note types'''

    @staticmethod
    def eighth_note():
        return duration.Duration(1 / 2)

    @staticmethod
    def eighth_note_triplet():
        return duration.Duration(1 / 3)

    @staticmethod
    def dotted_eighth_note():
        return duration.Duration(3 / 4)

    @staticmethod
    def sixteenth_note():
        return duration.Duration(1 / 4)

    @staticmethod
    def sixteenth_note_triplet():
        return duration.Duration(1 / 6)

    @staticmethod
    def dotted_sixteenth_note():
        return duration.Duration(3 / 8)

    @staticmethod
    def thirty_second_note():
        return duration.Duration(1 / 8)

    @staticmethod
    def dotted_thirty_second_note():
        return duration.Duration(3 / 16)


class EighthNote:
    '''Class representing an eighth note and its subdivisions.'''

    def __init__(self, start_time: float, end_time: float):
        '''Initialize the Grid class.'''
        self.start_time = start_time
        self.end_time = end_time
        self._eighth_notes = np.array([start_time, end_time])
        self._sixteenth_notes = None
        self._thirty_second_notes = None
        self._eighth_note_triplets = None
        self._eighth_note_sixlets = None

    @property
    def eighth_note(self) -> np.ndarray:
        '''The eighth note starting point.'''
        return self._eighth_notes[0:1]

    @property
    def sixteenth_notes(self) -> np.ndarray:
        '''The sixteenth note grid.'''
        if self._sixteenth_notes is not None:
            return self._sixteenth_notes
        self._sixteenth_notes = self._eighth_notes[:-1] + (
            np.diff(self._eighth_notes) / 2
        )
        return self._sixteenth_notes

    @property
    def thirty_second_notes(self) -> np.ndarray:
        '''The thirty-second note grid.'''
        if self._thirty_second_notes is not None:
            return self._thirty_second_notes
        combined = np.sort(
            np.concatenate((self._eighth_notes, self.sixteenth_notes), axis=0)
        )
        self._thirty_second_notes = combined[:-1] + (np.diff(combined) / 2)
        return self._thirty_second_notes

    @property
    def all_thirty_second_notes(self) -> np.ndarray:
        '''All thirty-second notes in the grid.'''
        return np.sort(
            np.concatenate(
                [self.eighth_note, self.sixteenth_notes, self.thirty_second_notes],
                axis=0,
            )
        )

    @property
    def eighth_note_triplets(self) -> np.ndarray:
        '''The eighth note triplet grid.'''
        if self._eighth_note_triplets is not None:
            return self._eighth_note_triplets
        triplets_first = self._eighth_notes[:-1] + (np.diff(self._eighth_notes) / 3)
        triplets_second = self._eighth_notes[:-1] + (
            np.diff(self._eighth_notes) / 3 * 2
        )
        self._eighth_note_triplets = np.sort(
            np.concatenate((triplets_first, triplets_second), axis=0)
        )
        return self._eighth_note_triplets

    @property
    def all_eighth_note_triplets(self) -> np.ndarray:
        '''All eighth note triplets in the grid.'''
        return np.sort(
            np.concatenate(
                [self.eighth_note, self.eighth_note_triplets],
                axis=0,
            )
        )

    @property
    def eighth_note_sixlets(self) -> np.ndarray:
        '''The eighth note sixlet grid.'''
        if self._eighth_note_sixlets is not None:
            return self._eighth_note_sixlets
        combined = np.sort(
            np.concatenate((self.eighth_note_triplets, self._eighth_notes), axis=0)
        )
        self._eighth_note_sixlets = combined[:-1] + (np.diff(combined) / 2)
        return self._eighth_note_sixlets

    @property
    def all_eighth_note_sixlets(self) -> np.ndarray:
        '''All eighth note sixlets in the grid.'''
        return np.sort(
            np.concatenate(
                [self.eighth_note, self.eighth_note_triplets, self.eighth_note_sixlets],
                axis=0,
            )
        )

    def _closest_match(self, notes) -> int:
        # We group the sixteenth and thirty-second notes together because the note
        # subdivision could be a combination of both.
        dist_to_thirty_second = np.average(
            np.min(np.abs(self.all_thirty_second_notes[:, None] - notes), axis=0)
        )
        dist_to_triplets = np.average(
            np.min(np.abs(self.all_eighth_note_triplets[:, None] - notes), axis=0)
        )
        dist_to_sixlets = np.average(
            np.min(np.abs(self.all_eighth_note_sixlets[:, None] - notes), axis=0)
        )
        dists = {
            32: dist_to_thirty_second,
            3: dist_to_triplets,
            6: dist_to_sixlets,
        }
        return min(dists, key=lambda k: dists[k])

    def match_notes_to_subdivision(self, notes: np.ndarray):
        notes = np.asarray(notes)
        # TODO: go through and list all the combos possible of 8th note subdivisions
        # and see if it would be easier to actually just compute the distances
        # to all the subdivisions and then assign the notes to the closest one.

        # Compute distances to all subdivisions in a vectorized way
        closest_match = self._closest_match(notes)
        if closest_match == 32:
            # TODO: walk through the notes and assign them to the closest
            # subdivision
            pass
        elif closest_match == 3:
            pass
        elif closest_match == 6:
            pass


@dataclass
class Subdivision:
    '''Class representing a subdivision.'''

    times: np.ndarray
    durations: list[duration.Duration]


class EighthNoteSubdivisions:
    def __init__(self, start_time: float, end_time: float, time_sig: TimeSignature):
        '''Initialize the EighthNoteSubdivisions class.'''
        self.start_time = start_time
        self.bpm = BPM.from_eighth_note(end_time - start_time, time_sig)

    def match_notes_to_subdivision(self, notes: pd.Series | np.ndarray) -> Subdivision:
        '''Matches notes to the closest eighth note subdivision.

        Args:
            notes (pd.Series | np.ndarray): The notes to match.

        Returns:
            dict[str, np.ndarray]: A dictionary with keys as subdivision names and
            values as arrays of matched notes.
        '''
        pass

    @property
    def subdivisions_by_num_notes(self) -> dict[int, list[Subdivision]]:
        '''Returns a dictionary of subdivisions by number of notes.'''
        return {
            1: [self.eighth_note()],
            2: [self.dotted_sixteenth_to_thirty_second()],
            3: [],
            4: [],
        }

    def eighth_note(self) -> Subdivision:
        return Subdivision(
            times=np.array([self.start_time]), durations=[Duration.eighth_note()]
        )

    def dotted_sixteenth_to_thirty_second(self) -> Subdivision:
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[Duration.dotted_sixteenth_note(), Duration.thirty_second_note()],
        )
