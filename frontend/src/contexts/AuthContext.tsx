import React, { createContext, useContext, useEffect, useReducer } from 'react'

import { getCurrentUser, logout } from '@/repository'

type User = {
  email: string
  name: string
} | null

type AuthState = {
  isAuthenticated: boolean
  isAuthenticationEnabled: boolean
  isLoading: boolean
  logout: () => Promise<any>
  user: User
}

type Action =
  | { type: 'LOGIN'; payload: { user: User; isAuthenticationEnabled: boolean } }
  | { type: 'POPULATE'; payload: User }
  | { type: 'LOGOUT' }
  | { type: 'STOP_LOADING' }

const StateContext = createContext<AuthState>({
  isAuthenticated: false,
  isAuthenticationEnabled: true,
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
        isAuthenticationEnabled: action.payload.isAuthenticationEnabled,
        user: action.payload.user,
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
    isAuthenticationEnabled: true,
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
        const { is_authentication_enabled, user } = await getCurrentUser()

        if ((is_authentication_enabled && user) || !is_authentication_enabled) {
          dispatch({
            type: 'LOGIN',
            payload: {
              user,
              isAuthenticationEnabled: is_authentication_enabled,
            },
          })
        }
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
      {state.isAuthenticationEnabled && state.isLoading
        ? 'Loading...'
        : children}
    </StateContext.Provider>
  )
}

export const useAuthState = () => useContext(StateContext)
