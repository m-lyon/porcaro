from pedalboard import Compressor
from pedalboard import Pedalboard  # type: ignore

import pandas as pd


def apply_compression_to_dataframe(df: pd.DataFrame) -> None:
    '''Apply compression to each audio clip in the DataFrame.'''

    pb = Pedalboard(
        [Compressor(threshold_db=-27, ratio=4, attack_ms=1, release_ms=200)]
    )

    df['audio_clip'] = df.apply(lambda x: pb(x.audio_clip, x.sampling_rate), axis=1)
