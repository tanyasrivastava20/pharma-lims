import { useState } from 'react'
import { api } from '../services/api.js'
import { useDebounced, useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import { ErrorBox, FieldMsg, Loading, Modal, Pager, Th, orderOf, useSort } from '../components/ui.jsx'
import { ROLES } from '../constants.js'

const FIELDS = [['username', 'Username'], ['full_name', 'Full name'], ['email', 'Email'], ['employee_id', 'Employee ID'], ['department', 'Department']]
const HINT = 'Letters and numbers only, at least 8 characters, with an uppercase letter, a lowercase letter and a number.'

export default function Users() {
  const S = useStore()
  const [q, setQ] = useState(''); const [role, setRole] = useState(''); const [page, setPage] = useState(1); const [sort, onSort] = useSort('username')
  const [edit, setEdit] = useState(null); const [reset, setReset] = useState(null); const [err, setErr] = useState({}); const [busy, setBusy] = useState(false)
  const dq = useDebounced(q)
  const { data, loading, error, reload } = useLoad(() => api.get('/users', { q: dq, role, sort: sort.k, order: orderOf(sort), page, per_page: 25 }), [dq, role, sort.k, sort.dir, page, S.version])

  const run = async (fn, okMsg, close) => {
    setBusy(true)
    try { await fn(); S.notify(okMsg); S.bump(); close(); setErr({}) }
    catch (e) { setErr(e.errors && !Array.isArray(e.errors) ? e.errors : {}); S.notify(e.message, 'err') } finally { setBusy(false) }
  }
  const save = () => {
    const r = edit.row
    const body = { full_name: r.full_name || '', email: r.email || null, employee_id: r.employee_id || null, department: r.department || null, role: r.role, is_active: r.is_active }
    return edit.isNew
      ? run(() => api.post('/users', { ...body, username: r.username || '', password: r.password || '' }), 'User created', () => setEdit(null))
      : run(() => api.put(`/users/${r.id}`, body), 'User updated', () => setEdit(null))
  }
  const remove = async u => {
    if (!window.confirm(`Delete user ${u.username}?`)) return
    try { await api.del(`/users/${u.id}`); S.notify('User deleted'); S.bump() } catch (e) { S.notify(e.message, 'err') }
  }

  return (
    <div className="page">
      <div className="toolbar">
        <input className="search" placeholder="Search username, name, email…" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
        <select value={role} onChange={e => { setRole(e.target.value); setPage(1) }} aria-label="Role filter"><option value="">All roles</option>{ROLES.map(r => <option key={r}>{r}</option>)}</select>
        <button className="btn primary" onClick={() => { setErr({}); setEdit({ isNew: true, row: { role: ROLES[2], is_active: true } }) }}>+ Add user</button>
      </div>
      {error && <ErrorBox message={error} onRetry={reload} />}
      <div className="card"><table className="data">
        <thead><tr><Th k="username" s={sort} on={onSort}>Username</Th><Th k="full_name" s={sort} on={onSort}>Name</Th><Th k="role" s={sort} on={onSort}>Role</Th><th>Department</th><Th k="is_active" s={sort} on={onSort}>Active</Th><th /></tr></thead>
        <tbody>{data && data.items.map(u => (
          <tr key={u.id}><td>{u.username}</td><td>{u.full_name}</td><td>{u.role}</td><td>{u.department}</td><td>{u.is_active ? 'Yes' : 'No'}</td>
            <td className="right"><button className="btn sm" onClick={() => { setErr({}); setEdit({ isNew: false, row: { ...u } }) }}>Edit</button>{' '}
              <button className="btn sm" onClick={() => { setErr({}); setReset({ user: u, password: '' }) }}>Reset password</button>{' '}
              <button className="btn sm danger" onClick={() => remove(u)}>Delete</button></td></tr>))}
        </tbody></table>
        {loading && !data && <Loading />}
      </div>
      {data && <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />}

      {edit && (
        <Modal title={edit.isNew ? 'Add user' : `Edit ${edit.row.username}`} onClose={() => setEdit(null)}
          foot={<><button className="btn primary" disabled={busy} onClick={save}>Save</button><button className="btn" onClick={() => setEdit(null)}>Cancel</button></>}>
          {FIELDS.map(([k, l]) => (
            <div className="row" key={k}><label>{l}</label><div className="ctl"><input name={k} disabled={k === 'username' && !edit.isNew} className={err[k] ? 'bad' : ''}
              value={edit.row[k] || ''} onChange={e => setEdit(x => ({ ...x, row: { ...x.row, [k]: e.target.value } }))} /><FieldMsg err={err} k={k} /></div></div>))}
          {edit.isNew && <div className="row"><label>Password</label><div className="ctl"><input name="password" type="password" className={err.password ? 'bad' : ''}
            value={edit.row.password || ''} onChange={e => setEdit(x => ({ ...x, row: { ...x.row, password: e.target.value } }))} /><FieldMsg err={err} k="password" /><small className="muted">{HINT}</small></div></div>}
          <div className="row"><label>Role</label><div className="ctl"><select name="role" value={edit.row.role} onChange={e => setEdit(x => ({ ...x, row: { ...x.row, role: e.target.value } }))}>{ROLES.map(r => <option key={r}>{r}</option>)}</select><FieldMsg err={err} k="role" /></div></div>
          <div className="row"><label /><div className="ctl"><label className="check"><input name="is_active" type="checkbox" checked={!!edit.row.is_active}
            onChange={e => setEdit(x => ({ ...x, row: { ...x.row, is_active: e.target.checked } }))} /> Active</label><FieldMsg err={err} k="is_active" /></div></div>
        </Modal>)}

      {reset && (
        <Modal title={`Reset password for ${reset.user.username}`} onClose={() => setReset(null)}
          foot={<><button className="btn primary" disabled={busy} onClick={() => run(() => api.post(`/users/${reset.user.id}/reset-password`, { new_password: reset.password }), 'Password reset', () => setReset(null))}>Reset</button><button className="btn" onClick={() => setReset(null)}>Cancel</button></>}>
          <div className="row"><label>New password</label><div className="ctl"><input name="new_password" type="password" className={err.new_password ? 'bad' : ''}
            value={reset.password} onChange={e => setReset(x => ({ ...x, password: e.target.value }))} /><FieldMsg err={err} k="new_password" /><small className="muted">{HINT}</small></div></div>
        </Modal>)}
    </div>
  )
}
