import { useState } from 'react'
import { STATUSES } from '../constants.js'

export const today = () => new Date().toISOString().slice(0, 10)
export const fmtDateTime = iso => (iso ? new Date(iso).toLocaleString() : '')
export const Status = ({ s }) => <span className={'badge st' + STATUSES.indexOf(s)}>{s}</span>
// API values can be null; form inputs need ''
export const nullsToBlank = o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v === null ? '' : v]))
const errText = v => (typeof v === 'string' ? v : JSON.stringify(v))
export const FieldMsg = ({ err, k }) => (err && err[k] ? <small className="msg">{errText(err[k])}</small> : null)

export const Row = ({ label, req, children }) => (
  <div className="row"><label>{label}{req && <b className="req"> *</b>}</label><div className="ctl">{children}</div></div>
)

export function Modal({ title, onClose, children, foot }) {
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" role="dialog" aria-label={title} onClick={e => e.stopPropagation()}>
        <div className="modal-head"><b>{title}</b><button className="x" onClick={onClose} aria-label="Close">×</button></div>
        <div className="modal-body">{children}</div>
        {foot && <div className="modal-foot">{foot}</div>}
      </div>
    </div>
  )
}

// code box + "..." button that opens a searchable picker + name box (like the reference screens)
export function Lookup({ rows, code, name, onPick, disabled, bad, field }) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const f = rows.filter(r => (r.code + ' ' + r.name).toLowerCase().includes(q.toLowerCase()))
  return (
    <>
      <input name={field} className={'code' + (bad ? ' bad' : '')} value={code || ''} readOnly />
      <button type="button" className="pick" disabled={disabled} onClick={() => { setQ(''); setOpen(true) }} aria-label="Search">⋯</button>
      <input name={field ? field + '_name' : undefined} className="grow" value={name || ''} readOnly />
      {open && (
        <Modal title="Select" onClose={() => setOpen(false)}>
          <input autoFocus placeholder="Search code or name…" value={q} onChange={e => setQ(e.target.value)} />
          <table className="data"><tbody>
            {f.map(r => <tr key={r.code} className="clickable" onClick={() => { onPick(r); setOpen(false) }}><td>{r.code}</td><td>{r.name}</td></tr>)}
            {!f.length && <tr><td className="empty">No matches</td></tr>}
          </tbody></table>
        </Modal>
      )}
    </>
  )
}

export const useSort = (key, dir = 1) => {
  const [s, setS] = useState({ k: key, dir })
  return [s, k => setS(x => ({ k, dir: x.k === k ? -x.dir : 1 }))]
}
export const orderOf = s => (s.dir > 0 ? 'asc' : 'desc')
export const Th = ({ k, s, on, children }) => (
  <th className="sortable" onClick={() => on(k)}>{children}{s.k === k ? (s.dir > 0 ? ' ▲' : ' ▼') : ''}</th>
)

export const Pager = ({ page, pages, total, onPage }) => (
  <div className="pager">
    <span className="muted">{total} record(s)</span>
    <button className="btn sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
    <span>Page {page} of {pages}</span>
    <button className="btn sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</button>
  </div>
)

export const Loading = () => <p className="empty">Loading…</p>
export const ErrorBox = ({ message, onRetry }) => (
  <div className="note err">{message} {onRetry && <button className="btn sm" onClick={onRetry}>Try again</button>}</div>
)
