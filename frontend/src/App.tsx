import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import '@/globals.css' // Be sure to import globals before tremor
import '@tremor/react/dist/esm/tremor.css'

import Router from './Router'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
    </QueryClientProvider>
  )
}

export default App
