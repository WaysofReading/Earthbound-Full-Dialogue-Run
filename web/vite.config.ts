import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base: './' so the build works under a GitHub Pages project subpath.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    target: 'es2020',
  },
})
