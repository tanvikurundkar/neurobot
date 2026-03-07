# Neurobot

Mental health dashboard: upload EEG data or answer text prompts; sentiment analysis (placeholder) generates a snapshot.

## Frontend (current)

- **Upload** — Drop or select an EEG file (e.g. `.edf`, `.csv`, `.txt`).
- **Text** — Optional: describe how you feel; used for placeholder “sentiment” analysis.
- **Dashboard** — Placeholder wellbeing score, sentiment, and data sources. Ready to hook up to a real backend.

### Run locally

```bash
npm install
npm run dev
```

Open the URL shown (e.g. `http://localhost:5173`). Build for production: `npm run build`; preview: `npm run preview`.

### Stack

- React 18 + Vite
- Bree Serif (headings) + Verdana (body), blue & grey theme
