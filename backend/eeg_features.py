"""
Band-power features for Muse-like EEG (4 channels × 5 bands = 20 values).
Matches EmotionModel input shape (1, 20) when a trained joblib model is loaded.
"""
from __future__ import annotations

import numpy as np

# Hz bands (Muse ~256 Hz; keep bands within Nyquist)
BANDS = (
    (1.0, 4.0),   # delta
    (4.0, 8.0),   # theta
    (8.0, 13.0),  # alpha
    (13.0, 30.0), # beta
    (30.0, 45.0), # gamma
)


def bandpower_1d(sig: np.ndarray, sfreq: float, fmin: float, fmax: float) -> float:
    """Log-scaled band power for one channel (Welch-like via rFFT + Hann)."""
    n = sig.size
    if n < 8:
        return 0.0
    window = np.hanning(n)
    x = sig * window
    freqs = np.fft.rfftfreq(n, 1.0 / sfreq)
    psd = np.abs(np.fft.rfft(x)) ** 2
    mask = (freqs >= fmin) & (freqs < fmax)
    p = float(np.sum(psd[mask]))
    return float(np.log1p(p))


def features_from_buffer(data: np.ndarray, sfreq: float) -> np.ndarray:
    """
    data: shape (n_channels, n_samples)
    returns shape (1, 20) — 4 channels × 5 bands (padded/truncated to 4 ch).
    """
    if data.ndim != 2:
        raise ValueError("data must be 2D (channels, samples)")
    n_ch, n_samp = data.shape
    n_use = min(4, n_ch)
    out: list[float] = []
    for c in range(n_use):
        sig = data[c].astype(np.float64, copy=False)
        for fmin, fmax in BANDS:
            out.append(bandpower_1d(sig, sfreq, fmin, fmax))
    # pad to 4 channels if fewer
    while len(out) < 20:
        out.extend([0.0] * min(5, 20 - len(out)))
    feat = np.asarray(out[:20], dtype=np.float64).reshape(1, 20)
    return feat
