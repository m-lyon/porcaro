'''Runs predictions using the Annoteator model.'''

import numpy as np
import torch
import pandas as pd

from porcaro.models.annoteator.module import load_pretrained_model
from porcaro.models.annoteator.dataset import DrumHitPredictDataset


def run_prediction(
    data: pd.DataFrame, sr: int | float, device: str = 'cpu'
) -> pd.DataFrame:
    '''Runs predictions on the provided data using the Annoteator model.

    Args:
        data (pd.DataFrame): DataFrame containing audio clips and metadata.
        sr (int | float): Sampling rate of the audio clips.
        device (str): Device to run the model on ('cpu' or 'cuda').

    Returns:
        pd.DataFrame: DataFrame with predictions added.

    '''
    model = load_pretrained_model().to(device)

    dataset = DrumHitPredictDataset(data, sr)
    data_loader = torch.utils.data.DataLoader(
        dataset, batch_size=32, shuffle=False, pin_memory=True
    )

    predictions = []
    with torch.no_grad():
        for batch in data_loader:
            inputs = batch.to(device)
            outputs = model(inputs)
            # predictions are probabilities, convert them to binary
            # using a threshold of 0.5. If there are no hits in a batch, set the highest
            # probability in each sample to 1.0, otherwise set it to 0.0.
            outputs = outputs.cpu().numpy()
            outputs = np.where(outputs > 0.5, 1.0, 0.0)

            # Vectorized operation to handle cases where no hits are present
            no_hits_mask = np.sum(outputs, axis=1) == 0
            max_indices = np.argmax(outputs, axis=1)
            outputs[no_hits_mask, max_indices[no_hits_mask]] = 1.0

            predictions.append(outputs)

    drum_hits = np.array(['SD', 'HH', 'KD', 'RC', 'TT', 'CC'])
    predictions = np.concatenate(predictions, axis=0)
    masked_hits = np.where(predictions == 1.0, drum_hits, '')
    hits = [row[row != ''].tolist() for row in masked_hits]

    data = data.copy()
    data['hits'] = hits

    return data
