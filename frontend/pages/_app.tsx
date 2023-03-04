import type { AppProps } from 'next/app'
import '@/styles/globals.css'
import '@tremor/react/dist/esm/tremor.css'

import { QueryClientProvider, QueryClient } from '@tanstack/react-query'
import { useState } from 'react'

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <QueryClientProvider client={queryClient}>
      <Component {...pageProps} />
    </QueryClientProvider>
  )
}
