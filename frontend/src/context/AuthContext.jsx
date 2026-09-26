import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import * as api from '../services/api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)       // { username, email, role, ... } from /auth/me
  const [loading, setLoading] = useState(true)  // true while we check for an existing session
  const [error, setError] = useState(null)

  const loadUser = useCallback(async () => {
    if (!api.getToken()) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await api.getCurrentUser()
      const userData = me?.user ?? me?.data ?? me
      setUser(userData)
    } catch (e) {
      api.clearToken()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadUser() }, [loadUser])

  const signIn = useCallback(async (username, password) => {
    setError(null)
    const res = await api.login(username, password)
    if (!res?.access_token) throw { message: res?.message || 'Login failed' }
    api.setToken(res.access_token)
    const me = await api.getCurrentUser()
    const userData = me?.user ?? me?.data ?? me
    setUser(userData)
    return me
  }, [])

  const signUp = useCallback(async (username, email, password, role = 'Viewer') => {
    setError(null)
    const res = await api.register({ username, email, password, role })
    if (res && res.success === false) {
      throw { message: res.message || 'Registration failed' }
    }
    return res
  }, [])

  const signOut = useCallback(() => {
    api.clearToken()
    setUser(null)
  }, [])

  const role = user?.role ?? user?.user?.role ?? user?.data?.role ?? null

  const value = { user, role, loading, error, setError, signIn, signUp, signOut, isAuthenticated: !!user }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
