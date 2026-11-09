import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, hasToken, setUnauthorizedHandler } from './services/api.js'

const Ctx = createContext(null)
export const useStore = () => useContext(Ctx)

// Who is signed in, the pop-up message, and a counter that tells pages to refresh after a change.
export function SessionProvider({ children }) {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(!hasToken())
  const [toast, setToast] = useState(null)
  const [version, setVersion] = useState(0)

  const notify = useCallback((msg, type = 'ok') => {
    setToast({ msg, type })
    setTimeout(() => setToast(t => (t && t.msg === msg ? null : t)), 3500)
  }, [])
  const bump = useCallback(() => setVersion(v => v + 1), [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      api.clearSession(); setUser(null); notify('Your session has ended. Please sign in again.', 'err')
    })
    if (hasToken()) {
      api.me().then(setUser).catch(() => api.clearSession()).finally(() => setReady(true))
    }
  }, [notify])

  const value = {
    user, ready, toast, notify, version, bump,
    login: async (username, password) => setUser(await api.login(username, password)),
    logout: async () => { await api.logout(); setUser(null) },
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
