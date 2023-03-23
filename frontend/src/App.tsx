import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import '@/globals.css'

import Router from './Router'

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
      <Router />
    </QueryClientProvider>
  )
}

export default App
