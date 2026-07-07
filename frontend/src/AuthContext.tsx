import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, clearTokens, hasSession, login as apiLogin } from './api'
import type { User } from './types'

type AuthValue = {
  user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>;
  bootstrap: (name: string, email: string, password: string) => Promise<void>; logout: () => Promise<void>;
  refreshUser: () => Promise<void>; can: (permission: string) => boolean;
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  async function loadUser() {
    if (!hasSession()) { setLoading(false); return }
    try { setUser(await api<User>('/auth/me')) } catch { clearTokens(); setUser(null) }
    finally { setLoading(false) }
  }

  useEffect(() => { void loadUser() }, [])

  async function login(email: string, password: string) {
    await apiLogin(email, password); setUser(await api<User>('/auth/me'))
  }

  async function bootstrap(name: string, email: string, password: string) {
    await api('/auth/bootstrap', { method: 'POST', body: JSON.stringify({ name, email, password }) })
    await login(email, password)
  }

  async function logout() {
    try { await api('/auth/logout', { method: 'POST' }) } finally { clearTokens(); setUser(null) }
  }

  async function refreshUser() {
    setUser(await api<User>('/auth/me'))
  }

  return <AuthContext.Provider value={{ user, loading, login, bootstrap, logout, refreshUser, can: p => user?.permission_keys.includes(p) ?? false }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider is missing')
  return value
}
