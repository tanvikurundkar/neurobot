"""
Background LSL reader: resolves EEG stream (e.g. Muse via Muse Lab → LSL), buffers samples,
computes band-power features, optionally runs EmotionModel + GolemanStateMapper.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .eeg_features import band_power_breakdown, downsample_for_plot, features_from_buffer

try:
    from pylsl import StreamInlet, resolve_byprop
except ImportError:
    StreamInlet = None  # type: ignore
    resolve_byprop = None  # type: ignore


def _load_predictors():
    """Returns (emotion_model_or_none, goleman_or_none)."""
    model_path = os.environ.get("EEG_MODEL_PATH", "").strip()
    emotion_model = None
    goleman = None
    if model_path and Path(model_path).is_file():
        try:
            from eeg_chatbot_pipeline.models.emotion_model import EmotionModel

            m = EmotionModel()
            m.load(model_path)
            emotion_model = m
        except Exception as e:
            print(f"[eeg] Could not load EEG model from {model_path}: {e}")
    try:
        from eeg_chatbot_pipeline.goleman_mapping.goleman_state_mapper import GolemanStateMapper

        goleman = GolemanStateMapper()
    except Exception as e:
        print(f"[eeg] Goleman mapper unavailable: {e}")
    return emotion_model, goleman


class LSLWorker:
    def __init__(self, on_snapshot: Callable[[Dict[str, Any]], None]) -> None:
        self._on_snapshot = on_snapshot
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._emotion_model, self._goleman = _load_predictors()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="lsl-eeg", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        if StreamInlet is None or resolve_byprop is None:
            self._emit(
                {
                    "connected": False,
                    "error": "pylsl not installed. pip install pylsl",
                    "samples_in_buffer": 0,
                    "sfreq": None,
                    "channels": None,
                    "emotion": None,
                    "goleman": None,
                    "muse_lsl": None,
                    "waveform": None,
                    "model_loaded": self._emotion_model is not None,
                }
            )
            return

        inlet: Optional[StreamInlet] = None
        buf: Optional[deque] = None
        sfreq = 256.0
        n_ch = 4

        while not self._stop.is_set():
            if inlet is None:
                try:
                    streams = resolve_byprop("type", "EEG", minimum=1, timeout=3.0)
                    if not streams:
                        self._emit(
                            {
                                "connected": False,
                                "error": "No EEG LSL stream found. Start Muse streaming (e.g. Muse Lab) with LSL enabled.",
                                "samples_in_buffer": 0,
                                "sfreq": None,
                                "channels": None,
                                "emotion": None,
                                "goleman": None,
                                "muse_lsl": None,
                                "waveform": None,
                                "model_loaded": self._emotion_model is not None,
                            }
                        )
                        time.sleep(2.0)
                        continue
                    inlet = StreamInlet(streams[0], max_buflen=360)
                    info = inlet.info()
                    sfreq = float(info.nominal_srate()) or 256.0
                    n_ch = int(info.channel_count()) or 4
                    max_samples = int(min(sfreq * 45, 200000))
                    buf = deque(maxlen=max_samples)
                except Exception as e:
                    self._emit(
                        {
                            "connected": False,
                            "error": str(e),
                            "samples_in_buffer": 0,
                            "sfreq": None,
                            "channels": None,
                            "emotion": None,
                            "goleman": None,
                            "muse_lsl": None,
                            "waveform": None,
                            "model_loaded": self._emotion_model is not None,
                        }
                    )
                    time.sleep(2.0)
                    continue

            assert inlet is not None and buf is not None

            try:
                chunk, ts = inlet.pull_chunk(max_samples=256, timeout=0.5)
                if chunk:
                    for row in chunk:
                        buf.append(np.asarray(row, dtype=np.float64))
                else:
                    time.sleep(0.05)
            except Exception as e:
                self._emit(
                    {
                        "connected": True,
                        "error": f"pull_chunk: {e}",
                        "samples_in_buffer": len(buf),
                        "sfreq": sfreq,
                        "channels": n_ch,
                        "emotion": None,
                        "goleman": None,
                        "muse_lsl": None,
                        "waveform": None,
                        "model_loaded": self._emotion_model is not None,
                    }
                )
                time.sleep(0.2)
                continue

            n_need = int(sfreq * 2)
            if len(buf) < n_need:
                self._emit(
                    {
                        "connected": True,
                        "error": None,
                        "samples_in_buffer": len(buf),
                        "sfreq": sfreq,
                        "channels": n_ch,
                        "emotion": None,
                        "goleman": None,
                        "muse_lsl": None,
                        "waveform": None,
                        "model_loaded": self._emotion_model is not None,
                    }
                )
                continue

            data = np.stack(list(buf)[-n_need:], axis=0)
            data = data.T
            if data.shape[0] > 4:
                data = data[:4, :]
            elif data.shape[0] < 4:
                pad = np.zeros((4 - data.shape[0], data.shape[1]))
                data = np.vstack([data, pad])

            feat = features_from_buffer(data, sfreq)
            try:
                muse_lsl = band_power_breakdown(data, sfreq)
            except Exception:
                muse_lsl = None
            try:
                waveform = downsample_for_plot(data, max_points=160)
            except Exception:
                waveform = None
            emotion_payload: Optional[Dict[str, Any]] = None
            goleman_payload: Optional[Dict[str, Any]] = None
            if self._emotion_model is not None:
                try:
                    pred = self._emotion_model.predict(feat)
                    emotion_payload = {
                        "label": pred["label"],
                        "confidence": pred["confidence"],
                        "probabilities": pred.get("probabilities"),
                    }
                    if self._goleman is not None:
                        goleman_payload = self._goleman.map(pred)
                except Exception as e:
                    emotion_payload = {"error": str(e)}

            self._emit(
                {
                    "connected": True,
                    "error": None,
                    "samples_in_buffer": len(buf),
                    "sfreq": sfreq,
                    "channels": n_ch,
                    "emotion": emotion_payload,
                    "goleman": goleman_payload,
                    "muse_lsl": muse_lsl,
                    "waveform": waveform,
                    "model_loaded": self._emotion_model is not None,
                }
            )
            time.sleep(0.8)

    def _emit(self, snap: Dict[str, Any]) -> None:
        try:
            self._on_snapshot(snap)
        except Exception:
            pass
