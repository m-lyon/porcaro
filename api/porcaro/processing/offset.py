import logging

import numpy as np
import pandas as pd
import librosa

from porcaro.utils import BPM

logger = logging.getLogger(__name__)


def get_eighth_note_time_grid(
    note_offset: int,
    sample_rate: int | float,
    bpm: BPM,
    onsets: pd.Series | np.ndarray,
    duration: float,
) -> np.ndarray:
    '''Calculates the eighth note time grid.

    Args:
        note_offset (int): The offset in notes to start the grid from.
        sample_rate (int | float): The sample rate of the audio.
        bpm (BPM): The BPM of the audio.
        onsets (pd.Series): The detected onsets in the audio.
        duration (float): The duration of the audio in seconds.

    Returns:
        np.ndarray: An array of time values for the eighth note grid.

    '''
    first_note = librosa.samples_to_time(onsets[note_offset], sr=sample_rate)
    return np.arange(first_note, duration, bpm.eighth_note)


def estimate_note_offset():
    total_eighth_notes: list[int] = []
    for n in range(20):
        tmp_eighth_note_grid = get_eighth_note_time_grid(n)
        tmp_synced_eighth_note_grid = map_onsets_to_eighth_notes(tmp_eighth_note_grid)
        total_eighth_notes.append(
            len(
                np.intersect1d(
                    np.around(note_line, 8),
                    np.around(tmp_synced_eighth_note_grid, 8),
                )
            )
        )
    note_offset = int(np.argmax(total_eighth_notes))
    logger.info('Note offset set to %d', note_offset)
    return note_offset
