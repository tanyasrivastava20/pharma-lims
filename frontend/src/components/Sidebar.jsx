import { useEffect, useState } from 'react'
import { TREE, TITLES, allowed, flat } from '../nav.js'
import { api } from '../services/api.js'
import { useStore } from '../store.jsx'

// A count of waiting samples is only an alert if this user can do something about it.
const ALERTS = [['Sample Created', 'awaiting receipt', 'receipt'], ['Sample Received', 'awaiting allocation', 'allocation'],
  ['Testing Assigned', 'awaiting testing', 'testing'], ['Analysis Completed', 'awaiting review', 'review']]

export default function Sidebar({ route, go, collapsed, onToggle, recent }) {
  const { user, version } = useStore()
  const [closed, setClosed] = useState({})
  const [counts, setCounts] = useState(null)
  useEffect(() => { api.get('/samples/summary').then(d => setCounts(d.counts)).catch(() => setCounts(null)) }, [version, route])
  const flip = k => setClosed(c => ({ ...c, [k]: !c[k] }))
  const alerts = counts ? ALERTS.filter(([s, , r]) => counts[s] > 0 && allowed(r, user.role)) : []
  const okKids = kids => kids.filter(([, r]) => allowed(r, user.role))
  const quick = TREE.flatMap(t => flat(t)).filter(([, r]) => allowed(r, user.role))

  if (collapsed) return <aside className="sidebar collapsed"><button className="collapse" onClick={onToggle} aria-label="Expand">»</button></aside>
  const Leaf = ([l, r], d = 1) => <li key={r} style={{ paddingLeft: 12 + d * 12 }} className={r === route ? 'active' : ''} onClick={() => go(r)}>{l}</li>
  return (
    <aside className="sidebar">
      <button className="collapse" onClick={onToggle} aria-label="Collapse">«</button>
      <select className="quick" value="" onChange={e => e.target.value && go(e.target.value)} aria-label="Quick links">
        <option value="">Quick Links…</option>
        {quick.map(([l, r]) => <option key={r} value={r}>{l}</option>)}
      </select>
      {TREE.map(t => {
        const items = t.items.map(i => (Array.isArray(i) ? (allowed(i[1], user.role) ? i : null) : (okKids(i.kids).length ? { ...i, kids: okKids(i.kids) } : null))).filter(Boolean)
        if (!items.length) return null
        return (
          <div key={t.title} className="nav-sec">
            <div className="nav-title" onClick={() => flip(t.title)}>{closed[t.title] ? '▸' : '▾'} {t.title}</div>
            {!closed[t.title] && <ul>{items.map(i => Array.isArray(i) ? Leaf(i) : (
              <li key={i.label} className="group"><div onClick={() => flip(i.label)}>{closed[i.label] ? '▸' : '▾'} {i.label}</div>
                {!closed[i.label] && <ul>{i.kids.map(k => Leaf(k, 2))}</ul>}</li>))}</ul>}
          </div>
        )
      })}
      <div className="nav-sec"><div className="nav-title">Recent Items</div>
        <ul>{recent.length ? recent.map(r => Leaf([TITLES[r] || r, r])) : <li className="muted">None yet</li>}</ul></div>
      <div className="nav-sec"><div className="nav-title">Alerts</div>
        <ul>{alerts.length ? alerts.map(([s, t, r]) => <li key={t} onClick={() => go(r)}><span className="dot" />{counts[s]} {t}</li>) : <li className="muted">No alerts</li>}</ul></div>
    </aside>
  )
}
