import { useEffect, useState } from 'react'

// Runs an API call and tracks loading / error. reload() runs it again.
export function useLoad(loader, deps) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const [tick, setTick] = useState(0)
  useEffect(() => {
    let alive = true
    setState(s => ({ ...s, loading: true, error: null }))
    loader()
      .then(data => alive && setState({ data, loading: false, error: null }))
      .catch(e => alive && setState({ data: null, loading: false, error: e.message }))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])
  return { ...state, reload: () => setTick(t => t + 1) }
}

export function useDebounced(value, ms = 300) {
  const [v, setV] = useState(value)
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t) }, [value, ms])
  return v
}
