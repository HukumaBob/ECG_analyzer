import { useState, useCallback } from 'react'
import { LangProvider, useLang } from './i18n/LangContext'
import UploadZone from './components/UploadZone'
import MetadataForm from './components/MetadataForm'
import EcgChart from './components/EcgChart'
import DiagnosisTable from './components/DiagnosisTable'
import ReportPanel from './components/ReportPanel'

const EMPTY_META = {
  age: null, sex: null, heart_rate: null,
  medications: [], icd10_codes: [],
  potassium: null, magnesium: null, has_pacemaker: null,
}

function buildMetadataJson(meta) {
  const clean = Object.fromEntries(
    Object.entries(meta).filter(([, v]) => {
      if (v === null || v === undefined) return false
      if (Array.isArray(v) && v.length === 0) return false
      return true
    })
  )
  return Object.keys(clean).length > 0 ? JSON.stringify(clean) : null
}

function AppInner() {
  const { lang, t, toggle } = useLang()
  const [files, setFiles] = useState([])
  const [meta, setMeta] = useState(EMPTY_META)
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [ecgPreview, setEcgPreview] = useState(null)
  const [error, setError] = useState(null)

  const handleFilesSelect = useCallback((fileList) => {
    setFiles(fileList)
    setResult(null)
    setEcgPreview(null)
    setError(null)
    setStatus('idle')
  }, [])

  async function handleAnalyze() {
    if (files.length === 0) return
    setStatus('loading')
    setResult(null)
    setEcgPreview(null)
    setError(null)

    try {
      const formData = new FormData()
      for (const f of files) formData.append('files', f)
      const metaJson = buildMetadataJson(meta)
      if (metaJson) formData.append('metadata_json', metaJson)

      const res = await fetch('/api/v1/analyze', { method: 'POST', body: formData })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(errData.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      setResult(data)
      if (data.ecg_preview) setEcgPreview(data.ecg_preview)
      setStatus('done')
    } catch (e) {
      setError(e.message)
      setStatus('error')
    }
  }

  function handleReset() {
    setFiles([])
    setMeta(EMPTY_META)
    setResult(null)
    setEcgPreview(null)
    setError(null)
    setStatus('idle')
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{
        background: '#1e40af',
        color: '#fff',
        padding: '14px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}>
        <span style={{ fontSize: 26 }}>🫀</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: 18, lineHeight: 1.2 }}>{t.appTitle}</div>
          <div style={{ fontSize: 12, opacity: 0.75 }}>{t.appSubtitle}</div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          {status === 'done' && (
            <button
              onClick={handleReset}
              style={{
                padding: '6px 14px',
                background: 'rgba(255,255,255,0.15)',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.3)',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              {t.newAnalysis}
            </button>
          )}
          <button
            onClick={toggle}
            title={lang === 'ru' ? 'Switch to English' : 'Переключить на русский'}
            style={{
              padding: '5px 12px',
              background: 'rgba(255,255,255,0.15)',
              color: '#fff',
              border: '1px solid rgba(255,255,255,0.3)',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: '0.03em',
            }}
          >
            {lang === 'ru' ? 'EN' : 'RU'}
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 900, margin: '0 auto', padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: 20 }}>

        {status !== 'done' && (
          <div style={{ background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', display: 'flex', flexDirection: 'column', gap: 16 }}>
            <h2 style={{ margin: 0, fontSize: 16, color: '#1f2937' }}>{t.uploadTitle}</h2>

            <UploadZone onFilesSelect={handleFilesSelect} disabled={status === 'loading'} />

            {files.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, padding: '8px 12px', background: '#eff6ff', borderRadius: 6, fontSize: 13, color: '#1e40af' }}>
                {files.map(f => (
                  <div key={f.name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span>📄</span>
                    <span style={{ fontWeight: 500 }}>{f.name}</span>
                    <span style={{ color: '#6b7280' }}>({(f.size / 1024).toFixed(1)} KB)</span>
                  </div>
                ))}
              </div>
            )}

            <MetadataForm value={meta} onChange={setMeta} />

            <button
              onClick={handleAnalyze}
              disabled={files.length === 0 || status === 'loading'}
              style={{
                padding: '12px',
                background: files.length > 0 && status !== 'loading' ? '#2563eb' : '#93c5fd',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                fontSize: 15,
                fontWeight: 600,
                cursor: files.length > 0 && status !== 'loading' ? 'pointer' : 'not-allowed',
                transition: 'background 0.2s',
              }}
            >
              {status === 'loading' ? t.analyzingBtn : t.analyzeBtn}
            </button>

            {status === 'loading' && (
              <p style={{ margin: 0, textAlign: 'center', color: '#6b7280', fontSize: 13 }}>
                {t.analyzingHint}
              </p>
            )}
          </div>
        )}

        {status === 'error' && (
          <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 10, padding: '14px 18px', color: '#991b1b', fontSize: 14 }}>
            <b>{t.errorLabel}:</b> {error}
          </div>
        )}

        {status === 'done' && result && (
          <>
            <ReportPanel result={result} />
            <DiagnosisTable diagnoses={result.diagnoses} />
            {ecgPreview && <EcgChart ecgData={ecgPreview} />}
          </>
        )}

      </main>
    </div>
  )
}

export default function App() {
  return (
    <LangProvider>
      <AppInner />
    </LangProvider>
  )
}
