import path from 'path'
import { defineConfig, splitVendorChunkPlugin } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  plugins: [react(), splitVendorChunkPlugin()],
  build: {
    outDir: path.resolve('..', 'src', 'plombery', 'static'),
  },
})
