import torch
import torch.nn as nn


class Policy(nn.Module):
    """Per-sample action logits (H, A, D) from a whole feature sequence (bidirectional GRU)."""

    def __init__(self, n_features, hidden=64):
        super().__init__()
        self.inp = nn.Sequential(nn.Linear(n_features, hidden), nn.ReLU())
        self.gru = nn.GRU(hidden, hidden, num_layers=2, batch_first=True, bidirectional=True,
                          dropout=0.1)
        self.out = nn.Linear(2 * hidden, 3)

    def forward(self, x):
        h, _ = self.gru(self.inp(x))
        return self.out(h)
