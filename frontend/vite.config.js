import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxies API calls to the existing FastAPI backend at http://127.0.0.1:8000
// so the frontend can simply call relative paths in dev, and CORS stays simple.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/upload': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/download': { target: 'http://127.0.0.1:8000', changeOrigin: true }
    }
  }
})
