import React, { createContext, useContext, useEffect, useReducer } from 'react'

import { getCurrentUser, logout } from '@/repository'

type User = {
  email: string
  name: string
} | null
type AuthState = {
  isAuthenticated: boolean
  user: User
  isLoading: boolean
  logout: () => Promise<any>
}
type Action =
  | { type: 'LOGIN'; payload: User }
  | { type: 'POPULATE'; payload: User }
  | { type: 'LOGOUT' }
  | { type: 'STOP_LOADING' }

const StateContext = createContext<AuthState>({
  isAuthenticated: false,
  isLoading: true,
  logout: async () => {},
  user: null,
})

const reducer = (state: AuthState, action: Action): AuthState => {
  switch (action.type) {
    case 'LOGIN':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload,
      }
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
      }
    case 'POPULATE':
      return {
        ...state,
        user: action.payload
          ? {
              ...state.user,
              ...action.payload,
            }
          : null,
      }
    case 'STOP_LOADING':
      return {
        ...state,
        isLoading: false,
      }
    default:
      throw new Error('Unknown action type')
  }
}

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [state, dispatch] = useReducer(reducer, {
    isAuthenticated: false,
    isLoading: true,
    logout: async () => {
      await logout()
      dispatch({ type: 'LOGOUT' })
    },
    user: null,
  })

  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await getCurrentUser()
        dispatch({ type: 'LOGIN', payload: user })
      } catch (err) {
        console.error(err)
      } finally {
        dispatch({ type: 'STOP_LOADING' })
      }
    }

    loadUser()
  }, [])

  return (
    <StateContext.Provider value={state}>
      {children}
    </StateContext.Provider>
  )
}

export const useAuthState = () => useContext(StateContext)
