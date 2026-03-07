import './DashboardView.css'

export function DashboardView({ result, onBack }) {
  if (!result) return null

  const scoreLabel = result.score >= 70 ? 'Good' : result.score >= 50 ? 'Moderate' : 'Low'
  const scoreColor = result.score >= 70 ? 'var(--blue-mid)' : result.score >= 50 ? 'var(--blue-soft)' : 'var(--grey-mid)'

  return (
    <main className="dashboard-view">
      <div className="dashboard-header">
        <button type="button" className="btn btn-ghost" onClick={onBack}>
          ← Back
        </button>
      </div>

      <h2 className="dashboard-title">Your mental health snapshot</h2>
      <p className="dashboard-subtitle">Placeholder analysis — connect a real backend for accurate insights.</p>

      <section className="dashboard-cards">
        <div className="metric-card main-metric">
          <span className="metric-label">Wellbeing score</span>
          <div className="score-ring" style={{ '--score': result.score, '--score-color': scoreColor }}>
            <span className="score-value">{result.score}</span>
          </div>
          <span className="score-label">{scoreLabel}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Detected sentiment</span>
          <span className="metric-value sentiment">{result.sentiment}</span>
        </div>

        <div className="metric-card sources">
          <span className="metric-label">Data used</span>
          <ul className="source-list">
            {result.hasEeg && <li>EEG upload</li>}
            {result.hasText && <li>Text prompt</li>}
          </ul>
        </div>
      </section>

      <section className="card tips-card">
        <h3>Suggestions</h3>
        <p className="tips-text">
          This is a placeholder dashboard. Once you connect sentiment analysis and EEG processing,
          you'll see personalized insights and recommendations here.
        </p>
      </section>
    </main>
  )
}
