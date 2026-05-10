const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

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
    const message = payload?.message || payload?.detail || `Request failed with status ${response.status}`
    throw new Error(message)
  }

  if (!payload || typeof payload !== 'object') {
    throw new Error('Invalid response payload')
  }

  if (payload.code !== 0) {
    throw new Error(payload.message || 'Request failed')
  }

  return payload.data
}

export async function fetchCategories() {
  return request(`${API_BASE_URL}/system/categories`)
}

export async function createCategory(payload) {
  return request(`${API_BASE_URL}/system/categories`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function deleteCategory(id) {
  return request(`${API_BASE_URL}/system/categories/${id}`, {
    method: 'DELETE'
  })
}

export async function renameCategory(id, payload) {
  return request(`${API_BASE_URL}/system/categories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function fetchPaymentMethods() {
  return request(`${API_BASE_URL}/system/payment-methods`)
}

export async function createPaymentMethod(payload) {
  return request(`${API_BASE_URL}/system/payment-methods`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function renamePaymentMethod(id, payload) {
  return request(`${API_BASE_URL}/system/payment-methods/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deletePaymentMethod(id) {
  return request(`${API_BASE_URL}/system/payment-methods/${id}`, {
    method: 'DELETE'
  })
}
