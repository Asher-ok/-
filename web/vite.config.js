import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? '/admin/' : '/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        // target: process.env.VITE_API_TARGET || 'http://38.180.128.101:8000',
        target: process.env.VITE_API_TARGET || 'http://127.0.0.1:8000', // 'http://38.180.128.101:8000',
        changeOrigin: true,
        rewrite: (path) => path,
        ws: true,
        timeout: 180000,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            console.log('代理错误:', err)
          })
        }
      }
    }
  },
  optimizeDeps: {
    include: ['pdfjs-dist/legacy/build/pdf.js']
  }
}))
