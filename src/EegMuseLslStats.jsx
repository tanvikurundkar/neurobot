/**
 * Live log-band stats (same feature basis as the emotion model): Muse LSL → pylsl.
 */
export function EegMuseLslStats({ museLsl }) {
  if (!museLsl?.channels?.length) {
    return <p className="eeg-muse-empty">Band powers appear when the LSL buffer has enough samples (~2s).</p>
  }

  const bandNames = museLsl.band_names || ['delta', 'theta', 'alpha', 'beta', 'gamma']

  return (
    <div className="eeg-muse-stats">
      <h4 className="eeg-muse-title">Muse / LSL band power (log)</h4>
      <div className="eeg-muse-scroll">
        <table className="eeg-muse-table">
          <thead>
            <tr>
              <th>Ch</th>
              {bandNames.map((b) => (
                <th key={b}>{b}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {museLsl.channels.map((ch) => (
              <tr key={ch.name}>
                <td>{ch.name}</td>
                {bandNames.map((b) => (
                  <td key={b}>{ch.bands?.[b] ?? '—'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
