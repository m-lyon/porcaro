'''Time Signature dataclass.'''

from dataclasses import dataclass


@dataclass
class TimeSignature:
    '''Class to represent a time signature.'''

    beats_in_measure: int
    note_value: int

    def __repr__(self) -> str:
        '''Return a string representation of the time signature.'''
        return f'{self.beats_in_measure}/{self.note_value}'

    def eighth_note_beat(self, pos: float | int) -> float:
        '''Get the 8th note beat number given a position in the measure.

        Args:
            pos (float | int): Position in the measure (starting at 1.0).

        Returns:
            int: The corresponding 8th note number (starting at 1).

        '''
        assert pos >= 1, 'Position must be ≥ 1 (start of the measure)'
        assert self.note_value & (self.note_value - 1) == 0, (
            'Note value must be a power of 2'
        )

        # Convert to eighth-note subdivisions:
        # Determine how many eighth notes per beat
        eighths_per_beat = 8 / self.note_value
        eighth_note_pos = (pos - 1) * eighths_per_beat + 1
        total_eighths = self.beats_in_measure * eighths_per_beat

        assert eighth_note_pos <= total_eighths, (
            f'Position exceeds measure length: {eighth_note_pos} > {total_eighths}'
        )

        return eighth_note_pos
