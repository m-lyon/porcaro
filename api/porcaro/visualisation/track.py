'''Module for visualizing audio tracks using matplotlib and librosa.'''

import numpy as np
import pandas as pd
import librosa.display
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


def plot_track(
    track: np.ndarray,
    sr: int | float,
    start: float = 0,
    stop: float | None = None,
):
    '''Plot the audio track.

    Args:
        track (np.ndarray): The audio track.
        sr (int): The sample rate of the audio track.
        start (float | None): The start time in seconds.
        stop (float | None): The stop time in seconds.

    Returns:
        fig, ax: The matplotlib figure and axis objects.

    '''
    start_sample = librosa.time_to_samples(start, sr=sr)
    stop_sample = librosa.time_to_samples(
        stop if stop is not None else len(track), sr=sr
    )

    fig, ax = plt.subplots(nrows=1, sharex=True, figsize=(20, 5))

    librosa.display.waveshow(track[start_sample:stop_sample], sr=sr, ax=ax)

    return fig, ax


def add_grid(ax: Axes, grid: np.ndarray, colour: str = 'r') -> None:
    '''Add a grid to the plot.

    Args:
        ax (matplotlib.axes.Axes): The axes to add the grid to.
        grid (np.ndarray): The grid to add.
        colour (str): The color of the grid lines.

    '''
    ax.vlines(
        grid,
        ymin=ax.get_ylim()[0],
        ymax=ax.get_ylim()[1],
        color=colour,
        alpha=0.5,
        linestyle='dashed',
        label='Grid',
    )


def add_onsets(
    ax: Axes,
    onsets: pd.Series | np.ndarray,
    colour: str = 'r',
) -> None:
    '''Add onset lines to the plot.

    Args:
        ax (matplotlib.axes.Axes): The axes to add the onsets to.
        onsets (pd.Series | np.ndarray): The onset times in seconds.
        sr (int | float): The sample rate of the audio.
        start (float): The start time in seconds.
        colour (str): The color of the onset lines.

    '''
    if isinstance(onsets, pd.Series):
        onsets = onsets.to_numpy()

    ax.vlines(
        onsets,
        ymin=ax.get_ylim()[0] / 2,
        ymax=ax.get_ylim()[1] / 2,
        color=colour,
        alpha=0.9,
        linestyle='solid',
        label='Onsets',
    )
