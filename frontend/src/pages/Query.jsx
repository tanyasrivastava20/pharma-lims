import { useState } from 'react'
import { api } from '../services/api.js'
import { useDebounced, useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import CsvTools from '../components/CsvTools.jsx'
import { ErrorBox, Loading, Pager, Status, Th, orderOf, useSort } from '../components/ui.jsx'
import { STATUSES } from '../constants.js'

const COLS = [['lab_no', 'Lab No'], ['material_name', 'Material'], ['batch_no', 'Batch No'], ['supplier_name', 'Supplier'],
  ['quantity', 'Qty'], ['expiry_date', 'Exp. Date'], ['status', 'Status'], ['analyst', 'Analyst']]

export default function Query({ param, go }) {
  const S = useStore()
  const [q, setQ] = useState(''); const [st, setSt] = useState((param && param.status) || ''); const [page, setPage] = useState(1)
  const [sort, onSort] = useSort('lab_no', -1)
  const dq = useDebounced(q)
  const query = { q: dq, status: st, sort: sort.k, order: orderOf(sort) }
  const { data, loading, error, reload } = useLoad(() => api.get('/samples', { ...query, page, per_page: 25 }), [dq, st, sort.k, sort.dir, page, S.version])
  const exportJson = () => {
    const blob = new Blob([JSON.stringify(data.items, null, 2)], { type: 'application/json' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'samples.json'; a.click()
  }
  return (
    <div className="page">
      <div className="toolbar">
        <input className="search" placeholder="Search lab no, material, batch, supplier…" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
        <select value={st} onChange={e => { setSt(e.target.value); setPage(1) }} aria-label="Status filter"><option value="">All statuses</option>{STATUSES.map(s => <option key={s}>{s}</option>)}</select>
        <CsvTools name="samples" exportPath="/export/samples" exportQuery={query} />
        <button className="btn" disabled={!data} onClick={exportJson}>Export JSON (this page)</button>
        <button className="btn" onClick={() => window.print()}>Print</button>
      </div>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <div className="card"><table className="data">
        <thead><tr>{COLS.map(([k, l]) => <Th key={k} k={k} s={sort} on={onSort}>{l}</Th>)}</tr></thead>
        <tbody>{data && data.items.map(s => (
          <tr key={s.id} className="clickable" onClick={() => go('sample/display', s.id)}>
            {COLS.map(([k]) => <td key={k}>{k === 'status' ? <Status s={s.status} /> : k === 'quantity' ? `${s.quantity} ${s.unit}` : s[k]}</td>)}</tr>))}
          {data && !data.items.length && <tr><td className="empty" colSpan={COLS.length}>No samples match.</td></tr>}</tbody></table>
        {loading && !data && <Loading />}
      </div>
      {data && <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />}
    </div>
  )
}
