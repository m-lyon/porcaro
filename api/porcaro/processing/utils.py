from porcaro.processing.bpm import BPM
from dataclasses import dataclass


def get_note_duration(resolution: int, bpm: float | int | BPM) -> float:
    '''Calculate the duration of a note based on the resolution and bpm.'''
    valid_resolutions = {4: 1, 8: 2, 16: 4, 32: 8}
    if resolution not in valid_resolutions:
        raise ValueError('Resolution must be either 4, 8, 16, or 32')
    return 60 / bpm / valid_resolutions[resolution]


@dataclass
class TimeSignature:
    '''Class to represent a time signature.'''

    beats_in_measure: int
    note_value: int

    def __repr__(self) -> str:
        return f'{self.beats_in_measure}/{self.note_value}'

    def eighth_note_beat(self, pos: float | int) -> float:
        '''Get the 8th note beat position given a position in the measure.

        Args:
            pos (float | int): Position in the measure.

        Returns:
            float: The 8th note beat position.
        '''
        assert pos >= 1, (
            'Position must be greater than or equal to 1 (start of the measure)'
        )
        assert self.note_value & (self.note_value - 1) == 0, (
            'Note value must be a power of 2'
        )
        if self.note_value == 8:
            eighth_notes_in_measure = self.beats_in_measure
            eighth_note_pos = pos
        divisor = self.note_value / 8

        eighth_notes_in_measure = self.beats_in_measure / divisor
        eighth_note_pos = pos / divisor
        assert eighth_note_pos < eighth_notes_in_measure + 1, (
            'Position must be less than or equal to the number of beats in the measure'
        )
        return eighth_note_pos


@dataclass
class SongData:
    '''Class to represent song metadata.'''

    bpm: BPM
    time_signature: TimeSignature
    duration: float
    sample_rate: int | float
    start_beat: float
