import './HomeView.css'

export function HomeView({ uploadedFile, setUploadedFile, textInput, setTextInput, onAnalyze }) {
  const hasInput = uploadedFile || textInput.trim()
  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    setUploadedFile(file || null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) setUploadedFile(file)
  }

  const handleDragOver = (e) => e.preventDefault()

  return (
    <main className="home-view">
      <section className="card upload-card">
        <h2>Upload EEG data</h2>
        <p className="card-desc">Drop a file or click to browse. We'll use it for mental health insights.</p>
        <div
          className={`dropzone ${uploadedFile ? 'has-file' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <input
            type="file"
            id="eeg-upload"
            accept=".edf,.csv,.txt,.json,application/octet-stream"
            onChange={handleFileChange}
            className="dropzone-input"
          />
          <label htmlFor="eeg-upload" className="dropzone-label">
            {uploadedFile ? (
              <span className="file-name">{uploadedFile.name}</span>
            ) : (
              <>Drop EEG file here or <span className="browse">browse</span></>
            )}
          </label>
        </div>
      </section>

      <section className="card text-card">
        <h2>Or share how you feel</h2>
        <p className="card-desc">A few words help us understand your current mood (placeholder analysis).</p>
        <textarea
          className="text-input"
          placeholder="e.g. I've been stressed at work but slept better this week..."
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          rows={4}
        />
      </section>

      <div className="actions">
        <button
          type="button"
          className="btn btn-primary"
          onClick={onAnalyze}
          disabled={!hasInput}
        >
          Analyze
        </button>
      </div>
    </main>
  )
}
