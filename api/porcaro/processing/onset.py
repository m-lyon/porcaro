'''Onset detection for drum tracks.'''

import logging

import numpy as np
import librosa

from porcaro.utils.bpm import BPM

logger = logging.getLogger(__name__)


def get_librosa_onsets_v1(
    track: np.ndarray,
    sample_rate: int | float,
    bpm: float | BPM | int,
) -> np.ndarray:
    '''Convert onset frames to samples.

    Args:
        track (np.ndarray): The audio track to analyze.
        sample_rate (int | float): The sample rate of the audio track.
        bpm (float): The estimated BPM of the track.

    Returns:
        np.ndarray: Array of onset sample indices.
    '''
    bpm_threshold = 110
    hop_length = 1024 if bpm < bpm_threshold else 512
    onset_env = librosa.onset.onset_strength(
        y=track, sr=sample_rate, hop_length=hop_length
    )
    onset_frames = librosa.onset.onset_detect(
        y=track, onset_envelope=onset_env, sr=sample_rate
    )
    onsets = librosa.frames_to_samples(onset_frames * (hop_length / 512))

    return onsets
