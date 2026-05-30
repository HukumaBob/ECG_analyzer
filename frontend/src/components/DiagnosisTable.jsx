const PRIORITY_CONFIG = {
  critical: { label: 'Критический', bg: '#fee2e2', color: '#991b1b', badge: '#dc2626' },
  high: { label: 'Высокий', bg: '#fef3c7', color: '#92400e', badge: '#d97706' },
  moderate: { label: 'Умеренный', bg: '#fffbeb', color: '#78350f', badge: '#f59e0b' },
  technical: { label: 'Технический', bg: '#f3f4f6', color: '#374151', badge: '#9ca3af' },
  normal: { label: 'Норма', bg: '#f0fdf4', color: '#166534', badge: '#16a34a' },
}

function ProbBar({ value }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.7 ? '#dc2626' : value >= 0.4 ? '#d97706' : '#6b7280'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 8, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4 }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 600, color, minWidth: 36, textAlign: 'right' }}>
        {pct}%
      </span>
    </div>
  )
}

export default function DiagnosisTable({ diagnoses }) {
  if (!diagnoses || diagnoses.length === 0) return null

  const sorted = [...diagnoses].sort((a, b) => b.probability - a.probability)

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f9fafb' }}>
            <th style={{ padding: '10px 14px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: '#6b7280', borderBottom: '1px solid #e5e7eb' }}>
              Диагноз
            </th>
            <th style={{ padding: '10px 14px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: '#6b7280', borderBottom: '1px solid #e5e7eb', width: 160 }}>
              Вероятность
            </th>
            <th style={{ padding: '10px 14px', textAlign: 'center', fontSize: 13, fontWeight: 600, color: '#6b7280', borderBottom: '1px solid #e5e7eb', width: 110 }}>
              Приоритет
            </th>
            <th style={{ padding: '10px 14px', textAlign: 'center', fontSize: 13, fontWeight: 600, color: '#6b7280', borderBottom: '1px solid #e5e7eb', width: 80 }}>
              Сработал
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((d, idx) => {
            const cfg = PRIORITY_CONFIG[d.priority] ?? PRIORITY_CONFIG.technical
            return (
              <tr
                key={d.label}
                style={{
                  background: d.triggered ? cfg.bg : idx % 2 === 0 ? '#fff' : '#fafafa',
                  borderBottom: '1px solid #f3f4f6',
                }}
              >
                <td style={{ padding: '10px 14px' }}>
                  <div style={{ fontWeight: d.triggered ? 600 : 400, color: '#1f2937', fontSize: 14 }}>
                    {d.label_ru || d.label}
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 1 }}>{d.label}</div>
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <ProbBar value={d.probability} />
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: 12,
                    fontSize: 11,
                    fontWeight: 600,
                    background: cfg.badge + '22',
                    color: cfg.badge,
                    border: `1px solid ${cfg.badge}44`,
                  }}>
                    {cfg.label}
                  </span>
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  {d.triggered
                    ? <span style={{ color: '#dc2626', fontWeight: 700, fontSize: 16 }}>✓</span>
                    : <span style={{ color: '#d1d5db' }}>—</span>
                  }
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
