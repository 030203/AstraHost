import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5400,
    proxy: {
      '/api': {
        target: 'http://localhost:8088',
        changeOrigin: true
      },
      '/ai-api': {
        target: 'http://localhost:8088',
        changeOrigin: true
      },
      '/chat': {
        target: 'http://localhost:5001',
        changeOrigin: true
      },
      '/conversations': {
        target: 'http://localhost:5001',
        changeOrigin: true
      },
      '/suggestions': {
        target: 'http://localhost:5001',
        changeOrigin: true
      },
      '/skills': {
        target: 'http://localhost:5001',
        changeOrigin: true
      },
      '/__dev_reload__': {
        target: 'http://localhost:5001',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:5001',
        changeOrigin: true
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name || ''
          if (/\.css$/i.test(info)) return 'css/[name]-[hash].css'
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(info)) return 'img/[name]-[hash][extname]'
          if (/\.(woff2?|eot|ttf|otf)$/i.test(info)) return 'fonts/[name]-[hash][extname]'
          return 'assets/[name]-[hash][extname]'
        }
      }
    },
    chunkSizeWarningLimit: 550,
    minify: 'esbuild',
    target: 'es2015'
  }
})
