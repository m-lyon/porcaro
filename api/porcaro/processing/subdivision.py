'''Module for handling rhythmic subdivisions.'''

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from music21 import duration

from porcaro.utils import BPM
from porcaro.utils import TimeSignature
from porcaro.processing.duration import Duration

logger = logging.getLogger(__name__)


@dataclass
class Match:
    '''Class representing a match of notes to a subdivision.'''

    distance: float
    durations: list[duration.Duration]
    notes: list[str | list[str]]

    def __add__(self, other: 'Match') -> 'Match':
        '''Adds two matches together.'''
        return Match(
            distance=self.distance + other.distance,
            durations=self.durations + other.durations,
            notes=self.notes + other.notes,
        )

    def __lt__(self, other: 'Match') -> bool:
        '''Compares two matches based on distance.'''
        return self.distance < other.distance

    def __gt__(self, other: 'Match') -> bool:
        '''Compares two matches based on distance.'''
        return self.distance > other.distance


@dataclass
class Subdivision:
    '''Class representing a subdivision.'''

    times: np.ndarray
    durations: list[duration.Duration]


class Subdivisions:
    '''Class representing a collection of subdivisions.'''

    def __init__(self, start_time: float, end_time: float, time_sig: TimeSignature):
        '''Initialize the Subdivisions class.'''
        raise NotImplementedError('This class is meant to be subclassed.')

    def match_notes(self, notes: pd.DataFrame) -> Match:
        '''Matches notes to the closest subdivision.

        Args:
            notes (pd.DataFrame): The notes to match.

        Returns:
            Match: The closest match to the notes in terms of subdivision.

        '''
        raise NotImplementedError('This method should be implemented in subclasses.')

    @staticmethod
    def _get_closest_match(
        notes: pd.DataFrame, possible_subdivs: list[Subdivision]
    ) -> Match:
        # Calculate distances to each possible subdivision
        distances = np.array(
            [
                np.sum(np.abs(notes['peak_time'] - subdiv.times))
                for subdiv in possible_subdivs
            ]
        )
        # Find the index of the closest subdivision
        closest_index = np.argmin(distances)
        closest_subdiv = possible_subdivs[closest_index]
        return Match(
            distance=distances[closest_index],
            durations=closest_subdiv.durations,
            notes=notes['hits'].tolist(),
        )

    @classmethod
    def match(
        cls,
        start_time: float,
        end_time: float,
        time_sig: TimeSignature,
        notes: pd.DataFrame,
    ) -> Match:
        '''Matches notes to the closest subdivision.

        Args:
            start_time (float): The start time of the subdivision.
            end_time (float): The end time of the subdivision.
            time_sig (TimeSignature): The time signature of the subdivision.
            notes (np.ndarray): The notes to match.

        Returns:
            Match: The closest match to the notes in terms of subdivision.

        '''
        return cls(start_time, end_time, time_sig).match_notes(notes)


class EighthNoteSubdivisions(Subdivisions):
    '''Class representing eighth note subdivisions.'''

    def __init__(self, start_time: float, end_time: float, time_sig: TimeSignature):
        '''Initialize the EighthNoteSubdivisions class.'''
        self.start_time = start_time
        self.bpm = BPM.from_eighth_note(end_time - start_time, time_sig)

    def match_notes(self, notes: pd.DataFrame) -> Match:
        '''Matches notes to the closest eighth note subdivision.

        Args:
            notes (pd.DataFrame): The notes to match.

        Returns:
            Match: The closest match to the notes in terms of subdivision.

        '''
        num_notes = len(notes)
        if num_notes == 0:
            return Match(0, [Duration.eighth_note()], ['REST'])
        omit_indices = []
        if num_notes > 4:
            logger.warning(
                'More than 4 notes detected. '
                'Dropping notes to match the closest subdivision.'
            )
            # If greater than 4 notes, drop notes with the closest distance to one
            # another until we have 4 notes.
            dists = np.abs(np.diff(notes['peak_time']))
            omit_indices = np.sort(np.argsort(dists)[: num_notes - 4])
            notes = notes.drop(omit_indices.tolist())
            num_notes = len(notes)
        possible_subdivs = self.get_possible_subdivisions()[num_notes]
        match = self._get_closest_match(notes, possible_subdivs)
        return match

    def get_possible_subdivisions(self) -> dict[int, list[Subdivision]]:
        '''Returns a dictionary of subdivisions by number of notes.'''
        return {
            1: [
                self.thirty_second_note(),
                self.sixteenth_note(),
                self.dotted_sixteenth_note(),
                self.eighth_note(),
            ],
            2: [
                self.two_thirty_second_notes(),
                self.sixteenth_and_thirty_second(),
                self.thirty_second_and_sixteenth(),
                self.dotted_sixteenth_and_thirty_second(),
                self.two_sixteenth_notes(),
                self.thirty_second_and_dotted_sixteenth(),
            ],
            3: [
                self.three_thirty_second_notes(),
                self.sixteenth_and_two_thirty_seconds(),
                self.thirty_second_and_sixteenth_and_thirty_second(),
                self.two_thirty_second_notes_and_sixteenth(),
            ],
            4: [self.four_thirty_second_notes()],
        }

    def thirty_second_note(self) -> Subdivision:
        '''Returns the thirty-second note subdivision.

        # 0001
        '''
        return Subdivision(
            times=np.array([self.start_time + self.bpm.dotted_sixteenth_note]),
            durations=[Duration.thirty_second_note()],
        )

    def sixteenth_note(self) -> Subdivision:
        '''Returns the sixteenth note subdivision.

        # 0010
        '''
        return Subdivision(
            times=np.array([self.start_time + self.bpm.sixteenth_note]),
            durations=[Duration.sixteenth_note()],
        )

    def two_thirty_second_notes(self) -> Subdivision:
        '''Returns the two thirty-second notes subdivision.

        # 0011
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time + self.bpm.sixteenth_note,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[Duration.thirty_second_note(), Duration.thirty_second_note()],
        )

    def dotted_sixteenth_note(self) -> Subdivision:
        '''Returns the dotted sixteenth note subdivision.

        # 0100
        '''
        return Subdivision(
            times=np.array([self.start_time + self.bpm.thirty_second_note]),
            durations=[Duration.dotted_sixteenth_note()],
        )

    def sixteenth_and_thirty_second(self) -> Subdivision:
        '''Returns the sixteenth note and thirty-second note subdivision.

        # 0101
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time + self.bpm.thirty_second_note,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[Duration.sixteenth_note(), Duration.thirty_second_note()],
        )

    def thirty_second_and_sixteenth(self) -> Subdivision:
        '''Returns the thirty-second note and sixteenth note subdivision.

        # 0110
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time + self.bpm.thirty_second_note,
                    self.start_time + self.bpm.sixteenth_note,
                ]
            ),
            durations=[Duration.thirty_second_note(), Duration.sixteenth_note()],
        )

    def three_thirty_second_notes(self) -> Subdivision:
        '''Returns the three thirty-second notes subdivision.

        # 0111
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time + self.bpm.thirty_second_note,
                    self.start_time + self.bpm.sixteenth_note,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[
                Duration.thirty_second_note(),
                Duration.thirty_second_note(),
                Duration.thirty_second_note(),
            ],
        )

    def eighth_note(self) -> Subdivision:
        '''Returns the eighth note subdivision.

        # 1000
        '''
        return Subdivision(
            times=np.array([self.start_time]),
            durations=[Duration.eighth_note()],
        )

    def dotted_sixteenth_and_thirty_second(self) -> Subdivision:
        '''Returns the dotted sixteenth note and thirty-second note subdivision.

        # 1001
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[Duration.dotted_sixteenth_note(), Duration.thirty_second_note()],
        )

    def two_sixteenth_notes(self) -> Subdivision:
        '''Returns the two sixteenth notes subdivision.

        # 1010
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.sixteenth_note,
                ]
            ),
            durations=[Duration.sixteenth_note(), Duration.sixteenth_note()],
        )

    def sixteenth_and_two_thirty_seconds(self) -> Subdivision:
        '''Returns the sixteenth note and two thirty-second notes subdivision.

        # 1011
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.sixteenth_note,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[
                Duration.sixteenth_note(),
                Duration.thirty_second_note(),
                Duration.thirty_second_note(),
            ],
        )

    def thirty_second_and_dotted_sixteenth(self) -> Subdivision:
        '''Returns the thirty-second note and dotted sixteenth note subdivision.

        # 1100
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.thirty_second_note,
                ]
            ),
            durations=[Duration.thirty_second_note(), Duration.dotted_sixteenth_note()],
        )

    def thirty_second_and_sixteenth_and_thirty_second(self) -> Subdivision:
        '''Returns the thirty-second, sixteenth, and thirty-second note subdivision.

        # 1101
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.thirty_second_note,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[
                Duration.thirty_second_note(),
                Duration.sixteenth_note(),
                Duration.thirty_second_note(),
            ],
        )

    def two_thirty_second_notes_and_sixteenth(self) -> Subdivision:
        '''Returns the two thirty-second notes and sixteenth note subdivision.

        # 1110
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.thirty_second_note,
                    self.start_time + self.bpm.sixteenth_note,
                ]
            ),
            durations=[
                Duration.thirty_second_note(),
                Duration.thirty_second_note(),
                Duration.sixteenth_note(),
            ],
        )

    def four_thirty_second_notes(self) -> Subdivision:
        '''Returns the four thirty-second notes subdivision.

        # 1111
        '''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.thirty_second_note,
                    self.start_time + self.bpm.sixteenth_note,
                    self.start_time + self.bpm.dotted_sixteenth_note,
                ]
            ),
            durations=[
                Duration.thirty_second_note(),
                Duration.thirty_second_note(),
                Duration.thirty_second_note(),
                Duration.thirty_second_note(),
            ],
        )


class EighthNoteTupletSubdivisions(Subdivisions):
    '''Class representing eighth note tuplet subdivisions.'''

    def __init__(self, start_time: float, end_time: float, time_sig: TimeSignature):
        '''Initialize the EighthNoteTupletSubdivisions class.

        Args:
            start_time (float): The start time of the tuplet.
            end_time (float): The end time of the tuplet. This should span two
                eighth notes.
            time_sig (TimeSignature): The time signature of the tuplet.

        '''
        self.start_time = start_time
        self.bpm = BPM.from_eighth_note((end_time - start_time) / 2, time_sig)

    def get_possible_subdivisions(self) -> dict[int, list[Subdivision]]:
        '''Returns a dictionary of tuplet subdivisions by number of notes.'''
        # We omit the 1-note tuplet as that would be better represented by a straight
        # note.
        return {
            2: [self.rested_first(), self.rested_second(), self.rested_third()],
            3: [self.three_triplets()],
        }

    def rested_first(self) -> Subdivision:
        '''Returns the rested first tuplet subdivision.'''
        return Subdivision(
            times=np.array(
                [
                    self.start_time + self.bpm.eighth_note_triplet,
                    self.start_time + self.bpm.eighth_note_triplet * 2,
                ]
            ),
            durations=[
                Duration.eighth_note_triplet(),
                Duration.eighth_note_triplet(),
            ],
        )

    def rested_second(self) -> Subdivision:
        '''Returns the rested second tuplet subdivision.'''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.eighth_note_triplet * 2,
                ]
            ),
            durations=[
                Duration.eighth_note_triplet(),
                Duration.eighth_note_triplet(),
            ],
        )

    def rested_third(self) -> Subdivision:
        '''Returns the rested third tuplet subdivision.'''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.eighth_note_triplet,
                ]
            ),
            durations=[
                Duration.eighth_note_triplet(),
                Duration.eighth_note_triplet(),
            ],
        )

    def three_triplets(self) -> Subdivision:
        '''Returns the three eighth note triplets subdivision.'''
        return Subdivision(
            times=np.array(
                [
                    self.start_time,
                    self.start_time + self.bpm.eighth_note_triplet,
                    self.start_time + self.bpm.eighth_note_triplet * 2,
                ]
            ),
            durations=[
                Duration.eighth_note_triplet(),
                Duration.eighth_note_triplet(),
                Duration.eighth_note_triplet(),
            ],
        )

    def match_notes(self, notes: pd.DataFrame) -> Match | None:
        '''Matches notes to the closest eighth note subdivision.

        Args:
            notes (pd.DataFrame): The notes to match.

        Returns:
            Match: The closest match to the notes in terms of subdivision.

        '''
        num_notes = len(notes)
        subdivs = self.get_possible_subdivisions()
        if num_notes not in subdivs:
            return None
        possible_subdivs = subdivs[num_notes]
        return self._get_closest_match(notes, possible_subdivs)
