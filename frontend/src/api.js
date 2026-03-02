const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const error = new Error(body.detail || `Request failed: ${res.status}`)
    error.status = res.status
    error.body = body
    throw error
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  auth: {
    requestOTP: (email) => request('/auth/request-otp', { method: 'POST', body: JSON.stringify({ email }) }),
    verifyOTP: (email, code) => request('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ email, code }) }),
    logout: () => request('/auth/logout', { method: 'POST' }),
  },
  users: {
    register: (data) => request('/users/register', { method: 'POST', body: JSON.stringify(data) }),
    me: () => request('/users/me'),
    update: (data) => request('/users/me', { method: 'PATCH', body: JSON.stringify(data) }),
    credits: () => request('/users/me/credits'),
  },
  availability: {
    mine: () => request('/availability/mine'),
    setRecurring: (data) => request('/availability/recurring', { method: 'POST', body: JSON.stringify(data) }),
    addOneOff: (data) => request('/availability/one-off', { method: 'POST', body: JSON.stringify(data) }),
    remove: (id) => request(`/availability/${id}`, { method: 'DELETE' }),
    togglePause: (id) => request(`/availability/${id}/pause`, { method: 'PATCH' }),
    addExclusion: (date) => request('/availability/recurring/exclude', { method: 'POST', body: JSON.stringify({ date }) }),
    removeExclusion: (date) => request(`/availability/recurring/exclude/${date}`, { method: 'DELETE' }),
  },
  map: {
    bays: () => request('/map/bays'),
    status: (date, start, end) => request(`/map/status?date=${date}&start=${start}&end=${end}`),
  },
  browse: {
    available: (date, start, end) => request(`/browse/available?date=${date}&start=${start}&end=${end}`),
  },
  bookings: {
    create: (data) => request('/bookings', { method: 'POST', body: JSON.stringify(data) }),
    mine: () => request('/bookings/mine'),
    extend: (id, hours) => request(`/bookings/${id}/extend`, { method: 'PATCH', body: JSON.stringify({ hours }) }),
    reduce: (id, hours) => request(`/bookings/${id}/reduce`, { method: 'PATCH', body: JSON.stringify({ hours }) }),
    cancel: (id) => request(`/bookings/${id}`, { method: 'DELETE' }),
  },
}
