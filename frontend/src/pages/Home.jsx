import { api } from '../services/api.js'
import { useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import { allowed } from '../nav.js'
import { ErrorBox, Loading } from '../components/ui.jsx'
import { STATUSES } from '../constants.js'

export default function Home({ go }) {
  const { user, version } = useStore()
  const { data, loading, error, reload } = useLoad(() => api.get('/samples/summary'), [version])
  const can = r => allowed(r, user.role)
  return (
    <div className="page">
      {error && <ErrorBox message={error} onRetry={reload} />}
      {loading && !data && <Loading />}
      {data && (
        <div className="cards">
          {STATUSES.map((s, i) => (
            <button key={s} className={'stat st' + i} onClick={() => go('query', { status: s })}>
              <b>{data.counts[s]}</b><span>{s}</span>
            </button>
          ))}
        </div>)}
      <div className="card"><h3>Quick actions</h3>
        <div className="actions">
          {can('sample/create') && <button className="btn primary" onClick={() => go('sample/create')}>+ New Sample Login</button>}
          {can('product/create') && <button className="btn" onClick={() => go('product/create')}>+ New Product/Material</button>}
          {can('receipt') && <button className="btn" onClick={() => go('receipt')}>Sample Receipt</button>}
          {can('review') && <button className="btn" onClick={() => go('review')}>Review &amp; Approve</button>}
          <button className="btn" onClick={() => go('query')}>Sample Query</button>
        </div>
      </div>
    </div>
  )
}
