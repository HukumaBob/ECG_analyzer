import { useState, useRef } from 'react'
import { useLang } from '../i18n/LangContext'

const ACCEPTED_EXTENSIONS = ['.mat', '.csv', '.hea', '.dat']

function validateFiles(fileList, t) {
  const files = Array.from(fileList)
  const invalid = files.filter(f => !ACCEPTED_EXTENSIONS.some(ext => f.name.toLowerCase().endsWith(ext)))
  if (invalid.length > 0) {
    return { ok: false, error: `${t.unsupportedFormat}: ${invalid.map(f => f.name).join(', ')}. ${t.allowedFormats}` }
  }
  const hasHea = files.some(f => f.name.toLowerCase().endsWith('.hea'))
  const hasDat = files.some(f => f.name.toLowerCase().endsWith('.dat'))
  if (hasHea && !hasDat) {
    return { ok: false, error: t.wfdbError }
  }
  return { ok: true }
}

export default function UploadZone({ onFilesSelect, disabled }) {
  const { t } = useLang()
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  function handleFiles(fileList) {
    const files = Array.from(fileList)
    if (files.length === 0) return
    const { ok, error } = validateFiles(files, t)
    if (!ok) { alert(error); return }
    onFilesSelect(files)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    handleFiles(e.dataTransfer.files)
  }

  function handleChange(e) {
    handleFiles(e.target.files)
    e.target.value = ''
  }

  return (
    <div
      style={{
        border: `2px dashed ${dragOver ? '#2563eb' : '#9ca3af'}`,
        borderRadius: 12,
        padding: '32px 24px',
        textAlign: 'center',
        background: dragOver ? '#eff6ff' : '#f9fafb',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.2s',
        opacity: disabled ? 0.6 : 1,
      }}
      onDragOver={e => { e.preventDefault(); if (!disabled) setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
    >
      <div style={{ fontSize: 40, marginBottom: 8 }}>📂</div>
      <p style={{ margin: 0, fontWeight: 600, color: '#374151' }}>{t.dropzone}</p>
      <p style={{ margin: '4px 0 4px', color: '#6b7280', fontSize: 14 }}>{t.dropzoneFormats}</p>
      <p style={{ margin: '0 0 12px', color: '#6b7280', fontSize: 14 }}>{t.dropzoneWfdb}</p>
      <button
        type="button"
        disabled={disabled}
        style={{
          padding: '8px 20px',
          background: '#2563eb',
          color: '#fff',
          border: 'none',
          borderRadius: 6,
          cursor: disabled ? 'not-allowed' : 'pointer',
          fontSize: 14,
          fontWeight: 500,
        }}
      >
        {t.chooseFiles}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".mat,.csv,.hea,.dat"
        multiple
        style={{ display: 'none' }}
        onChange={handleChange}
      />
    </div>
  )
}
