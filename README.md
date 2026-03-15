# Neurobot

Mental health chatbot-style frontend for a mental health dashboard. Right now it’s a **placeholder emotional check-in chat** that you can later wire up to EEG + sentiment analysis.

## Frontend (current)

- **Chatbot** — Neurobot asks a short sequence of questions about mood, emotion word, energy, sleep, and stressors.
- **Chat UI** — Blue/grey, Bree Serif + Verdana, chat bubbles for bot/user.
- **Summary card** — Simple, fake summary based on replies (e.g. mood around X/10) to be replaced with real models later.
- **EEG upload section** — Drag/drop or browse for an EEG file; front-end only so you can attach your own analysis pipeline.

### Run locally

```bash
npm install
npm run dev
```

Open the URL shown (e.g. `http://localhost:5173`). Build for production: `npm run build`; preview: `npm run preview`.

### Stack

- React 18 + Vite
- Bree Serif (headings) + Verdana (body), blue & grey theme
