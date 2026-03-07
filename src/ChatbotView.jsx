import { useMemo, useState } from 'react'
import './ChatbotView.css'

const STEPS = [
  {
    id: 'overall_mood',
    question: 'Over the last few days, how would you rate your overall mood from 1–10?',
  },
  {
    id: 'emotion_word',
    question: 'If you had to pick one word for how you feel right now (e.g. calm, anxious, hopeful), what would it be?',
  },
  {
    id: 'energy',
    question: 'How has your energy level been lately?',
  },
  {
    id: 'sleep',
    question: 'How have you been sleeping?',
  },
  {
    id: 'stress',
    question: 'What’s been stressing you out the most, if anything?',
  },
]

const initialMessages = [
  {
    id: 'intro-1',
    from: 'bot',
    text: "Hey, I'm Neurobot. I’m here to gently check in on how you’ve been feeling.",
  },
  {
    id: 'intro-2',
    from: 'bot',
    text: STEPS[0].question,
  },
]

export function ChatbotView() {
  const [messages, setMessages] = useState(initialMessages)
  const [stepIndex, setStepIndex] = useState(0)
  const [input, setInput] = useState('')
  const [answers, setAnswers] = useState({})
  const [finished, setFinished] = useState(false)

  const handleReset = () => {
    setMessages(initialMessages)
    setStepIndex(0)
    setInput('')
    setAnswers({})
    setFinished(false)
  }

  const summary = useMemo(() => {
    if (!finished) return null
    const moodRaw = answers.overall_mood
    const moodScore = Number.parseInt(moodRaw, 10)
    const clampedScore = Number.isNaN(moodScore)
      ? null
      : Math.min(10, Math.max(1, moodScore))

    let wellbeingLevel = 'balanced'
    if (clampedScore != null) {
      if (clampedScore >= 8) wellbeingLevel = 'feeling mostly steady'
      else if (clampedScore >= 5) wellbeingLevel = 'in a mixed, in‑between place'
      else wellbeingLevel = 'feeling a bit low'
    }

    const emotionWord = answers.emotion_word

    return {
      moodScore: clampedScore,
      wellbeingLevel,
      emotionWord,
    }
  }, [answers, finished])

  const handleSend = (evt) => {
    evt?.preventDefault()
    if (!input.trim() || finished) return

    const text = input.trim()
    const currentStep = STEPS[stepIndex]
    const nextStepIndex = stepIndex + 1

    const updatedAnswers = {
      ...answers,
      [currentStep.id]: text,
    }

    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        from: 'user',
        text,
      },
    ])
    setAnswers(updatedAnswers)
    setInput('')

    if (nextStepIndex < STEPS.length) {
      const nextStep = STEPS[nextStepIndex]
      setMessages((prev) => [
        ...prev,
        {
          id: `bot-${nextStep.id}`,
          from: 'bot',
          text: nextStep.question,
        },
      ])
      setStepIndex(nextStepIndex)
    } else {
      const moodRaw = updatedAnswers.overall_mood
      const moodScore = Number.parseInt(moodRaw, 10)
      const clampedScore = Number.isNaN(moodScore)
        ? null
        : Math.min(10, Math.max(1, moodScore))

      const emotionWord = updatedAnswers.emotion_word

      const closing = [
        "Thank you for sharing all of that with me.",
        clampedScore != null
          ? `From what you’ve shared, it sounds like your mood has been around ${clampedScore}/10 and you’ve been feeling "${emotionWord || 'how you described'}".`
          : `From what you’ve shared, I’m getting a picture of how things have been feeling for you emotionally.`,
        'This is just a placeholder check‑in — when you plug in real models, this conversation can power a richer mental health dashboard.',
      ]
        .filter(Boolean)
        .join(' ')

      setMessages((prev) => [
        ...prev,
        {
          id: 'bot-summary',
          from: 'bot',
          text: closing,
        },
      ])
      setFinished(true)
    }
  }

  return (
    <main className="chatbot-view">
      <section className="chat-card">
        <div className="chat-header">
          <div className="chat-avatar">N</div>
          <div className="chat-header-text">
            <span className="chat-title">Neurobot</span>
            <span className="chat-subtitle">Emotion check‑in (placeholder)</span>
          </div>
        </div>

        <div className="chat-body">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`chat-row ${m.from === 'user' ? 'chat-row-user' : 'chat-row-bot'}`}
            >
              <div className={`bubble bubble-${m.from}`}>
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
              finished
                ? 'You’ve reached the end of this check‑in.'
                : 'Type your response and hit Enter...'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={finished}
          />
          <button
            type="submit"
            className="btn btn-primary chat-send"
            disabled={!input.trim() || finished}
          >
            Send
          </button>
        </form>
      </section>

      {summary && (
        <section className="summary-card">
          <h3>Your snapshot (fake for now)</h3>
          <p className="summary-main">
            {summary.moodScore != null ? (
              <>
                Based on this quick chat, your mood lands around{' '}
                <span className="summary-highlight">{summary.moodScore}/10</span>, which points to{' '}
                <span className="summary-highlight">{summary.wellbeingLevel}</span>.
              </>
            ) : (
              <>Thanks for walking through this with me — I’ve got a rough picture of where you’re at.</>
            )}
          </p>
          {summary.emotionWord && (
            <p className="summary-secondary">
              The emotion word you used was{' '}
              <span className="summary-highlight">“{summary.emotionWord}”</span>.
            </p>
          )}
          <p className="summary-footnote">
            Hook this up to your sentiment models or EEG pipeline to turn this into a real dashboard.
          </p>
          <button type="button" className="btn btn-ghost summary-reset" onClick={handleReset}>
            Start a new check‑in
          </button>
        </section>
      )}
    </main>
  )
}

