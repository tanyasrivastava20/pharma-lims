import { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import { useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import { allowed } from '../nav.js'
import { FieldMsg, Lookup, Modal, Row, nullsToBlank } from '../components/ui.jsx'
import { DOSAGE_FORMS, MATERIAL_TYPES, PLANTS, SUBGROUPS, UNITS } from '../constants.js'

const blank = () => ({ plant: PLANTS[0], material_code: '', material_name: '', material_type: MATERIAL_TYPES[0], dosage_form: DOSAGE_FORMS[0],
  subgroup: SUBGROUPS[0], unit: 'kg', market: '', retest_period: 12, color: '', composition: '', supplier: '', manufacturer: '', remarks: '', obsolete: false })
const KEYS = ['plant', 'material_name', 'material_type', 'dosage_form', 'subgroup', 'unit', 'market', 'retest_period', 'color', 'composition',
  'supplier', 'manufacturer', 'remarks', 'obsolete']

export default function ProductMaster({ mode, param, go }) {
  const S = useStore()
  const ro = mode === 'display'
  const [f, setF] = useState(mode === 'create' ? blank() : null)
  const [err, setErr] = useState({}); const [busy, setBusy] = useState(false); const [confirm, setConfirm] = useState(false)
  const products = useLoad(() => (mode === 'create' ? Promise.resolve(null) : api.get('/products', { per_page: 200, sort: 'material_code' })), [S.version])
  const parties = useLoad(() => api.get('/master/party', { per_page: 200 }), [])
  const markets = useLoad(() => api.get('/master/misc', { per_page: 200, group: 'Market' }), [])
  const rows = products.data ? products.data.items : []
  useEffect(() => { if (param && rows.length && !f) setF(nullsToBlank(rows.find(p => p.id === param) || rows[0])) }, [rows.length]) // eslint-disable-line

  const set = (k, v) => setF(x => ({ ...x, [k]: v }))
  const sel = (k, opts) => <select name={k} value={f[k]} disabled={ro} onChange={e => set(k, e.target.value)}>{opts.map(o => <option key={o}>{o}</option>)}</select>
  const txt = (k, p = {}) => <input name={k} value={f[k]} disabled={ro} className={err[k] ? 'bad' : ''} onChange={e => set(k, e.target.value)} {...p} />
  const E = k => <FieldMsg err={err} k={k} />
  const partyRows = parties.data ? parties.data.items : []
  const marketRows = markets.data ? markets.data.items : []
  const nameOf = (list, c) => (list.find(r => r.code === c) || {}).name || ''

  const save = async () => {
    setBusy(true)
    try {
      const payload = Object.fromEntries(KEYS.map(k => [k, f[k]]))
      const saved = mode === 'create' ? await api.post('/products', { ...payload, material_code: f.material_code }) : await api.put(`/products/${f.id}`, payload)
      S.notify(`Product ${saved.material_code} saved`); S.bump(); go('product/display', saved.id)
    } catch (e) { setErr(e.errors && !Array.isArray(e.errors) ? e.errors : {}); S.notify(e.message, 'err') } finally { setBusy(false) }
  }
  const remove = async () => {
    setConfirm(false)
    try { await api.del(`/products/${f.id}`); S.notify(`Product ${f.material_code} deleted`); S.bump(); go('product/list') }
    catch (e) { S.notify(e.message, 'err') }
  }

  return (
    <div className="page">
      <div className="card">
        <Row label="Plant">{f ? sel('plant', PLANTS) : <select disabled />}</Row>
        <Row label="Product/Material Code" req>
          {mode === 'create'
            ? <>{txt('material_code', { className: 'code' + (err.material_code ? ' bad' : '') })}{txt('material_name', { className: 'grow' + (err.material_name ? ' bad' : ''), placeholder: 'Product / material name' })}</>
            : <Lookup field="material_code" rows={rows.map(p => ({ ...p, code: p.material_code, name: p.material_name }))} code={f && f.material_code} name={f && f.material_name}
                onPick={r => { setF(nullsToBlank(r)); setErr({}) }} />}
          {E('material_code')}{E('material_name')}
        </Row>
        {!f ? <p className="empty">Pick a product with the ⋯ button.</p> : (
          <>
            {mode === 'change' && <Row label="Name" req>{txt('material_name')}{E('material_name')}</Row>}
            <Row label="Product/Material Type">{sel('material_type', MATERIAL_TYPES)}
              <label className="inline">Dosage Form</label>{sel('dosage_form', DOSAGE_FORMS)}
              <label className="inline">SubGroup</label>{sel('subgroup', SUBGROUPS)}</Row>
            <Row label="Unit">{sel('unit', UNITS)}</Row>
            <Row label="Market"><Lookup field="market" disabled={ro} rows={marketRows} code={f.market} name={nameOf(marketRows, f.market)} onPick={r => set('market', r.code)} />{E('market')}</Row>
            <Row label="Retest Period">{txt('retest_period', { type: 'number', min: 0, className: 'num' })} Months{E('retest_period')}</Row>
            <Row label="Color">{txt('color')}</Row>
            <Row label="Composition"><textarea name="composition" rows="2" disabled={ro} value={f.composition} onChange={e => set('composition', e.target.value)} /></Row>
            <Row label="Supplier"><Lookup field="supplier" disabled={ro} rows={partyRows} code={f.supplier} name={nameOf(partyRows, f.supplier)} onPick={r => set('supplier', r.code)} />{E('supplier')}</Row>
            <Row label="Manufacturer"><Lookup field="manufacturer" disabled={ro} rows={partyRows} code={f.manufacturer} name={nameOf(partyRows, f.manufacturer)} onPick={r => set('manufacturer', r.code)} />{E('manufacturer')}</Row>
            <Row label="Remark"><textarea name="remarks" rows="2" disabled={ro} value={f.remarks} onChange={e => set('remarks', e.target.value)} /></Row>
            <Row label=""><label className="check"><input name="obsolete" type="checkbox" disabled={ro} checked={f.obsolete} onChange={e => set('obsolete', e.target.checked)} /> Obsolete</label></Row>
          </>
        )}
      </div>
      <div className="actions">
        {!ro && <button className="btn primary" disabled={busy || !f} onClick={save}>{busy ? 'Saving…' : 'Save'}</button>}
        {ro && f && allowed('product/change', S.user.role) && <button className="btn" onClick={() => go('product/change', f.id)}>Edit</button>}
        {mode === 'change' && f && <button className="btn danger" onClick={() => setConfirm(true)}>Delete</button>}
        <button className="btn" onClick={() => go('home')}>{ro ? 'Close' : 'Cancel'}</button>
      </div>
      {confirm && (
        <Modal title="Confirm" onClose={() => setConfirm(false)} foot={<><button className="btn danger" onClick={remove}>Yes, delete</button><button className="btn" onClick={() => setConfirm(false)}>No</button></>}>
          Delete {f.material_code} - {f.material_name}? A material that samples already use can't be deleted; mark it Obsolete instead.
        </Modal>
      )}
    </div>
  )
}
