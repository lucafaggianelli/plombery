import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import '@/globals.css'

import Router from './Router'
import { AuthProvider } from './contexts/AuthContext'
import { BrowserRouter } from 'react-router-dom'
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
