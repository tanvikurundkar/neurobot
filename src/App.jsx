import { useState } from 'react'
import { HomeView } from './HomeView'
import { DashboardView } from './DashboardView'
import './App.css'

function App() {
  const [view, setView] = useState('home')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [textInput, setTextInput] = useState('')
  const [placeholderResult, setPlaceholderResult] = useState(null)

  const handleAnalyze = () => {
    // Placeholder: fake sentiment analysis
    const hasInput = uploadedFile || textInput.trim()
    if (!hasInput) return

    const sentiments = ['positive', 'neutral', 'calm', 'slightly low', 'balanced']
    const randomSentiment = sentiments[Math.floor(Math.random() * sentiments.length)]
    const score = 40 + Math.floor(Math.random() * 50) // 40–90

    setPlaceholderResult({
      sentiment: randomSentiment,
      score,
      hasEeg: !!uploadedFile,
      hasText: !!textInput.trim(),
    })
    setView('dashboard')
  }

  const handleReset = () => {
    setView('home')
    setUploadedFile(null)
    setTextInput('')
    setPlaceholderResult(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Neurobot</h1>
        <p className="tagline">Mental health insights from EEG &amp; text</p>
      </header>

      {view === 'home' ? (
        <HomeView
          uploadedFile={uploadedFile}
          setUploadedFile={setUploadedFile}
          textInput={textInput}
          setTextInput={setTextInput}
          onAnalyze={handleAnalyze}
        />
      ) : (
        <DashboardView
          result={placeholderResult}
          onBack={handleReset}
        />
      )}
    </div>
  )
}

export default App
