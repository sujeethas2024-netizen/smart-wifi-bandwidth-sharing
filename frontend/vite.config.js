import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// host: true → the dev server listens on 0.0.0.0 so phones/laptops on
// the same WiFi can open http://<PC-IP>:5173 (real-time multi-device demo).
// The /api proxy forwards API calls to the Flask backend on port 5000.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})