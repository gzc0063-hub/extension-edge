import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/extension-edge/', // Match the GitHub repository name for proper asset resolution on GH Pages
  build: {
    outDir: 'dist',
  }
})
