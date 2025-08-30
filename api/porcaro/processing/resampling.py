'''Module for resampling audio clips in a DataFrame.'''

import numpy as np
import pandas as pd
import librosa


def resample_to_length(
    audio_clip: np.ndarray, target_length: int, sampling_rate: int
) -> tuple[np.ndarray, int | float]:
    '''Resample audio clip to a target length.'''
    original_length = len(audio_clip)
    if original_length == target_length:
        return audio_clip, sampling_rate

    resample_ratio = target_length / original_length
    new_sampling_rate = sampling_rate * resample_ratio
    resampled = librosa.resample(
        audio_clip, orig_sr=sampling_rate, target_sr=new_sampling_rate
    )
    return resampled, new_sampling_rate


def apply_resampling_to_dataframe(df: pd.DataFrame, target_length: int) -> None:
    '''Apply resampling to each audio clip in the DataFrame.'''
    df[['audio_clip', 'sampling_rate']] = df.apply(
        lambda x: pd.Series(
            resample_to_length(x['audio_clip'], target_length, x['sampling_rate'])
        ),
        axis=1,
    )
    df['start_sample'] = df.apply(
        lambda x: librosa.time_to_samples(x['start_time'], sr=x['sampling_rate']),
        axis=1,
    )
    df['end_sample'] = df.apply(
        lambda x: librosa.time_to_samples(x['end_time'], sr=x['sampling_rate']),
        axis=1,
    )
