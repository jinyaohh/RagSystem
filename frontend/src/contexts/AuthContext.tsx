'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, AuthResponse } from '@/types'
import { getCurrentUser, getAuthToken, setAuthToken, logout as apiLogout } from '@/lib/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  login: (authResponse: AuthResponse) => void
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      const token = getAuthToken()
      if (token) {
        try {
          const userData = await getCurrentUser()
          setUser(userData)
        } catch (error) {
          console.error('Failed to load user:', error)
          // Token is invalid, clear it
          setAuthToken(null)
        }
      }
      setLoading(false)
    }

    loadUser()
  }, [])

  const login = (authResponse: AuthResponse) => {
    setUser(authResponse.user)
    // Token is already set by the API function
  }

  const logout = async () => {
    try {
      await apiLogout()
    } finally {
      setUser(null)
      setAuthToken(null)
    }
  }

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Failed to refresh user:', error)
      // If refresh fails, user might be logged out
      setUser(null)
      setAuthToken(null)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
