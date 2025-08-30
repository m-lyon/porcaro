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


def add_playback_clips_to_dataframe(
    df: pd.DataFrame,
    drum_track: np.ndarray,
    sample_rate: int | float,
    window_size: float = 1.0,
):
    '''Add larger audio clips for playback to the prediction DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing the prediction results.
        drum_track (np.ndarray): The original drum track audio data.
        sample_rate (int | float): The sample rate of the original drum track.
        window_size (float): The size of the playback window in seconds. Default is 1.0
            seconds.
    '''
    # Need to calculate start and end samples because the sampling rate may have changed
    # due to resampling.
    sample_starts = librosa.time_to_samples(
        df['peak_time'].to_numpy() - (window_size / 2), sr=sample_rate
    )
    sample_starts = np.maximum(sample_starts, 0)
    sample_ends = librosa.time_to_samples(
        df['peak_time'].to_numpy() + (window_size / 2), sr=sample_rate
    )
    sample_ends = np.minimum(sample_ends, len(drum_track))
    playback_clips = [
        drum_track[start:end]
        for start, end in zip(sample_starts, sample_ends, strict=False)
    ]
    df['playback_clip'] = playback_clips
