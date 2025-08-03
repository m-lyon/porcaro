'''Formatting module for drum track predictions.'''

import numpy as np
import pandas as pd
import librosa

from porcaro.utils import SongData
from porcaro.processing.utils import get_note_duration


def format_for_prediction(
    drum_track: np.ndarray,
    song_data: SongData,
    onsets: np.ndarray,
    window_size: int,
) -> pd.DataFrame:
    '''Formats the drum track for prediction.

    Args:
        drum_track (np.ndarray): The audio data of the drum track.
        song_data (SongData): Metadata about the song including BPM, sample rate, and
            duration.
        onsets (np.ndarray): The detected onsets in the audio.
        window_size (int): The size of the window for each audio clip.

    Returns:
        pd.DataFrame: A DataFrame containing the formatted audio clips, their start and
            end samples, sampling rate, peak sample, and peak time.

    '''
    padding = librosa.time_to_samples(
        get_note_duration(32, song_data.bpm) / 4, sr=song_data.sample_rate
    )

    clip_starts = np.maximum(onsets - padding, 0)
    clip_ends = clip_starts + window_size
    audio_clips = [
        drum_track[start:end]
        for start, end in zip(clip_starts, clip_ends, strict=False)
    ]

    df = pd.DataFrame.from_dict(
        {
            'audio_clip': audio_clips,
            'sample_start': clip_starts,
            'sample_end': clip_ends,
            'sampling_rate': [song_data.sample_rate] * len(onsets),
            'peak_sample': onsets,
            'peak_time': librosa.samples_to_time(onsets, sr=song_data.sample_rate),
        }
    )

    return df
