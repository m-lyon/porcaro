'''Dataset for drum hits prediction.'''

import numpy as np
import torch
import pandas as pd
import librosa


class DrumHitPredictDataset(torch.utils.data.Dataset):
    '''Dataset for drum hits.'''

    def __init__(self, data: pd.DataFrame, sr: int | float):
        '''Initialize the DrumHitDataset.

        Args:
            data (pd.DataFrame): DataFrame containing the audio data and labels.
            sr (int): Sample rate of the audio data.

        '''
        self.x = torch.tensor(
            np.stack(
                [
                    librosa.feature.melspectrogram(
                        y=audio_clip, sr=sr, n_mels=128, fmax=8000
                    )
                    for audio_clip in data.audio_clip
                ],
                axis=0,
            ),
            dtype=torch.float32,
        ).unsqueeze(1)

    def __len__(self) -> int:
        '''Return the length of the dataset.'''
        return len(self.x)

    def __getitem__(self, idx: int) -> torch.Tensor:
        '''Get an item from the dataset.

        Args:
            idx (int): Index of the item to retrieve.

        Returns:
            tuple[torch.Tensor, int]: Tuple containing the audio tensor and its label.

        '''
        return self.x[idx]
