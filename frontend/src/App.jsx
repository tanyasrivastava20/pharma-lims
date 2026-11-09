import { useEffect, useState } from 'react'
import { SessionProvider, useStore } from './store.jsx'
import { TITLES, allowed } from './nav.js'
import Header from './components/Header.jsx'
import Sidebar from './components/Sidebar.jsx'
import ChangePassword from './components/ChangePassword.jsx'
import { Modal } from './components/ui.jsx'
import Login from './pages/Login.jsx'
import Home from './pages/Home.jsx'
import SampleLogin from './pages/SampleLogin.jsx'
import ProductMaster from './pages/ProductMaster.jsx'
import ProductList from './pages/ProductList.jsx'
import MasterList, { KINDS } from './pages/MasterList.jsx'
import Workflow, { STAGES, Sap } from './pages/Workflow.jsx'
import Query from './pages/Query.jsx'
import Users from './pages/Users.jsx'

function Page({ route, param, go }) {
  const [a, b] = route.split('/')
  if (a === 'home') return <Home go={go} />
  if (a === 'sample') return <SampleLogin key={route + param} mode={b} param={param} go={go} />
  if (a === 'product') return b === 'list' ? <ProductList go={go} /> : <ProductMaster key={route + param} mode={b} param={param} go={go} />
  if (a === 'sap') return <Sap />
  if (a === 'query') return <Query key={JSON.stringify(param)} param={param} go={go} />
  if (a === 'users') return <Users />
  if (a === 'soon') return <div className="page"><p className="empty">The {b} module is not part of this phase yet.</p></div>
  if (STAGES[a]) return <Workflow key={a} stage={a} />
  if (KINDS[a]) return <MasterList key={a} kind={a} />
  return null
}

function Shell() {
  const S = useStore()
  const [route, setRoute] = useState('home'); const [param, setParam] = useState(null)
  const [recent, setRecent] = useState([]); const [collapsed, setCollapsed] = useState(false)
  const [about, setAbout] = useState(false); const [password, setPassword] = useState(false); const [dark, setDark] = useState(false)
  useEffect(() => { document.documentElement.dataset.theme = dark ? 'dark' : 'light' }, [dark])
  useEffect(() => { if (!S.user) { setRoute('home'); setParam(null); setRecent([]) } }, [S.user])

  if (!S.ready) return <p className="empty">Loading…</p>
  if (!S.user) return <Login />

  const go = (r, p = null) => {
    if (r === '#logout') return S.logout()
    if (r === '#about') return setAbout(true)
    if (r === '#theme') return setDark(d => !d)
    if (r === '#password') return setPassword(true)
    setRoute(r); setParam(p)
    if (r !== 'home') setRecent(x => [r, ...x.filter(y => y !== r)].slice(0, 5))
  }
  return (
    <div className="app">
      <Header go={go} />
      <div className="body">
        <Sidebar route={route} go={go} collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} recent={recent} />
        <main className="workspace">
          <div className="titlebar">{TITLES[route] || route}</div>
          {allowed(route, S.user.role) ? <Page route={route} param={param} go={go} /> : <div className="page"><p className="empty">You do not have permission to open this page.</p></div>}
        </main>
      </div>
      <footer className="statusbar"><span>Plant: P003-PIL-III</span><span>{S.user.full_name} ({S.user.role})</span><span>PharmaLIMS 4.0</span></footer>
      {S.toast && <div className={'toast ' + S.toast.type} role="status">{S.toast.msg}</div>}
      {password && <ChangePassword onClose={() => setPassword(false)} />}
      {about && <Modal title="About PharmaLIMS" onClose={() => setAbout(false)}>PharmaLIMS 4.0 - sample login, master data and the lab workflow, connected to the Flask backend.</Modal>}
    </div>
  )
}
export default function App() { return <SessionProvider><Shell /></SessionProvider> }
