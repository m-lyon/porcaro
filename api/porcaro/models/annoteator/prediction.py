'''Runs predictions using the Annoteator model.'''

import numpy as np
import torch
import pandas as pd

from porcaro.models.annoteator.module import load_pretrained_model
from porcaro.models.annoteator.dataset import DrumHitPredictDataset


def run_prediction(
    data: pd.DataFrame, sr: int | float, device: str = 'cpu'
) -> pd.DataFrame:
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

    drum_hits = ['SD', 'HH', 'KD', 'RC', 'TT', 'CC']
    predictions = np.concatenate(predictions, axis=0)
    prediction = pd.DataFrame(predictions, columns=drum_hits)

    data = data.reset_index()
    prediction.reset_index(inplace=True)

    result = data.merge(prediction, left_on='index', right_on='index')
    result.drop(columns=['index'], inplace=True)

    return result
