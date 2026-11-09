import { useEffect, useState } from 'react'
import { MENUS, allowed } from '../nav.js'
import { useStore } from '../store.jsx'

export default function Header({ go }) {
  const { user } = useStore()
  const [open, setOpen] = useState(null)
  useEffect(() => { const c = () => setOpen(null); document.addEventListener('click', c); return () => document.removeEventListener('click', c) }, [])
  const toggle = (e, k) => { e.stopPropagation(); setOpen(open === k ? null : k) }
  const pick = r => { setOpen(null); go(r) }
  const menus = Object.entries(MENUS)
    .map(([k, items]) => [k, items.filter(([, r]) => allowed(r, user.role))])
    .filter(([, items]) => items.length)
  return (
    <header className="header">
      <div className="topbar">
        <div className="brand" onClick={() => go('home')}>
          <div className="logo">Rx</div>
          <div><div className="brand-name">PharmaLIMS 4.0</div><div className="brand-sub">Laboratory Information Management</div></div>
        </div>
        <div className="menu-wrap">
          <button className="user-btn" onClick={e => toggle(e, '__user')}>
            <span className="avatar">{user.username[0].toUpperCase()}</span>{user.full_name} <small>({user.role})</small> ▾
          </button>
          {open === '__user' && (
            <ul className="dropdown right">
              <li onClick={() => pick('#password')}>Change password</li>
              <li onClick={() => pick('#theme')}>Toggle dark mode</li>
              <li onClick={() => pick('#logout')}>Sign out</li>
            </ul>
          )}
        </div>
      </div>
      <nav className="menubar">
        <button className="home" onClick={() => go('home')} aria-label="Home">⌂</button>
        {menus.map(([k, items]) => (
          <div className="menu-wrap" key={k}>
            <button className={open === k ? 'on' : ''} onClick={e => toggle(e, k)}>{k}</button>
            {open === k && <ul className="dropdown">{items.map(([l, r]) => <li key={l} onClick={() => pick(r)}>{l}</li>)}</ul>}
          </div>
        ))}
      </nav>
    </header>
  )
}
