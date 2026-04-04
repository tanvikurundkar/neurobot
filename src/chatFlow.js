/** Mood check-in copy: intro once; support path weaves in coping strategies (Goleman-style self‑regulation ideas). */

export const INTRO_TEXT =
  "Hey — I'm Neurobot. I'll ask a few short questions while your EEG streams in the background. Take your time."

export const QUESTIONS = {
  overall_mood: 'First, how would you rate your overall mood over the last few days, from 1 (very low) to 10 (great)?',
  emotion_word: 'In one word, how would you describe how you feel right now?',
  energy: 'How has your energy been lately — drained, steady, or wired?',
  sleep: 'How has sleep been — falling asleep, staying asleep, waking rested?',
  stress: "What’s been weighing on you most — even if it's small?",
}

/** Coping / regulation strategies shown during the support path (not the happy shortcut). */
export const COPING_STRATEGIES = [
  'Try a slow breath: in for 4 counts, hold for 2, out for 6. That cues your nervous system toward calm.',
  'Name one tiny thing you can control in the next hour — even making tea or a 2‑minute walk counts.',
  'Ground: notice 5 things you see, 4 you feel, 3 you hear. It pulls attention into the present.',
  'If thoughts are looping, label them gently (“worry story”) without fighting them — then shift one small action.',
  'Pair a low mood with one self‑care step: water, light stretch, or texting someone you trust.',
]

export function parseMood1to10(text) {
  const t = text.trim().toLowerCase()
  const wordMap = {
    one: 1,
    two: 2,
    three: 3,
    four: 4,
    five: 5,
    six: 6,
    seven: 7,
    eight: 8,
    nine: 9,
    ten: 10,
  }
  if (wordMap[t] != null) return wordMap[t]
  const m = t.match(/\d{1,2}/)
  if (!m) return null
  const n = parseInt(m[0], 10)
  if (n >= 1 && n <= 10) return n
  return null
}

export function isHappyMood(score) {
  return score != null && score >= 8
}

export function happyClosing(score) {
  return `That’s wonderful to hear${score != null ? ` (${score}/10)` : ''}. Keep smiling, enjoy what you’re doing, and ride that energy. I’ll leave you here — come back anytime you want a longer check‑in.`
}

export function supportClosing(answers) {
  const mood = answers.overall_mood
  const word = answers.emotion_word
  const lines = [
    'Thank you for trusting me with that. You’re not alone in how heavy days can feel.',
    word
      ? `Holding both your mood (“${mood}”) and that feeling (“${word}”) takes courage.`
      : 'Noticing your patterns is already a form of self‑awareness.',
    'Small steps count: one breath, one boundary, one bit of rest. Be gentle with yourself.',
  ]
  return lines.join(' ')
}
