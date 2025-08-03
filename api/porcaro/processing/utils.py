'''Utility functions and classes for processing music data.'''

from porcaro.utils import BPM


def get_note_duration(resolution: int, bpm: float | int | BPM) -> float:
    '''Calculate the duration of a note based on the resolution and bpm.'''
    valid_resolutions = {4: 1, 8: 2, 16: 4, 32: 8}
    if resolution not in valid_resolutions:
        raise ValueError('Resolution must be either 4, 8, 16, or 32')
    return 60 / bpm / valid_resolutions[resolution]
