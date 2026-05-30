import { useState } from 'react'

const FIELD_STYLE = {
  width: '100%',
  padding: '6px 10px',
  border: '1px solid #d1d5db',
  borderRadius: 6,
  fontSize: 14,
  boxSizing: 'border-box',
}

const LABEL_STYLE = {
  display: 'block',
  fontSize: 13,
  fontWeight: 500,
  color: '#374151',
  marginBottom: 4,
}

export default function MetadataForm({ value, onChange }) {
  const [open, setOpen] = useState(false)

  function update(field, val) {
    onChange({ ...value, [field]: val })
  }

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' }}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%',
          padding: '12px 16px',
          background: '#f3f4f6',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 14,
          fontWeight: 600,
          color: '#374151',
        }}
      >
        <span>Клинические данные (необязательно)</span>
        <span>{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div style={{ padding: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div>
            <label style={LABEL_STYLE}>Возраст</label>
            <input
              type="number"
              min={0}
              max={130}
              placeholder="лет"
              style={FIELD_STYLE}
              value={value.age ?? ''}
              onChange={e => update('age', e.target.value ? Number(e.target.value) : null)}
            />
          </div>

          <div>
            <label style={LABEL_STYLE}>Пол</label>
            <select
              style={FIELD_STYLE}
              value={value.sex ?? ''}
              onChange={e => update('sex', e.target.value || null)}
            >
              <option value="">— не указан —</option>
              <option value="M">Мужской</option>
              <option value="F">Женский</option>
            </select>
          </div>

          <div>
            <label style={LABEL_STYLE}>ЧСС (уд/мин)</label>
            <input
              type="number"
              min={20}
              max={300}
              placeholder="уд/мин"
              style={FIELD_STYLE}
              value={value.heart_rate ?? ''}
              onChange={e => update('heart_rate', e.target.value ? Number(e.target.value) : null)}
            />
          </div>

          <div>
            <label style={LABEL_STYLE}>K⁺ (ммоль/л)</label>
            <input
              type="number"
              step="0.1"
              min={1}
              max={9}
              placeholder="ммоль/л"
              style={FIELD_STYLE}
              value={value.potassium ?? ''}
              onChange={e => update('potassium', e.target.value ? Number(e.target.value) : null)}
            />
          </div>

          <div>
            <label style={LABEL_STYLE}>Mg²⁺ (ммоль/л)</label>
            <input
              type="number"
              step="0.1"
              min={0.3}
              max={3}
              placeholder="ммоль/л"
              style={FIELD_STYLE}
              value={value.magnesium ?? ''}
              onChange={e => update('magnesium', e.target.value ? Number(e.target.value) : null)}
            />
          </div>

          <div>
            <label style={LABEL_STYLE}>Электрокардиостимулятор</label>
            <select
              style={FIELD_STYLE}
              value={value.has_pacemaker === null ? '' : String(value.has_pacemaker)}
              onChange={e => update('has_pacemaker', e.target.value === '' ? null : e.target.value === 'true')}
            >
              <option value="">— не указан —</option>
              <option value="true">Да</option>
              <option value="false">Нет</option>
            </select>
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={LABEL_STYLE}>Препараты (через запятую)</label>
            <input
              type="text"
              placeholder="дигоксин, амиодарон..."
              style={FIELD_STYLE}
              value={(value.medications ?? []).join(', ')}
              onChange={e => update('medications', e.target.value ? e.target.value.split(',').map(s => s.trim()).filter(Boolean) : [])}
            />
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={LABEL_STYLE}>Коды МКБ-10 (через запятую)</label>
            <input
              type="text"
              placeholder="I48, I10..."
              style={FIELD_STYLE}
              value={(value.icd10_codes ?? []).join(', ')}
              onChange={e => update('icd10_codes', e.target.value ? e.target.value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean) : [])}
            />
          </div>
        </div>
      )}
    </div>
  )
}
