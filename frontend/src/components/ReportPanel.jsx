import { useLang } from '../i18n/LangContext'

export default function ReportPanel({ result }) {
  const { lang, t } = useLang()
  if (!result) return null

  const { has_critical, conclusion, conclusion_en, segments_analyzed, device_used, warning, request_id } = result
  const text = lang === 'en' ? (conclusion_en || conclusion) : conclusion

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {has_critical && (
        <div style={{
          background: '#dc2626',
          color: '#fff',
          borderRadius: 10,
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 12,
          boxShadow: '0 4px 12px rgba(220,38,38,0.4)',
          animation: 'pulse 2s infinite',
        }}>
          <span style={{ fontSize: 28, lineHeight: 1 }}>⚠️</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 17, marginBottom: 4 }}>{t.alertTitle}</div>
            <div style={{ fontSize: 14, opacity: 0.9 }}>{t.alertBody}</div>
          </div>
        </div>
      )}

      {warning && (
        <div style={{
          background: '#fef3c7',
          border: '1px solid #fbbf24',
          borderRadius: 8,
          padding: '12px 16px',
          color: '#92400e',
          fontSize: 14,
        }}>
          ⚠ {warning}
        </div>
      )}

      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: 20 }}>
        <h3 style={{ margin: '0 0 12px', fontSize: 16, color: '#1f2937' }}>{t.reportTitle}</h3>
        <pre style={{
          margin: 0,
          fontFamily: 'inherit',
          fontSize: 14,
          lineHeight: 1.7,
          color: '#374151',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}>
          {text}
        </pre>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, color: '#9ca3af', padding: '0 4px' }}>
        <span>{t.segmentsLabel}: <b style={{ color: '#6b7280' }}>{segments_analyzed}</b></span>
        <span>{t.deviceLabel}: <b style={{ color: '#6b7280' }}>{device_used}</b></span>
        <span style={{ marginLeft: 'auto', fontFamily: 'monospace' }}>ID: {request_id?.slice(0, 8)}</span>
      </div>

      <p style={{ margin: 0, fontSize: 11, color: '#d1d5db', fontStyle: 'italic' }}>
        {t.disclaimer}
      </p>
    </div>
  )
}
