"""
FastAPI server: WebSocket /ws/eeg streams live Muse (LSL) EEG status + optional emotion/Goleman predictions.

Run from repo root:
  pip install -r backend/requirements.txt
  export EEG_MODEL_PATH=/path/to/model.joblib   # optional trained EmotionModel
  uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
"""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .lsl_worker import LSLWorker

app = FastAPI(title="Neurobot EEG (LSL)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_snapshot: Dict[str, Any] = {
    "connected": False,
    "error": "Starting…",
    "samples_in_buffer": 0,
    "sfreq": None,
    "channels": None,
    "emotion": None,
    "goleman": None,
    "model_loaded": False,
}
_snapshot_lock = threading.Lock()
_worker: LSLWorker | None = None


def _set_snapshot(update: Dict[str, Any]) -> None:
    global _snapshot
    with _snapshot_lock:
        _snapshot = {**_snapshot, **update}


@app.on_event("startup")
def _startup() -> None:
    global _worker
    _worker = LSLWorker(on_snapshot=_set_snapshot)
    _worker.start()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/eeg/status")
def eeg_status() -> Dict[str, Any]:
    with _snapshot_lock:
        return dict(_snapshot)


@app.websocket("/ws/eeg")
async def ws_eeg(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            with _snapshot_lock:
                payload = dict(_snapshot)
            payload["type"] = "eeg"
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
