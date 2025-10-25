import { PropsWithChildren } from 'react'
import {
  RouteObject,
  useLocation,
  Navigate,
  Routes,
  Route,
} from 'react-router'

import { useAuthState } from '@/contexts/AuthContext'

const ProtectedRoute: React.FC<PropsWithChildren> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthState()
  const location = useLocation()

  if (!isAuthenticated && !isLoading) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <>{children}</>
}

const pages = import.meta.glob<React.FC>('./pages/**/[a-z0-9]*.tsx', {
  eager: true,
  import: 'default',
})

const routes: RouteObject[] = Object.entries(pages).map(
  ([filename, Component]) => {
    const path = filename
      .slice('./pages'.length)
      .replace(/(index)?\.tsx$/, '')
      .split('/')
      .map((part) => part.replace(/\[(.+)\]/, ':$1'))
      .join('/')

    return {
      path,
      element:
        path !== '/login' ? (
          <ProtectedRoute>
            <Component />
          </ProtectedRoute>
        ) : (
          <Component />
        ),
    }
  }
)

const Router = () => {
  return (
    <Routes>
      {routes.map((route) => (
        <Route path={route.path} element={route.element} key={route.path} />
      ))}
    </Routes>
  )
}

export default Router
