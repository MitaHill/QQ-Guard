const API_BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok || data.success === false) {
    const message = data.error || `请求失败: ${response.status}`
    throw new Error(message)
  }
  return data
}

export function apiGet(path) {
  return request(path)
}

export function apiPut(path, body) {
  return request(path, {
    method: 'PUT',
    body: JSON.stringify(body)
  })
}

export function apiPatch(path, body) {
  return request(path, {
    method: 'PATCH',
    body: JSON.stringify(body)
  })
}
