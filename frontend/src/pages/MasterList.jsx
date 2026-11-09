import { useState } from 'react'
import { api } from '../services/api.js'
import { useDebounced, useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import CsvTools from '../components/CsvTools.jsx'
import { ErrorBox, FieldMsg, Loading, Modal, Pager, Th, orderOf, useSort } from '../components/ui.jsx'

export const KINDS = {
  party: { title: 'Party Master', cols: [['code', 'Party Code'], ['name', 'Party Name'], ['city', 'City']] },
  test: { title: 'Test Characteristics', cols: [['code', 'Code'], ['name', 'Characteristic'], ['type', 'Type'], ['unit', 'Unit']] },
  misc: { title: 'Miscellaneous', cols: [['code', 'Code'], ['name', 'Description'], ['group', 'Group']] },
  assay: { title: 'Assay Master', cols: [['code', 'Code'], ['name', 'Assay'], ['method', 'Method'], ['limit', 'Limit']] },
  sampling: { title: 'Sampling Inspection', cols: [['code', 'Code'], ['name', 'Plan name'], ['plan', 'Plan'], ['level', 'Level']] },
  spec: { title: 'Specification Master', cols: [['code', 'Spec Code'], ['name', 'Specification'], ['material', 'Material Code'], ['version', 'Version']] },
}

export default function MasterList({ kind }) {
  const S = useStore(); const cfg = KINDS[kind]; const isAdmin = S.user.role === 'Admin'
  const [q, setQ] = useState(''); const [page, setPage] = useState(1); const [sort, onSort] = useSort('code')
  const [edit, setEdit] = useState(null); const [err, setErr] = useState({}); const [busy, setBusy] = useState(false)
  const dq = useDebounced(q)
  const query = { q: dq, sort: sort.k, order: orderOf(sort) }
  const { data, loading, error, reload } = useLoad(() => api.get(`/master/${kind}`, { ...query, page, per_page: 25 }), [kind, dq, sort.k, sort.dir, page, S.version])

  const save = async () => {
    setBusy(true)
    const body = Object.fromEntries(cfg.cols.map(([k]) => [k, edit.row[k] ?? '']).filter(([k]) => !(k === 'code' && !edit.isNew)))
    try {
      if (edit.isNew) await api.post(`/master/${kind}`, body); else await api.put(`/master/${kind}/${edit.row.id}`, body)
      S.notify('Saved'); S.bump(); setEdit(null); setErr({})
    } catch (e) { setErr(e.errors && !Array.isArray(e.errors) ? e.errors : {}); S.notify(e.message, 'err') } finally { setBusy(false) }
  }
  const remove = async r => {
    if (!window.confirm(`Delete ${r.code}?`)) return
    try { await api.del(`/master/${kind}/${r.id}`); S.notify('Deleted'); S.bump() } catch (e) { S.notify(e.message, 'err') }
  }

  return (
    <div className="page">
      <div className="toolbar">
        <input className="search" placeholder="Search…" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
        {isAdmin && <button className="btn primary" onClick={() => { setErr({}); setEdit({ isNew: true, row: {} }) }}>+ Add</button>}
        <CsvTools name={`master_${kind}`} exportPath={`/export/master/${kind}`} exportQuery={query} importPath={`/import/master/${kind}`} canImport={isAdmin} onImported={reload} />
      </div>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <div className="card"><table className="data">
        <thead><tr>{cfg.cols.map(([k, l]) => <Th key={k} k={k} s={sort} on={onSort}>{l}</Th>)}{isAdmin && <th />}</tr></thead>
        <tbody>
          {data && data.items.map(r => (
            <tr key={r.id}>{cfg.cols.map(([k]) => <td key={k}>{r[k]}</td>)}
              {isAdmin && <td className="right"><button className="btn sm" onClick={() => { setErr({}); setEdit({ isNew: false, row: { ...r } }) }}>Edit</button>{' '}
                <button className="btn sm danger" onClick={() => remove(r)}>Delete</button></td>}</tr>))}
          {data && !data.items.length && <tr><td className="empty" colSpan={cfg.cols.length + 1}>No records</td></tr>}
        </tbody></table>
        {loading && !data && <Loading />}
      </div>
      {data && <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />}
      {edit && (
        <Modal title={(edit.isNew ? 'Add ' : 'Edit ') + cfg.title} onClose={() => setEdit(null)}
          foot={<><button className="btn primary" disabled={busy} onClick={save}>Save</button><button className="btn" onClick={() => setEdit(null)}>Cancel</button></>}>
          {cfg.cols.map(([k, l]) => (
            <div className="row" key={k}><label>{l}</label>
              <div className="ctl"><input name={k} disabled={k === 'code' && !edit.isNew} className={err[k] ? 'bad' : ''} value={edit.row[k] || ''}
                onChange={e => setEdit(x => ({ ...x, row: { ...x.row, [k]: e.target.value } }))} /><FieldMsg err={err} k={k} /></div></div>))}
        </Modal>
      )}
    </div>
  )
}
