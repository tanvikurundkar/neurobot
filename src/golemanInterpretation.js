/**
 * Plain-language tie-in to Goleman’s emotional-intelligence domains (self-awareness,
 * self-regulation / self-management, motivation, empathy, social skill) for sidebar copy.
 * Aligned with labels from eeg_chatbot_pipeline/goleman_mapping/goleman_state_mapper.py.
 */

const DOMAIN_FRAMING = {
  self_awareness:
    'In Goleman’s model, self-awareness is noticing feelings as they arise — the raw signal before you decide what to do with it.',
  self_regulation:
    'Self-regulation (self-management) is how you channel arousal: calming, refocusing, or recovering after stress — not suppressing emotion, but steering it.',
  motivation:
    'Motivation here means inner drive and engagement — energy pointed toward goals, including small wins on hard days.',
}

const STATE_HINTS = {
  positive_engagement: 'A regulated, engaged state often pairs with steadier attention and approach behaviors.',
  regulated_baseline: 'A neutral baseline can still hold a lot beneath the surface; it is a valid place to work from.',
  low_mood_awareness: 'Naming low mood is already self-awareness — the first step Goleman emphasizes before shifting behavior.',
  stress_dysregulation: 'Under stress, the nervous system prioritizes survival signals; gentle pacing and grounding support regulation.',
  aversive_reactivity: 'Strong aversion can narrow attention; widening the lens (one sensory anchor, one slow breath) supports flexibility.',
  unclassified_emotional_state: 'When the signal is unclear, treat predictions as hypotheses — combine them with how you actually feel.',
}

export function golemanDomainTitle(domain) {
  if (!domain || typeof domain !== 'string') return null
  const d = domain.replace(/_/g, ' ')
  return d.charAt(0).toUpperCase() + d.slice(1)
}

/** @param {Record<string, unknown> | null | undefined} goleman */
export function getGolemanInterpretation(goleman) {
  if (!goleman?.goleman_state) return null
  const domainKey = goleman.goleman_domain
  const domainTitle = golemanDomainTitle(domainKey)
  const domainFrame = domainKey ? DOMAIN_FRAMING[domainKey] : null
  const stateHint = STATE_HINTS[goleman.goleman_state] || STATE_HINTS.unclassified_emotional_state
  const lines = []
  if (domainTitle && domainFrame) {
    lines.push({ kind: 'domain', title: domainTitle, text: domainFrame })
  }
  if (goleman.notes) {
    lines.push({ kind: 'notes', title: 'Signal notes', text: goleman.notes })
  }
  lines.push({ kind: 'state', title: 'What this suggests', text: stateHint })
  return {
    stateLabel: goleman.goleman_state.replace(/_/g, ' '),
    emotion: goleman.emotion,
    confidence: goleman.confidence,
    lines,
  }
}
