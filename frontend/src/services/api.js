// Everything the frontend knows about the backend lives here.
// In development Vite forwards /api to the Flask server (see vite.config.js).
const BASE = import.meta.env.VITE_API_URL || '/api'
const KEY = 'pharmalims_token'

let token = null
try { token = sessionStorage.getItem(KEY) } catch { /* storage unavailable */ }
let onUnauthorized = () => {}

export class ApiError extends Error {
  constructor(message, status, errors) { super(message); this.status = status; this.errors = errors }
}
export const hasToken = () => !!token
export const setUnauthorizedHandler = fn => { onUnauthorized = fn }
const saveToken = t => {
  token = t
  try { t ? sessionStorage.setItem(KEY, t) : sessionStorage.removeItem(KEY) } catch { /* ignore */ }
}
const qs = q => {
  const p = new URLSearchParams()
  Object.entries(q || {}).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') p.append(k, v) })
  const s = p.toString()
  return s ? `?${s}` : ''
}

async function request(method, path, { body, query, text, raw } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (text !== undefined) { headers['Content-Type'] = 'text/csv'; payload = text }
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body) }
  let res
  try { res = await fetch(BASE + path + qs(query), { method, headers, body: payload }) }
  catch { throw new ApiError('Cannot reach the server. Is the backend running?', 0) }
     // The dev server answers 502/503/504 when the backend is stopped or not responding
   if ([502, 503, 504].includes(res.status)) throw new ApiError('Cannot reach the server. Is the backend running?', res.status)
  if (raw && res.ok) return res
  let json = null
  try { json = await res.json() } catch { /* not JSON */ }
  if (res.status === 401 && path !== '/auth/login') onUnauthorized()
  if (!res.ok || !json || json.success !== true) {
    throw new ApiError((json && json.message) || `Request failed (${res.status})`, res.status, json && json.errors)
  }
  return json.data
}

export const api = {
  get: (path, query) => request('GET', path, { query }),
  post: (path, body, query) => request('POST', path, { body, query }),
  put: (path, body) => request('PUT', path, { body }),
  del: path => request('DELETE', path),

  async login(username, password) {
    const data = await request('POST', '/auth/login', { body: { username, password } })
    saveToken(data.access_token)
    return data.user
  },
  me: () => request('GET', '/auth/me'),
  async logout() { try { await request('POST', '/auth/logout') } catch { /* token may already be invalid */ } saveToken(null) },
  clearSession: () => saveToken(null),
  changePassword: (current_password, new_password) => request('POST', '/auth/change-password', { body: { current_password, new_password } }),

  // CSV import: send the file's text. dry_run=true only checks it.
  importCsv: (path, text, query) => request('POST', path, { text, query }),

  // CSV / PDF downloads (they need the login token, so a plain link would not work)
  async download(path, query, fallbackName) {
    const res = await request('GET', path, { query, raw: true })
    const blob = await res.blob()
    const match = /filename="?([^";]+)"?/.exec(res.headers.get('Content-Disposition') || '')
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = match ? match[1] : fallbackName
    document.body.appendChild(link); link.click(); link.remove()
    setTimeout(() => URL.revokeObjectURL(link.href), 1000)
  },
}
