'''Extract the drum track from a given audio file using Demucs.'''

import logging
import multiprocessing
from pathlib import Path

import numpy as np
import torch
import librosa
from demucs import apply
from demucs import audio
from demucs import pretrained

from porcaro.models.demucs import MODELS
from porcaro.models.demucs import MODEL_DIRPATH

logger = logging.getLogger(__name__)


def extract_drums_demucs(
    fpath: str | Path,
    device: str = "cpu",
    progress_bar: bool = True,
    drum_start: int | None = None,
    drum_end: int | None = None,
) -> tuple[np.ndarray, int]:
    '''Extract the drum track from a given audio file using Demucs.

    Args:
        fpath (str | Path): Path to the audio file.
        device (str): Device to use for processing. Default is "cpu".
        progress_bar (bool): Whether to show a progress bar. Default is True.
        drum_start (int | None): Start time for the drum extraction in seconds.
            Default is None.
        drum_end (int | None): End time for the drum extraction in seconds. Default
            is None.

    Returns:
        None

    '''
    sub_models: list[apply.Model] = [
        pretrained.get_model(name=model, repo=MODEL_DIRPATH) for model in MODELS
    ]  # type: ignore
    model = apply.BagOfModels(sub_models)
    # assert that drum_start and drum_end are either both None or both not None
    if (drum_start is None) != (drum_end is None):
        raise ValueError("drum_start and drum_end must be either both None or both not None")
    duration = drum_end - drum_start if drum_end is not None and drum_start is not None else None
    wav = audio.AudioFile(Path(fpath)).read(
        streams=0,  # type: ignore
        samplerate=model.samplerate,
        channels=model.audio_channels,
        seek_time=drum_start,
        duration=duration,
    )

    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()
    sources = apply.apply_model(
        model,
        wav.unsqueeze(0),
        device=device,
        shifts=1,
        split=True,
        overlap=0.25,
        progress=progress_bar,
        num_workers=multiprocessing.cpu_count() if device == "cpu" else 0,
    )
    assert isinstance(sources, torch.Tensor)

    sources = sources[0] * ref.std() + ref.mean()
    drum = sources[0]
    sample_rate = model.samplerate
    drum_track = librosa.to_mono(drum.numpy())

    return drum_track, sample_rate
