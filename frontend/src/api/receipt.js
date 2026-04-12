const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function buildQuery(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    query.append(key, String(value))
  })
  const text = query.toString()
  return text ? `?${text}` : ''
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  let payload = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    const message = payload?.detail || `Request failed with status ${response.status}`
    throw new Error(message)
  }

  return payload
}

// Keep signatures unchanged for existing views.
export async function fetchReceipts(params) {
  return request(`${API_BASE_URL}/receipts${buildQuery(params || {})}`)
}

export async function createReceipt(payload) {
  return request(`${API_BASE_URL}/receipts`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function updateReceipt(id, payload) {
  return request(`${API_BASE_URL}/receipts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deleteReceipt(id) {
  return request(`${API_BASE_URL}/receipts/${id}`, {
    method: 'DELETE'
  })
}
