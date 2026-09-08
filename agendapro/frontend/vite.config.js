import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// En desarrollo, /api se proxia al backend Flask local (gunicorn/wsgi en :8000).
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
