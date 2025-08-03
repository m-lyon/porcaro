"""Onset detection for drum tracks."""

import logging

import numpy as np
import pandas as pd
import librosa
from pedalboard import Compressor
from pedalboard import Pedalboard  # type: ignore
from librosa.feature import rhythm

from porcaro.utils import SongData
from porcaro.processing.utils import get_note_duration
from porcaro.processing.window import get_fixed_window_size

logger = logging.getLogger(__name__)


def get_librosa_onsets(
    track: np.ndarray,
    sample_rate: int | float,
    hop_length: int,
) -> np.ndarray:
    """Convert onset frames to samples."""
    onset_env = librosa.onset.onset_strength(
        y=track, sr=sample_rate, hop_length=hop_length
    )
    onset_frames = librosa.onset.onset_detect(
        y=track, onset_envelope=onset_env, sr=sample_rate
    )
    onsets = librosa.frames_to_samples(onset_frames * (hop_length / 512))

    return onsets


def _get_onsets(
    track: np.ndarray,
    sample_rate: int | float,
    hop_length: int,
    backtrack: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert onset frames to samples."""
    onset_env = librosa.onset.onset_strength(
        y=track, sr=sample_rate, hop_length=hop_length
    )
    onset_frames = librosa.onset.onset_detect(
        y=track, onset_envelope=onset_env, sr=sample_rate, backtrack=backtrack
    )
    peak_frames = librosa.onset.onset_detect(
        y=track, onset_envelope=onset_env, sr=sample_rate
    )
    onset_samples = librosa.frames_to_samples(onset_frames * (hop_length / 512))
    peak_samples = librosa.frames_to_samples(peak_frames * (hop_length / 512))

    return onset_samples, peak_samples


def _resample(x, target_length):
    org_sr = x['sampling_rate']
    tar_sr_ratio = target_length / len(x['audio_clip'])
    return pd.Series(
        [
            librosa.resample(
                x['audio_clip'], orig_sr=org_sr, target_sr=int(org_sr * tar_sr_ratio)
            ),
            int(org_sr * tar_sr_ratio),
        ]
    )


def get_hit_onsets(
    drum_track: np.ndarray,
    sample_rate: int | float,
    estimated_bpm: float | None = None,
    resolution: int | None = 16,
    fixed_clip_length: bool = False,
    hop_length: int = 1024,
    backtrack: bool = False,
):
    '''Calculates the onsets of drum hits in a given track.

    This function detects and extracts onset from a drum track and format the onsets
    into a df for prediction task

    Args:
        drum_track (np.ndarray): The extracted drum track
        sample_rate (int): The sampling rate of the drum track
        estimated_bpm (int): Beats per minute. It is best to provide a estimated bpm to
            improve the bpm detection accuracy
        resolution (int): Either 8/16/32. Default is 16. Control the window size of the
            onset sound clip if "fixed_clip_length" is not set. 8 means the window size
            equal to the 8th note duration (calculated by the bpm value), etc.
        fixed_clip_length (bool): Default False. Sets window_size of the clip to 0.2
            seconds as default, overriding resolution setting if set to True.
        hop_length (int): Default 1024. 1024 should work in most cases, this value will
            be auto adjusted to 512 if the song is really fast (>110 bpm)
        backtrack (bool): Default False. if True, the detected onset position will roll
            back to the previous local minima to capture the full sound. However, after
            a few testing, this does not work well for drum sound. Only turn this on in
            special cases!

    Returns:
        df (pd.DataFrame): Dataframe containing onsets found in the track
        bpm (float): The estimated bpm value

    '''
    if estimated_bpm is None:
        logger.info(
            'Estimating BPM value from time difference between each detected drum hit'
        )
    if not fixed_clip_length and resolution is None:
        logger.info(
            'Resolution is not set, using 25% quantile value of all time differences '
            'between each detected drum hit'
        )

    onset_samples, peak_samples = _get_onsets(
        drum_track, sample_rate, hop_length, backtrack
    )

    # calculate note duration for 4,8,16,32 note with respect to the bpm of the song
    if estimated_bpm is None:
        eigth_note_len = pd.Series(peak_samples).diff().mode()[0]
        eight_time = librosa.samples_to_time(int(eigth_note_len), sr=int(sample_rate))
        estimated_bpm = float(60.0 / (eight_time * 2.0))

    bpm = rhythm.tempo(y=drum_track, sr=sample_rate, start_bpm=estimated_bpm)[0]

    logger.info(f'Estimated BPM value: {bpm}')
    if bpm > 110:
        logger.info('BPM greater than 110, re-calibrating hop-length to 512')
        onset_samples, peak_samples = _get_onsets(
            drum_track, sample_rate, 512, backtrack
        )
    song_data = SongData(bpm=bpm, sample_rate=sample_rate)
    window_size = get_fixed_window_size(
        resolution if not fixed_clip_length else 0.18, song_data, onset_samples
    )

    if not backtrack:
        padding = librosa.time_to_samples(
            get_note_duration(32, bpm) / 4, sr=sample_rate
        )
    else:
        padding = 0

    # create df for prediction task
    df_dict = {
        'audio_clip': [],
        'sample_start': [],
        'sample_end': [],
        'sampling_rate': [],
    }

    for onset in onset_samples:
        if onset - padding < 0:
            onset = 0
        df_dict['audio_clip'].append(drum_track[onset - padding : onset + window_size])
        df_dict['sample_start'].append(onset - padding)
        df_dict['sample_end'].append(onset + window_size)
        df_dict['sampling_rate'].append(sample_rate)

    df = pd.DataFrame.from_dict(df_dict)
    df['peak_sample'] = pd.Series(peak_samples)

    # check clip length to align with model requirement
    df[['audio_clip', 'sampling_rate']] = df.apply(
        lambda x: _resample(x, 8820)
        if len(x['audio_clip']) != 8820
        else pd.Series([x['audio_clip'], x['sampling_rate']]),
        axis=1,
    )

    pb = Pedalboard(
        [Compressor(threshold_db=-27, ratio=4, attack_ms=1, release_ms=200)]
    )
    df['audio_clip'] = df.apply(lambda x: pb(x.audio_clip, x.sampling_rate), axis=1)

    return df, bpm
