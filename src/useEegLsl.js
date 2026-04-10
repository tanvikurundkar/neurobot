import { useCallback, useEffect, useRef, useState } from 'react'

function defaultWsUrl() {
  if (import.meta.env.VITE_EEG_WS_URL) return import.meta.env.VITE_EEG_WS_URL
  if (import.meta.env.DEV && typeof window !== 'undefined') {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    return `${proto}://${window.location.host}/ws-eeg`
  }
  const host = import.meta.env.VITE_EEG_HOST || '127.0.0.1:8000'
  const proto = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${host}/ws/eeg`
}

/**
 * Live EEG snapshot from backend (Muse → LSL → FastAPI). Connect when user clicks Connect.
 */
export function useEegLsl(wsUrl = defaultWsUrl()) {
  const [snapshot, setSnapshot] = useState(null)
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
    setWsConnected(false)
  }, [])

  const connect = useCallback(() => {
    disconnect()
    const ws = new WebSocket(wsUrl)
    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => {
      setWsConnected(false)
      wsRef.current = null
    }
    ws.onerror = () => {}
    ws.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data)
        setSnapshot(d)
      } catch {
        /* ignore */
      }
    }
    wsRef.current = ws
  }, [disconnect, wsUrl])

  useEffect(() => () => disconnect(), [disconnect])

  return { snapshot, wsConnected, connect, disconnect }
}
