import { useEffect, useRef } from 'react'

const COLORS = ['#2d6a8f', '#4a90c2', '#7eb8da', '#1a4a66']

/**
 * In-browser “stream view” for Muse → LSL: downsampled µV traces (last ~2s window from backend).
 * @param {number[][] | null | undefined} waveform — channels × samples
 */
export function EegWaveform({ waveform }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !waveform?.length) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const w = canvas.width
    const h = canvas.height
    ctx.fillStyle = '#f4f8fb'
    ctx.fillRect(0, 0, w, h)
    ctx.strokeStyle = '#dce8f0'
    ctx.lineWidth = 1
    for (let i = 1; i < 4; i++) {
      const y = (h / 4) * i
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(w, y)
      ctx.stroke()
    }
    const nCh = waveform.length
    const rowH = h / Math.max(nCh, 1)
    waveform.forEach((row, ci) => {
      if (!row?.length) return
      const mid = rowH * (ci + 0.5)
      const min = Math.min(...row)
      const max = Math.max(...row)
      const span = Math.max(max - min, 1e-9)
      ctx.strokeStyle = COLORS[ci % COLORS.length]
      ctx.lineWidth = 1.5
      ctx.beginPath()
      row.forEach((v, i) => {
        const x = (i / (row.length - 1)) * w
        const y = mid - ((v - min) / span - 0.5) * rowH * 0.85
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.stroke()
    })
  }, [waveform])

  if (!waveform?.length) {
    return <p className="eeg-waveform-empty">Connect the stream to see a live trace (browser “muselsl-style” view).</p>
  }

  return (
    <div className="eeg-waveform-wrap">
      <canvas ref={canvasRef} className="eeg-waveform-canvas" width={320} height={140} />
      <p className="eeg-waveform-legend">TP9 · AF7 · AF8 · TP10 (typical Muse order)</p>
    </div>
  )
}
