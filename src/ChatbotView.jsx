import { useMemo, useState } from 'react'
import {
  COPING_STRATEGIES,
  INTRO_TEXT,
  QUESTIONS,
  happyClosing,
  isHappyMood,
  parseMood1to10,
  supportClosing,
} from './chatFlow'
import { useEegLsl } from './useEegLsl'
import './ChatbotView.css'

const initialMessages = () => [
  { id: 'intro', from: 'bot', text: INTRO_TEXT },
  { id: 'q-overall_mood', from: 'bot', text: QUESTIONS.overall_mood },
]

/** After each answer, which question comes next (support path). */
const NEXT = {
  overall_mood: 'emotion_word',
  emotion_word: 'energy',
  energy: 'sleep',
  sleep: 'stress',
  stress: null,
}

/** Strategy index after completing each step (before showing next question). */
const strategyIndexAfter = {
  overall_mood: 0,
  emotion_word: 1,
  energy: 2,
  sleep: 3,
}

export function ChatbotView() {
  const [messages, setMessages] = useState(initialMessages)
  const [awaiting, setAwaiting] = useState('overall_mood')
  const [input, setInput] = useState('')
  const [answers, setAnswers] = useState({})
  const [finished, setFinished] = useState(false)

  const { snapshot, wsConnected, connect, disconnect } = useEegLsl()

  const handleReset = () => {
    setMessages(initialMessages())
    setAwaiting('overall_mood')
    setInput('')
    setAnswers({})
    setFinished(false)
  }

  const summary = useMemo(() => {
    if (!finished) return null
    const moodRaw = answers.overall_mood
    const moodScore = parseMood1to10(moodRaw ?? '')
    return {
      moodScore,
      emotionWord: answers.emotion_word,
    }
  }, [answers, finished])

  const handleSend = (evt) => {
    evt?.preventDefault()
    if (!input.trim() || finished) return

    const text = input.trim()
    const userMsg = { id: `user-${Date.now()}`, from: 'user', text }
    setInput('')

    setMessages((prev) => [...prev, userMsg])

    const merged = { ...answers, [awaiting]: text }
    setAnswers(merged)

    if (awaiting === 'overall_mood') {
      const score = parseMood1to10(text)
      if (isHappyMood(score)) {
        setMessages((prev) => [
          ...prev,
          {
            id: `bot-happy-${Date.now()}`,
            from: 'bot',
            text: happyClosing(score),
          },
        ])
        setFinished(true)
        return
      }

      const si = strategyIndexAfter.overall_mood
      const strat = COPING_STRATEGIES[si] ?? COPING_STRATEGIES[0]
      const nextKey = NEXT.overall_mood
      setMessages((prev) => [
        ...prev,
        {
          id: `strategy-${si}`,
          from: 'bot',
          variant: 'strategy',
          text: strat,
        },
        {
          id: `q-${nextKey}`,
          from: 'bot',
          text: QUESTIONS[nextKey],
        },
      ])
      setAwaiting(nextKey)
      return
    }

    if (awaiting === 'stress') {
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-close-${Date.now()}`,
          from: 'bot',
          text: supportClosing(merged),
        },
      ])
      setFinished(true)
      return
    }

    const si = strategyIndexAfter[awaiting]
    const strat = si != null ? COPING_STRATEGIES[si] : null
    const nextKey = NEXT[awaiting]
    const nextMsgs = []
    if (strat) {
      nextMsgs.push({
        id: `strategy-${awaiting}-${si}`,
        from: 'bot',
        variant: 'strategy',
        text: strat,
      })
    }
    if (nextKey && QUESTIONS[nextKey]) {
      nextMsgs.push({
        id: `q-${nextKey}`,
        from: 'bot',
        text: QUESTIONS[nextKey],
      })
    }
    setMessages((prev) => [...prev, ...nextMsgs])
    setAwaiting(nextKey || 'stress')
  }

  return (
    <main className="chatbot-view">
      <section className="chat-card">
        <div className="chat-header">
          <div className="chat-avatar">N</div>
          <div className="chat-header-text">
            <span className="chat-title">Neurobot</span>
            <span className="chat-subtitle">Muse · LSL · check-in while EEG streams</span>
          </div>
        </div>

        <div className="chat-body">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`chat-row ${m.from === 'user' ? 'chat-row-user' : 'chat-row-bot'}`}
            >
              <div
                className={`bubble bubble-${m.from} ${m.variant === 'strategy' ? 'bubble-strategy' : ''}`}
              >
                {m.text}
              </div>
            </div>
          ))}
        </div>

        <form className="chat-input-row" onSubmit={handleSend}>
          <input
            type="text"
            className="chat-input"
            placeholder={
              finished ? 'Conversation ended — start a new check-in below.' : 'Type your reply…'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={finished}
          />
          <button type="submit" className="btn btn-primary chat-send" disabled={!input.trim() || finished}>
            Send
          </button>
        </form>
      </section>

      <section className="side-panel">
        {summary && (
          <section className="summary-card">
            <h3>Session snapshot</h3>
            <p className="summary-main">
              {summary.moodScore != null ? (
                <>
                  Mood you reported:{' '}
                  <span className="summary-highlight">{summary.moodScore}/10</span>
                  {summary.emotionWord ? (
                    <>
                      {' '}
                      · word: <span className="summary-highlight">“{summary.emotionWord}”</span>
                    </>
                  ) : null}
                </>
              ) : (
                <>Thanks for completing the check-in.</>
              )}
            </p>
            <p className="summary-footnote">
              EEG labels below come from your pipeline when a model is loaded on the backend (
              <code>EEG_MODEL_PATH</code>).
            </p>
            <button type="button" className="btn btn-ghost summary-reset" onClick={handleReset}>
              Start a new check-in
            </button>
          </section>
        )}

        <section className="eeg-card eeg-live">
          <h3>Live EEG (Muse → LSL)</h3>
          <p className="eeg-desc">
            Stream from Muse Lab (or any LSL EEG outlet with type <code>EEG</code>). Start the backend, then
            connect here; data is processed in Python while you chat.
          </p>
          <div className="eeg-actions">
            {!wsConnected ? (
              <button type="button" className="btn btn-primary eeg-connect-btn" onClick={connect}>
                Connect live stream
              </button>
            ) : (
              <button type="button" className="btn btn-ghost eeg-connect-btn" onClick={disconnect}>
                Disconnect
              </button>
            )}
          </div>
          <dl className="eeg-stats">
            <div>
              <dt>WebSocket</dt>
              <dd>{wsConnected ? 'connected' : 'disconnected'}</dd>
            </div>
            <div>
              <dt>LSL EEG</dt>
              <dd>{snapshot?.connected ? 'receiving' : 'not connected'}</dd>
            </div>
            <div>
              <dt>Sample rate</dt>
              <dd>{snapshot?.sfreq != null ? `${Math.round(snapshot.sfreq)} Hz` : '—'}</dd>
            </div>
            <div>
              <dt>Channels</dt>
              <dd>{snapshot?.channels ?? '—'}</dd>
            </div>
            <div>
              <dt>Buffer</dt>
              <dd>{snapshot?.samples_in_buffer ?? 0} samples</dd>
            </div>
            <div>
              <dt>Model</dt>
              <dd>{snapshot?.model_loaded ? 'loaded' : 'not loaded'}</dd>
            </div>
          </dl>
          {snapshot?.emotion?.error && (
            <p className="eeg-error">
              <strong>Model error:</strong> {snapshot.emotion.error}
            </p>
          )}
          {snapshot?.emotion?.label && !snapshot?.emotion?.error && (
            <p className="eeg-emotion">
              <strong>Emotion (model):</strong> {snapshot.emotion.label}
              {snapshot.emotion.confidence != null && (
                <span className="eeg-conf"> ({(snapshot.emotion.confidence * 100).toFixed(0)}%)</span>
              )}
            </p>
          )}
          {snapshot?.goleman?.goleman_state && (
            <p className="eeg-goleman">
              <strong>Goleman state:</strong> {snapshot.goleman.goleman_state.replace(/_/g, ' ')}
            </p>
          )}
          {snapshot?.error && <p className="eeg-error">{snapshot.error}</p>}
          <p className="eeg-hint">
            Backend: <code>uvicorn backend.main:app --port 8000</code> · optional{' '}
            <code>EEG_MODEL_PATH</code> to your trained <code>EmotionModel</code> joblib.
          </p>
        </section>
      </section>
    </main>
  )
}
