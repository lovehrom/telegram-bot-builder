import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  // Для development используем '/', для production - '/editor/'
  base: process.env.NODE_ENV === 'production' ? '/editor/' : '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: true,
    hmr: {
      interval: 30,
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
