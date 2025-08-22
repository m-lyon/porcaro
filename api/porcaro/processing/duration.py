'''Module for creating music21 Duration objects based on note types.'''

from music21 import duration

from porcaro.utils import BPM


def get_note_duration(resolution: int, bpm: float | int | BPM) -> float:
    '''Calculate the duration of a note based on the resolution and bpm.'''
    valid_resolutions = {4: 1, 8: 2, 16: 4, 32: 8}
    if resolution not in valid_resolutions:
        raise ValueError('Resolution must be either 4, 8, 16, or 32')
    return 60 / bpm / valid_resolutions[resolution]


class Duration:
    '''Factory class for creating music21 Duration objects based on note types.'''

    @staticmethod
    def eighth_note():
        '''Returns an eighth note duration.'''
        return duration.Duration(1 / 2)

    @staticmethod
    def eighth_note_triplet():
        '''Returns an eighth note triplet duration.'''
        return duration.Duration(1 / 3)

    @staticmethod
    def dotted_eighth_note():
        '''Returns a dotted eighth note duration.'''
        return duration.Duration(3 / 4)

    @staticmethod
    def sixteenth_note():
        '''Returns a sixteenth note duration.'''
        return duration.Duration(1 / 4)

    @staticmethod
    def sixteenth_note_triplet():
        '''Returns a sixteenth note triplet duration.'''
        return duration.Duration(1 / 6)

    @staticmethod
    def dotted_sixteenth_note():
        '''Returns a dotted sixteenth note duration.'''
        return duration.Duration(3 / 8)

    @staticmethod
    def thirty_second_note():
        '''Returns a thirty-second note duration.'''
        return duration.Duration(1 / 8)

    @staticmethod
    def dotted_thirty_second_note():
        '''Returns a dotted thirty-second note duration.'''
        return duration.Duration(3 / 16)
