'''Module for handling BPM calculations and conversions.'''

import numpy as np
from librosa.feature import rhythm

from .time_signature import TimeSignature


class BPM:
    '''Class to handle BPM calculations.'''

    def __init__(self, bpm: float):
        '''Initialize the BPM class.'''
        self.bpm = bpm

    def __lt__(self, other: 'BPM | float | int') -> bool:
        '''Compare BPM with another BPM or a number.'''
        if isinstance(other, BPM):
            return self.bpm < other.bpm
        return self.bpm < other

    def __eq__(self, other: 'BPM | float | int') -> bool:
        '''Check equality with another BPM or a number.'''
        if isinstance(other, BPM):
            return self.bpm == other.bpm
        return self.bpm == other

    def __gt__(self, other: 'BPM | float | int') -> bool:
        '''Compare BPM with another BPM or a number.'''
        if isinstance(other, BPM):
            return self.bpm > other.bpm
        return self.bpm > other

    def __mul__(self, other: 'BPM | float | int') -> float:
        '''Multiply BPM by another BPM or a number.'''
        if isinstance(other, BPM):
            return self.bpm * other.bpm
        return self.bpm * other

    def __rmul__(self, other: 'BPM | float | int') -> float:
        '''Reverse multiply BPM by another BPM or a number.'''
        if isinstance(other, BPM):
            return other.bpm * self.bpm
        return other * self.bpm

    def __truediv__(self, other: 'BPM | float | int') -> float:
        '''Divide BPM by another BPM or a number.'''
        if isinstance(other, BPM):
            return self.bpm / other.bpm
        return self.bpm / other

    def __rtruediv__(self, other: 'BPM | float | int') -> float:
        '''Reverse divide BPM by another BPM or a number.'''
        if isinstance(other, BPM):
            return other.bpm / self.bpm
        return other / self.bpm

    def __repr__(self) -> str:
        '''Return a string representation of the BPM.'''
        return f'{self.bpm} BPM'

    @property
    def eighth_note(self) -> float:
        '''The duration of an eighth note.'''
        return 60 / self.bpm / 2

    @property
    def eighth_note_triplet(self) -> float:
        '''The duration of an eighth note triplet.'''
        return 60 / self.bpm / 3

    @property
    def dotted_eighth_note(self) -> float:
        '''The duration of a dotted eighth note.'''
        return self.eighth_note * 1.5

    @property
    def sixteenth_note(self) -> float:
        '''The duration of a sixteenth note.'''
        return 60 / self.bpm / 4

    @property
    def sixteenth_note_triplet(self) -> float:
        '''The duration of a sixteenth note triplet.'''
        return 60 / self.bpm / 6

    @property
    def dotted_sixteenth_note(self) -> float:
        '''The duration of a dotted sixteenth note.'''
        return self.sixteenth_note * 1.5

    @property
    def thirty_second_note(self) -> float:
        '''The duration of a thirty-second note.'''
        return 60 / self.bpm / 8

    @classmethod
    def from_audio(cls, track: np.ndarray, sample_rate: int | float) -> 'BPM':
        '''Estimate BPM from an audio track.'''
        bpm = rhythm.tempo(y=track, sr=sample_rate)[0]
        return cls(bpm)

    @classmethod
    def from_eighth_note(cls, duration: float, time_sig: TimeSignature) -> 'BPM':
        '''Calculate BPM from an eighth note duration and time signature.'''
        # NOTE: this assumes the BPM estimation takes into account the time signature,
        # when in fact it may just assume a 4/4 time. Will need to test for scenarios
        # with a different time signature, e.g. 6/8.
        bpm = (60 / duration) * (time_sig.note_value / 8)
        return cls(bpm)
