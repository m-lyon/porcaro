'''Visualisation functions for audio processing.'''

import numpy as np
import pandas as pd
import librosa
import matplotlib.pyplot as plt


def plot_onset_on_track(
    track: np.ndarray,
    sr: int | float,
    onset: pd.Series | np.ndarray,
    start: float = 0,
    stop: float | None = None,
    _8: None | np.ndarray = None,
    _16: None | np.ndarray = None,
    _32: None | np.ndarray = None,
    _8_3: None | np.ndarray = None,
    _8_6: None | np.ndarray = None,
):
    '''Plot the onsets on the audio track.

    Args:
        track (np.ndarray): The audio track.
        sr (int): The sample rate of the audio track.
        onset (pd.Series | np.ndarray): The onset time in samples.
        start (float | None): The start time in seconds.
        stop (float | None): The stop time in seconds.
        _8 (None | np.ndarray): 8th notes in samples. Default is None.
        _16 (None | np.ndarray): 16th notes in samples. Default is None.
        _32 (None | np.ndarray): 32nd notes in samples. Default is None.
        _8_3 (None | np.ndarray): 8th triplet notes in samples. Default is None.
        _8_6 (None | np.ndarray): 8th sixlet notes in samples. Default is None.

    Returns:
        fig, ax: The matplotlib figure and axis objects.

    '''
    start_sample = librosa.time_to_samples(start, sr=sr)
    stop_sample = librosa.time_to_samples(stop if stop is not None else len(track), sr=sr)

    fig, ax = plt.subplots(nrows=1, sharex=True, figsize=(20, 5))

    librosa.display.waveshow(track[start_sample:stop_sample], sr=sr, ax=ax)

    ymin = min(ax.get_ylim())
    ymax = max(ax.get_ylim())

    onset_line = onset
    onset_line = onset_line - start_sample  # type: ignore
    onset_line = pd.Series(onset_line).apply(lambda x: librosa.samples_to_time(x, sr=sr))

    ax.vlines(onset_line, ymin, ymax, color='r', alpha=0.9, linestyle='solid', label='Onsets')

    if _8 is not None:
        _8_line = _8
        _8_line = _8_line - start
        ax.vlines(
            pd.Series(_8_line),
            ymin,
            ymax,
            color='darkorange',
            alpha=1,
            linestyle='--',
            label='8th notes',
        )

    if _16 is not None:
        _16_line = _16
        _16_line = _16_line - start
        ax.vlines(
            pd.Series(_16_line),
            ymin,
            ymax,
            color='royalblue',
            alpha=1,
            linestyle='--',
            label='16th notes',
        )

    if _32 is not None:
        _32_line = _32
        _32_line = _32_line - start
        ax.vlines(
            pd.Series(_32_line),
            ymin,
            ymax,
            color='green',
            alpha=1,
            linestyle='--',
            label='32th notes',
        )

    if _8_3 is not None:
        _8_3_line = _8_3
        _8_3_line = _8_3_line - start
        ax.vlines(
            pd.Series(_8_3_line),
            ymin,
            ymax,
            color='darkviolet',
            alpha=1,
            linestyle='dotted',
            label='8th triplet notes',
        )

    if _8_6 is not None:
        _8_6_line = _8_6
        _8_6_line = _8_6_line - start
        ax.vlines(
            pd.Series(_8_6_line),
            ymin,
            ymax,
            color='darkviolet',
            alpha=1,
            linestyle='dotted',
            label='8th sixlet notes',
        )

    ax.legend()

    return fig, ax
