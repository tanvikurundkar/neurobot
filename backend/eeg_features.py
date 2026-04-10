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

BAND_NAMES = ("delta", "theta", "alpha", "beta", "gamma")
# Default Muse 2016 channel order when using Muse Lab → LSL
MUSE_CHANNEL_NAMES = ("TP9", "AF7", "AF8", "TP10")


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


def band_power_breakdown(data: np.ndarray, sfreq: float) -> dict:
    """
    Human-readable band powers for UI (Muse LSL / muselsl-style stats).
    data: (n_channels, n_samples)
    """
    if data.ndim != 2:
        raise ValueError("data must be 2D (channels, samples)")
    n_ch, _ = data.shape
    n_use = min(4, n_ch)
    channels_out = []
    for c in range(n_use):
        sig = data[c].astype(np.float64, copy=False)
        name = MUSE_CHANNEL_NAMES[c] if c < len(MUSE_CHANNEL_NAMES) else f"ch{c + 1}"
        bands_dict = {
            BAND_NAMES[i]: round(bandpower_1d(sig, sfreq, BANDS[i][0], BANDS[i][1]), 4)
            for i in range(len(BANDS))
        }
        channels_out.append({"name": name, "bands": bands_dict})
    return {"channels": channels_out, "band_names": list(BAND_NAMES)}


def downsample_for_plot(data: np.ndarray, max_points: int = 160) -> list[list[float]]:
    """Shape (n_ch, n_samp) → list of channels, each list of max_points amplitudes (µV-scale float)."""
    if data.size == 0:
        return []
    n_ch, n = data.shape
    if n <= max_points:
        return np.asarray(data, dtype=float).tolist()
    idx = np.linspace(0, n - 1, max_points, dtype=int)
    return data[:, idx].astype(float).tolist()


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
