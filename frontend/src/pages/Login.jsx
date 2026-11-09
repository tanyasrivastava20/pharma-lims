import { useState } from 'react'
import { useStore } from '../store.jsx'

export default function Login() {
  const S = useStore()
  const [u, setU] = useState(''); const [p, setP] = useState(''); const [busy, setBusy] = useState(false)
  const submit = async e => {
    e.preventDefault()
    if (!u.trim() || !p) return S.notify('Enter your username and password', 'err')
    setBusy(true)
    try { await S.login(u.trim(), p) } catch (err) { S.notify(err.message, 'err') } finally { setBusy(false) }
  }
  return (
    <div className="login-wrap">
      <form className="login card" onSubmit={submit}>
        <div className="logo big">Rx</div><h2>PharmaLIMS 4.0</h2>
        <label>Username<input name="username" value={u} onChange={e => setU(e.target.value)} autoFocus autoComplete="username" /></label>
        <label>Password<input name="password" type="password" value={p} onChange={e => setP(e.target.value)} autoComplete="current-password" /></label>
        <button className="btn primary" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
      </form>
      {S.toast && <div className={'toast ' + S.toast.type} role="status">{S.toast.msg}</div>}
    </div>
  )
}
