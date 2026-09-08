const API_BASE = '/api/v1'

export class ApiError extends Error {
  constructor(status, payload) {
    super(payload?.message || 'Error en la solicitud')
    this.status = status
    this.code = payload?.code
    this.details = payload?.details || []
    this.payload = payload
  }
}

function authHeader() {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, { method = 'GET', body, auth = false, query } = {}) {
  if (query) {
    const params = new URLSearchParams(
      Object.entries(query).filter(([, v]) => v !== undefined && v !== null)
    ).toString()
    if (params) path += (path.includes('?') ? '&' : '?') + params
  }
  const headers = { 'Content-Type': 'application/json', ...(auth ? authHeader() : {}) }
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { message: text }
    }
  }
  if (!res.ok) {
    throw new ApiError(res.status, data)
  }
  return data
}

export const api = {
  get: (p, opts) => request(p, { ...opts, method: 'GET' }),
  post: (p, body, opts) => request(p, { ...opts, method: 'POST', body }),
  put: (p, body, opts) => request(p, { ...opts, method: 'PUT', body }),
  del: (p, opts) => request(p, { ...opts, method: 'DELETE' }),
}
