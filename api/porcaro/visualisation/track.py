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


def add_grid(ax: Axes, grid: np.ndarray, colour: str = 'r', start: float = 0) -> None:
    '''Add a grid to the plot.

    Args:
        ax (matplotlib.axes.Axes): The axes to add the grid to.
        grid (np.ndarray): The grid to add.
        colour (str): The color of the grid lines.
        start (float): The start time in seconds.

    '''
    ax.vlines(
        grid - start,
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
    start: float = 0,
) -> None:
    '''Add onset lines to the plot.

    Args:
        ax (matplotlib.axes.Axes): The axes to add the onsets to.
        onsets (pd.Series | np.ndarray): The onset times in seconds.
        start (float): The start time in seconds.
        colour (str): The color of the onset lines.
        start (float): The start time in seconds.

    '''
    if isinstance(onsets, pd.Series):
        onsets = onsets.to_numpy()

    ax.vlines(
        onsets - start,
        ymin=ax.get_ylim()[0] / 2,
        ymax=ax.get_ylim()[1] / 2,
        color=colour,
        alpha=0.9,
        linestyle='solid',
        label='Onsets',
    )


def add_measures(
    ax: Axes,
    grid: np.ndarray,
    grid_type: str = 'eighth',
    colour: str = 'g',
    start: float = 0,
) -> None:
    '''Add measure lines to the plot.

    Args:
        ax (matplotlib.axes.Axes): The axes to add the measures to.
        measures (np.ndarray): The measure times in seconds.
        start (float): The start time in seconds.
        colour (str): The color of the measure lines.
        start (float): The start time in seconds.

    '''
    if grid_type != 'eighth':
        raise NotImplementedError('Only eighth note grids are supported.')
    # Measures are every 8th note
    grid = grid[::8]
    ax.vlines(
        grid - start,
        ymin=ax.get_ylim()[0],
        ymax=ax.get_ylim()[1],
        color=colour,
        alpha=0.7,
        linestyle='dashdot',
        label='Measures',
    )
