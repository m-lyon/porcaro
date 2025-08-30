'''Formatting module for drum track predictions.'''

import numpy as np
import pandas as pd
import librosa

from porcaro.utils import SongData
from porcaro.processing.duration import get_note_duration


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
        onsets (np.ndarray): The detected onsets in the audio in number of samples.
        window_size (int): The size of the window for each audio clip in number of
            samples.

    Returns:
        pd.DataFrame: A DataFrame containing the formatted audio clips, their start and
            end samples, sampling rate, peak sample, and peak time.
    '''
    padding = librosa.time_to_samples(
        get_note_duration(32, song_data.bpm) / 4, sr=song_data.sample_rate
    )

    clip_sample_starts = np.maximum(onsets - padding, 0)
    clip_time_starts = librosa.samples_to_time(
        clip_sample_starts, sr=song_data.sample_rate
    )
    clip_sample_ends = clip_sample_starts + window_size
    clip_time_ends = librosa.samples_to_time(clip_sample_ends, sr=song_data.sample_rate)
    audio_clips = [
        drum_track[start:end]
        for start, end in zip(clip_sample_starts, clip_sample_ends, strict=False)
    ]

    df = pd.DataFrame.from_dict(
        {
            'audio_clip': audio_clips,
            'start_sample': clip_sample_starts,
            'start_time': clip_time_starts,
            'end_sample': clip_sample_ends,
            'end_time': clip_time_ends,
            'sampling_rate': [song_data.sample_rate] * len(onsets),
            'peak_sample': onsets,
            'peak_time': librosa.samples_to_time(onsets, sr=song_data.sample_rate),
        }
    )

    return df
