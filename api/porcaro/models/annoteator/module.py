'''Annoteator module for PyTorch.'''

from pathlib import Path

import torch

WEIGHTS_PATH = Path(__file__).parent.joinpath('weights.pt')


class AnnoteatorModule(torch.nn.Module):
    '''Annoteator module for PyTorch.'''

    def __init__(self):
        '''Initialize the Annoteator module.'''
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Conv2d(1, 32, kernel_size=3, padding='same'),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=2),
            torch.nn.Conv2d(32, 64, kernel_size=3, padding='same'),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=2),
            torch.nn.Conv2d(64, 64, kernel_size=3, padding='valid'),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=2),
            torch.nn.Flatten(),
            torch.nn.Linear(960, 100),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(100, 100),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(100, 6),
            torch.nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        '''Forward pass through the module.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor after passing through the module.

        '''
        return self.layers(x)


def load_pretrained_model() -> AnnoteatorModule:
    '''Load a pretrained Annoteator model.

    Returns:
        AnnoteatorModule: Loaded Annoteator module.

    '''
    model = AnnoteatorModule()
    model.load_state_dict(torch.load(WEIGHTS_PATH))
    model.eval()
    return model
