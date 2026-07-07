const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

type Tokens = { access_token: string; refresh_token: string; token_type: string }
let accessToken = localStorage.getItem('workspace_access')
let refreshToken = localStorage.getItem('workspace_refresh')

export function saveTokens(tokens: Tokens) {
  accessToken = tokens.access_token
  refreshToken = tokens.refresh_token
  localStorage.setItem('workspace_access', accessToken)
  localStorage.setItem('workspace_refresh', refreshToken)
}

export function clearTokens() {
  accessToken = null; refreshToken = null
  localStorage.removeItem('workspace_access'); localStorage.removeItem('workspace_refresh')
}

async function parseError(response: Response) {
  try {
    const data = await response.json()
    if (Array.isArray(data.detail)) return data.detail.map((x: { msg: string }) => x.msg).join('، ')
    return data.detail || 'حدث خطأ غير متوقع'
  } catch { return 'تعذر الاتصال بالخادم' }
}

async function refreshSession() {
  if (!refreshToken) return false
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken })
  })
  if (!response.ok) { clearTokens(); return false }
  saveTokens(await response.json()); return true
}

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(options.headers)
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (response.status === 401 && retry && await refreshSession()) return api<T>(path, options, false)
  if (!response.ok) throw new Error(await parseError(response))
  if (response.status === 204) return undefined as T
  return response.json()
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password })
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form
  })
  if (!response.ok) throw new Error(await parseError(response))
  const tokens = await response.json(); saveTokens(tokens); return tokens
}

export async function download(path: string, filename: string) {
  const headers = new Headers(); if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  let response = await fetch(`${API_URL}${path}`, { headers })
  if (response.status === 401 && await refreshSession()) {
    headers.set('Authorization', `Bearer ${accessToken}`); response = await fetch(`${API_URL}${path}`, { headers })
  }
  if (!response.ok) throw new Error(await parseError(response))
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click()
  URL.revokeObjectURL(url)
}

export const hasSession = () => Boolean(accessToken && refreshToken)
