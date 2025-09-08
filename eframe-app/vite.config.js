import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/safetydetection': 'http://localhost:5000',
      '/detection_feed': 'http://localhost:5000',
      '/stopdetection': 'http://localhost:5000',
      // add more endpoints as needed
    }
  }
})
