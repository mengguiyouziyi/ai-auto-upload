import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 移除自动导入，改用@use语法
      }
    }
  },
  server: {
    port: 5174,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/getValidAccounts': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/postVideo': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/getFiles': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/download': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/account': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/updateUserinfo': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/deleteAccount': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      },
      '/login': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          elementPlus: ['element-plus'],
          utils: ['axios']
        }
      }
    }
  }
})
