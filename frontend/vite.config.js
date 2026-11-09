import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the React app calls /api; this forwards those calls to the Flask backend
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:5000' } },
})
