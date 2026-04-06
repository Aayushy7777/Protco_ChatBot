import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5144,
    proxy: {
      '/upload': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      '/dashboard': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
    }
  }
})
