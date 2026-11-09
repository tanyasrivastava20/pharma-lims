import { useState } from 'react'
import { api } from '../services/api.js'
import { useStore } from '../store.jsx'
import { FieldMsg, Modal } from './ui.jsx'

export default function ChangePassword({ onClose }) {
  const S = useStore()
  const [cur, setCur] = useState(''); const [pw, setPw] = useState(''); const [again, setAgain] = useState(''); const [err, setErr] = useState({}); const [busy, setBusy] = useState(false)
  const submit = async () => {
    if (pw !== again) return setErr({ again: 'The two new passwords do not match' })
    setBusy(true)
    try { await api.changePassword(cur, pw); S.notify('Password changed'); onClose() }
    catch (e) { setErr(e.errors && !Array.isArray(e.errors) ? { new_password: e.errors.new_password, current: e.message } : { current: e.message }) } finally { setBusy(false) }
  }
  return (
    <Modal title="Change password" onClose={onClose} foot={<><button className="btn primary" disabled={busy} onClick={submit}>Change</button><button className="btn" onClick={onClose}>Cancel</button></>}>
      <div className="row"><label>Current password</label><div className="ctl"><input name="current" type="password" value={cur} onChange={e => setCur(e.target.value)} /><FieldMsg err={err} k="current" /></div></div>
      <div className="row"><label>New password</label><div className="ctl"><input name="new_password" type="password" value={pw} onChange={e => setPw(e.target.value)} /><FieldMsg err={err} k="new_password" /></div></div>
      <div className="row"><label>Repeat new</label><div className="ctl"><input name="again" type="password" value={again} onChange={e => setAgain(e.target.value)} /><FieldMsg err={err} k="again" /></div></div>
      <small className="muted">Letters and numbers only, at least 8 characters, with an uppercase letter, a lowercase letter and a number.</small>
    </Modal>
  )
}
