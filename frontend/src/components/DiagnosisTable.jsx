import { useLang } from '../i18n/LangContext'

const PRIORITY_CONFIG = {
  critical: { bg: '#fee2e2', color: '#991b1b', badge: '#dc2626' },
  high:     { bg: '#fef3c7', color: '#92400e', badge: '#d97706' },
  moderate: { bg: '#fffbeb', color: '#78350f', badge: '#f59e0b' },
  technical:{ bg: '#f3f4f6', color: '#374151', badge: '#9ca3af' },
  normal:   { bg: '#f0fdf4', color: '#166534', badge: '#16a34a' },
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
  const { lang, t } = useLang()
  if (!diagnoses || diagnoses.length === 0) return null

  const sorted = [...diagnoses].sort((a, b) => b.probability - a.probability)

  const PRIORITY_LABELS = {
    critical:  t.priorityCritical,
    high:      t.priorityHigh,
    moderate:  t.priorityModerate,
    technical: t.priorityTechnical,
    normal:    t.priorityNormal,
  }

  const TH = { padding: '10px 14px', textAlign: 'left', fontSize: 13, fontWeight: 600, color: '#6b7280', borderBottom: '1px solid #e5e7eb' }

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f9fafb' }}>
            <th style={TH}>{t.colDiagnosis}</th>
            <th style={{ ...TH, width: 160 }}>{t.colProbability}</th>
            <th style={{ ...TH, textAlign: 'center', width: 110 }}>{t.colPriority}</th>
            <th style={{ ...TH, textAlign: 'center', width: 80 }}>{t.colTriggered}</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((d, idx) => {
            const cfg = PRIORITY_CONFIG[d.priority] ?? PRIORITY_CONFIG.technical
            const name = lang === 'en' ? (d.label_en || d.label) : (d.label_ru || d.label)
            const subname = lang === 'en' ? d.label : d.label_en
            return (
              <tr
                key={d.label}
                style={{
                  background: d.triggered ? cfg.bg : idx % 2 === 0 ? '#fff' : '#fafafa',
                  borderBottom: '1px solid #f3f4f6',
                }}
              >
                <td style={{ padding: '10px 14px' }}>
                  <div style={{ fontWeight: d.triggered ? 600 : 400, color: '#1f2937', fontSize: 14 }}>{name}</div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 1 }}>{subname}</div>
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
                    {PRIORITY_LABELS[d.priority] ?? d.priority}
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
