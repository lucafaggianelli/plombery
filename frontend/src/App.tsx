import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router'

import '@/globals.css'
import Router from './Router'
import { AuthProvider } from './contexts/AuthContext'
import WebSocketContext from './contexts/WebSocketContext'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketContext>
        <BrowserRouter>
          <AuthProvider>
            <Router />
          </AuthProvider>
        </BrowserRouter>
      </WebSocketContext>
    </QueryClientProvider>
  )
}

export default App
