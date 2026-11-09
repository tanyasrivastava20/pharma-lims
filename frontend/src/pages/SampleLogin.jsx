import { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import { allowed } from '../nav.js'
import { FieldMsg, Loading, Lookup, Modal, Row, Status, fmtDateTime, nullsToBlank, today } from '../components/ui.jsx'
import { CATEGORIES, MATERIAL_TYPES, PACKAGING_UNITS, PLANTS, UNITS } from '../constants.js'

const blank = user => ({
  lab_no: '(assigned on save)', plant: PLANTS[0], login_date: today(), material_code: '', material_name: '', supplier: '', supplier_name: '',
  manufacturer: '', manufacturer_name: '', ar_no: '', batch_no: '', sap_batch_no: '', manufacturing_date: '', expiry_date: '',
  material_type: MATERIAL_TYPES[0], category: CATEGORIES[0], sap_lot_no: '', login_by_name: user.full_name, quantity: '', unit: 'kg',
  retest_required: false, packaging: [{ count: 1, quantity: 25, unit: 'Kg' }], status: 'Sample Created', history: [] })

const FIELDS = ['plant', 'login_date', 'material_code', 'supplier', 'manufacturer', 'ar_no', 'batch_no', 'sap_batch_no',
  'manufacturing_date', 'expiry_date', 'material_type', 'category', 'sap_lot_no', 'unit']
const toPayload = f => ({
  ...Object.fromEntries(FIELDS.map(k => [k, f[k]])),
  quantity: f.quantity === '' ? '' : Number(f.quantity), retest_required: f.retest_required,
  packaging: f.packaging.map(p => ({ count: Number(p.count), quantity: Number(p.quantity), unit: p.unit })),
})

export default function SampleLogin({ mode, param, go }) {
  const S = useStore()
  const ro = mode === 'display' || mode === 'delete'
  const [f, setF] = useState(mode === 'create' ? blank(S.user) : null)
  const [err, setErr] = useState({}); const [tab, setTab] = useState('pack'); const [busy, setBusy] = useState(false); const [confirm, setConfirm] = useState(false)
  const products = useLoad(() => api.get('/products', { per_page: 200, obsolete: false, sort: 'material_name' }), [])
  const parties = useLoad(() => api.get('/master/party', { per_page: 200 }), [])
  const list = useLoad(() => (mode === 'create' ? Promise.resolve(null) : api.get('/samples', { per_page: 200, sort: 'lab_no', order: 'desc' })), [S.version])

  const load = async id => {
    if (!id) { setF(null); return }
    try { const s = await api.get(`/samples/${id}`); setF({ ...nullsToBlank(s), packaging: s.packaging, history: s.history }); setErr({}) }
    catch (e) { S.notify(e.message, 'err') }
  }
  useEffect(() => { if (mode !== 'create' && param) load(param) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k, v) => setF(x => ({ ...x, [k]: v }))
  const inp = (k, type = 'text', p = {}) => <input name={k} type={type} value={f[k]} disabled={ro} className={err[k] ? 'bad' : ''} onChange={e => set(k, e.target.value)} {...p} />
  const sel = (k, opts) => <select name={k} value={f[k]} disabled={ro} onChange={e => set(k, e.target.value)}>{opts.map(o => <option key={o}>{o}</option>)}</select>
  const E = k => <FieldMsg err={err} k={k} />
  const productRows = (products.data ? products.data.items : []).map(p => ({ ...p, code: p.material_code, name: p.material_name }))
  const partyRows = parties.data ? parties.data.items : []
  const setPk = (i, k, v) => set('packaging', f.packaging.map((p, j) => (j === i ? { ...p, [k]: v } : p)))
  const packed = f ? f.packaging.reduce((a, p) => a + (Number(p.count) || 0) * (Number(p.quantity) || 0), 0) : 0
  const pkErrors = Object.entries(err).filter(([k]) => k.startsWith('packaging'))

  const save = async () => {
    setBusy(true)
    try {
      const saved = mode === 'create' ? await api.post('/samples', toPayload(f)) : await api.put(`/samples/${f.id}`, toPayload(f))
      S.notify(`Sample ${saved.lab_no} saved`); S.bump(); go('sample/display', saved.id)
    } catch (e) { setErr(e.errors && !Array.isArray(e.errors) ? e.errors : {}); S.notify(e.message, 'err') } finally { setBusy(false) }
  }
  const remove = async () => {
    setConfirm(false)
    try { const d = await api.del(`/samples/${f.id}`); S.notify(`Sample ${d.lab_no} ${d.action}`); S.bump(); go('home') }
    catch (e) { S.notify(e.message, 'err') }
  }

  return (
    <div className="page">
      {mode !== 'create' && (
        <div className="selector"><label>Lab No</label>
          <select name="pick_sample" value={f ? f.id : ''} onChange={e => load(e.target.value)}>
            <option value="">-- Select sample --</option>
            {list.data && list.data.items.map(s => <option key={s.id} value={s.id}>{s.lab_no} - {s.material_name} ({s.status})</option>)}
          </select></div>
      )}
      {!f ? (list.loading ? <Loading /> : <p className="empty">Select a Lab No to continue.</p>) : (
        <>
          <div className="card form2">
            <div>
              <Row label="Plant">{sel('plant', PLANTS)}</Row>
              <Row label="Login Date">{inp('login_date', 'date')}{E('login_date')}</Row>
              <Row label="Lab No"><input name="lab_no" value={f.lab_no} readOnly /></Row>
              <Row label="Material" req>
                <Lookup field="material_code" bad={err.material_code} disabled={ro} rows={productRows} code={f.material_code} name={f.material_name}
                  onPick={r => setF(x => ({ ...x, material_code: r.code, material_name: r.name, unit: r.unit, material_type: r.material_type }))} />{E('material_code')}</Row>
              <Row label="Supplier" req>
                <Lookup field="supplier" bad={err.supplier} disabled={ro} rows={partyRows} code={f.supplier} name={f.supplier_name}
                  onPick={r => setF(x => ({ ...x, supplier: r.code, supplier_name: r.name }))} />{E('supplier')}</Row>
              <Row label="Manufacturer">
                <Lookup field="manufacturer" disabled={ro} rows={partyRows} code={f.manufacturer} name={f.manufacturer_name}
                  onPick={r => setF(x => ({ ...x, manufacturer: r.code, manufacturer_name: r.name }))} />{E('manufacturer')}</Row>
              <Row label="AR No">{inp('ar_no')}{E('ar_no')}</Row>
              <Row label="Batch No" req>{inp('batch_no')}{E('batch_no')}</Row>
              <Row label="SAP Batch No">{inp('sap_batch_no')}</Row>
              <Row label="Mfg. Date">{inp('manufacturing_date', 'date')}{E('manufacturing_date')}</Row>
            </div>
            <div>
              <Row label="Material Type">{sel('material_type', MATERIAL_TYPES)}{E('material_type')}</Row>
              <Row label="Category">{sel('category', CATEGORIES)}</Row>
              <Row label="SAP Lot No">{inp('sap_lot_no')}</Row>
              <Row label="Login By"><input value={f.login_by_name || f.login_by || ''} readOnly /></Row>
              <Row label="Total Qty" req>
                {inp('quantity', 'number', { min: 0, className: 'num' + (err.quantity ? ' bad' : '') })}
                <select name="unit" className="unit" value={f.unit} disabled={ro} onChange={e => set('unit', e.target.value)}>{UNITS.map(u => <option key={u}>{u}</option>)}</select>
                <label className="check"><input name="retest_required" type="checkbox" checked={f.retest_required} disabled={ro} onChange={e => set('retest_required', e.target.checked)} /> Retest</label>{E('quantity')}</Row>
              <Row label="Exp. Date">{inp('expiry_date', 'date')}{E('expiry_date')}</Row>
              <Row label="Status"><Status s={f.status} /></Row>
              {f.analyst && <Row label="Analyst"><input value={f.analyst_name || f.analyst} readOnly /></Row>}
            </div>
          </div>

          <div className="card">
            <div className="tabs">
              <button className={tab === 'pack' ? 'on' : ''} onClick={() => setTab('pack')}>Packaging</button>
              <button className={tab === 'res' ? 'on' : ''} onClick={() => setTab('res')}>Result</button>
              <button className={tab === 'hist' ? 'on' : ''} onClick={() => setTab('hist')}>History</button>
            </div>
            {tab === 'pack' && (
              <>
                <table className="data"><thead><tr><th>No. of containers</th><th>Qty per container</th><th>Unit</th><th /></tr></thead>
                  <tbody>{f.packaging.map((p, i) => (
                    <tr key={i}>
                      <td><input type="number" min="0" disabled={ro} value={p.count} onChange={e => setPk(i, 'count', e.target.value)} /></td>
                      <td><input type="number" min="0" disabled={ro} value={p.quantity} onChange={e => setPk(i, 'quantity', e.target.value)} /></td>
                      <td><select disabled={ro} value={p.unit} onChange={e => setPk(i, 'unit', e.target.value)}>{PACKAGING_UNITS.map(u => <option key={u}>{u}</option>)}</select></td>
                      <td>{!ro && <button className="btn sm" onClick={() => set('packaging', f.packaging.filter((_, j) => j !== i))}>Remove</button>}</td>
                    </tr>))}</tbody></table>
                {pkErrors.map(([k, v]) => <small key={k} className="msg">{k}: {typeof v === 'string' ? v : JSON.stringify(v)}</small>)}
                <div className="actions">
                  {!ro && <button className="btn sm" onClick={() => set('packaging', [...f.packaging, { count: 1, quantity: 25, unit: 'Kg' }])}>+ Add row</button>}
                  <span className={'muted' + (f.quantity !== '' && packed !== Number(f.quantity) ? ' warn' : '')}>Packed {packed} of {f.quantity || 0} {f.unit}</span>
                </div>
              </>
            )}
            {tab === 'res' && <p>{f.result ? f.result : <span className="muted">No result recorded yet.</span>}</p>}
            {tab === 'hist' && (
              <ul className="timeline">{f.history.length ? [...f.history].reverse().map(h => <li key={h.id}><b>{fmtDateTime(h.timestamp)}</b> {h.changed_by_name}: {h.action}</li>) : <li className="muted">No history yet.</li>}</ul>
            )}
          </div>

          <div className="actions">
            {(mode === 'create' || mode === 'change') && <><button className="btn primary" disabled={busy} onClick={save}>{busy ? 'Saving…' : 'Save'}</button><button className="btn" onClick={() => go('home')}>Cancel</button></>}
            {mode === 'delete' && <><button className="btn danger" onClick={() => setConfirm(true)}>Delete / Cancel Sample</button><button className="btn" onClick={() => go('home')}>Back</button></>}
            {mode === 'display' && <>
              {allowed('sample/change', S.user.role) && <button className="btn" onClick={() => go('sample/change', f.id)}>Edit</button>}
              <button className="btn" onClick={() => api.download(`/export/samples/${f.id}`, {}, `sample_${f.lab_no}.pdf`).catch(e => S.notify(e.message, 'err'))}>Download PDF report</button>
              <button className="btn" onClick={() => window.print()}>Print</button></>}
          </div>
        </>
      )}
      {confirm && (
        <Modal title="Confirm" onClose={() => setConfirm(false)} foot={<><button className="btn danger" onClick={remove}>Yes, remove</button><button className="btn" onClick={() => setConfirm(false)}>No</button></>}>
          Remove sample {f.lab_no}? {f.status === 'Sample Created' ? 'It will be deleted.' : 'It will be marked Cancelled.'}
        </Modal>
      )}
    </div>
  )
}
