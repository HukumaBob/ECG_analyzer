import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Tooltip, ReferenceLine,
} from 'recharts'
import { useLang } from '../i18n/LangContext'

const DEFAULT_LEADS = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

export default function EcgChart({ ecgData }) {
  const { t } = useLang()
  if (!ecgData || !ecgData.leads || ecgData.leads.length === 0) return null

  const { leads, sample_rate = 100, duration_sec, lead_names = DEFAULT_LEADS } = ecgData

  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 14 }}>
        <h3 style={{ margin: 0, fontSize: 16, color: '#1f2937' }}>{t.ecgTitle}</h3>
        {duration_sec != null && (
          <span style={{ fontSize: 13, color: '#6b7280' }}>
            {duration_sec} {t.ecgSec} · {sample_rate} {t.ecgHz}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {leads.slice(0, 12).map((lead, idx) => {
          const name = lead_names[idx] ?? `L${idx + 1}`
          const data = lead.map((v, i) => ({ t: +(i / sample_rate).toFixed(3), v }))
          const vals = lead.filter(v => isFinite(v))
          const min = Math.min(...vals)
          const max = Math.max(...vals)
          const pad = Math.max((max - min) * 0.15, 0.05)
          const domain = [+(min - pad).toFixed(4), +(max + pad).toFixed(4)]

          return (
            <div key={idx} style={{
              background: '#fffdf7',
              border: '1px solid #fde68a',
              borderRadius: 6,
              padding: '6px 8px 4px',
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#92400e', marginBottom: 2 }}>{name}</div>
              <ResponsiveContainer width="100%" height={90}>
                <LineChart data={data} margin={{ top: 2, right: 4, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#fde68a" vertical={false} />
                  <ReferenceLine y={0} stroke="#fbbf24" strokeWidth={0.8} />
                  <XAxis dataKey="t" hide />
                  <YAxis hide domain={domain} />
                  <Tooltip
                    formatter={v => [`${v} mV`, name]}
                    labelFormatter={tv => `${tv} ${t.ecgSec}`}
                    contentStyle={{ fontSize: 11, padding: '2px 8px' }}
                  />
                  <Line
                    type="monotone" dataKey="v"
                    stroke="#dc2626" dot={false} strokeWidth={1.2}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )
        })}
      </div>

      <p style={{ margin: '10px 0 0', fontSize: 11, color: '#d1d5db', fontStyle: 'italic' }}>
        {t.ecgFooter}
      </p>
    </div>
  )
}
