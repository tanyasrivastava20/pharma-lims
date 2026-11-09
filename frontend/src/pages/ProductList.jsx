import { useState } from 'react'
import { api } from '../services/api.js'
import { useDebounced, useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import CsvTools from '../components/CsvTools.jsx'
import { ErrorBox, Loading, Pager, Th, orderOf, useSort } from '../components/ui.jsx'

export default function ProductList({ go }) {
  const S = useStore()
  const [q, setQ] = useState(''); const [page, setPage] = useState(1); const [sort, onSort] = useSort('material_code')
  const dq = useDebounced(q)
  const query = { q: dq, sort: sort.k, order: orderOf(sort) }
  const { data, loading, error, reload } = useLoad(() => api.get('/products', { ...query, page, per_page: 25 }), [dq, sort.k, sort.dir, page, S.version])
  return (
    <div className="page">
      <div className="toolbar">
        <input className="search" placeholder="Search code, name, supplier…" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
        <CsvTools name="products" exportPath="/export/products" exportQuery={query} importPath="/import/products" canImport={S.user.role === 'Admin'} onImported={reload} />
      </div>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <div className="card">
        <table className="data">
          <thead><tr><Th k="material_code" s={sort} on={onSort}>Code</Th><Th k="material_name" s={sort} on={onSort}>Name</Th><Th k="material_type" s={sort} on={onSort}>Type</Th>
            <th>Unit</th><th>Market</th><Th k="retest_period" s={sort} on={onSort}>Retest (months)</Th><th>Supplier</th><th>Obsolete</th></tr></thead>
          <tbody>
            {data && data.items.map(p => (
              <tr key={p.id} className="clickable" onClick={() => go('product/display', p.id)}>
                <td>{p.material_code}</td><td>{p.material_name}</td><td>{p.material_type}</td><td>{p.unit}</td><td>{p.market_name || p.market}</td>
                <td>{p.retest_period}</td><td>{p.supplier_name || p.supplier}</td><td>{p.obsolete ? 'Yes' : ''}</td></tr>))}
            {data && !data.items.length && <tr><td className="empty" colSpan="8">No products found.</td></tr>}
          </tbody></table>
        {loading && !data && <Loading />}
      </div>
      {data && <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />}
    </div>
  )
}
