# Neurobot

React UI for a **live Muse → LSL → Python** EEG pipeline plus a **guided mood check-in** chat.

- **Chat** — One introduction line from Neurobot (not repeated every turn). If mood is **8–10**, it ends with a short “keep smiling / enjoy what you’re doing” style close. Otherwise it walks through follow-up questions and **weaves in coping strategies** (self-regulation style) between steps, then a supportive closing.
- **Live EEG** — While you talk, start the backend and click **Connect live stream** in the sidebar. The server reads an **LSL stream with `type=EEG`** (e.g. Muse via Muse Lab), buffers samples, computes **band-power features (4 × 5 = 20 values)**, and—if you set `EEG_MODEL_PATH`—runs your trained `EmotionModel` plus `GolemanStateMapper`.

## Frontend

```bash
npm install
npm run dev
```

Open `http://localhost:5173` (or the URL Vite prints).

Optional env:

- `VITE_EEG_WS_URL` — full WebSocket URL (default `ws://127.0.0.1:8000/ws/eeg`).
- `VITE_EEG_HOST` — host:port if you only override the host (default `127.0.0.1:8000`).

## Backend (LSL + FastAPI)

Use a virtualenv (recommended on macOS):

```bash
cd /path/to/neurobot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

Optional: point at a joblib saved from `eeg_chatbot_pipeline/models/emotion_model.py` (`EmotionModel.save(...)`):

```bash
export EEG_MODEL_PATH=/absolute/path/to/your_model.joblib
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Health: `GET http://127.0.0.1:8000/health`  
Snapshot: `GET http://127.0.0.1:8000/eeg/status`  
Live updates: WebSocket `ws://127.0.0.1:8000/ws/eeg`

**Muse:** start streaming with LSL enabled (e.g. Muse Lab) so an EEG outlet appears; the worker resolves `type=EEG` and buffers samples in the background.

## Repo layout (EEG pipeline)

- `eeg_chatbot_pipeline/models/emotion_model.py` — `RandomForestClassifier` wrapper; `predict` expects shape `(1, 20)`.
- `eeg_chatbot_pipeline/goleman_mapping/goleman_state_mapper.py` — maps emotion label to Goleman-style state.
- `backend/eeg_features.py` — band-power features aligned to 20 dims for the default Muse-like 4-channel setup.
- `backend/lsl_worker.py` — LSL inlet thread + optional model + mapper.
- `process/clean_data.py` — offline BIDS cleaning (separate from live LSL).

## Stack

- React 18 + Vite  
- Bree Serif + Verdana, blue/grey UI  
- FastAPI + Uvicorn + pylsl + NumPy + scikit-learn (backend)
