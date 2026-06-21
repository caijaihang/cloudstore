import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  // 桌面版打包配置：构建产物输出到 backend/frontend_build/
  build: {
    outDir: fileURLToPath(new URL('../backend/frontend_build', import.meta.url)),
    emptyOutDir: true,
    // 使用绝对路径，Django 通过 serve_frontend_or_index 正确服务静态资源
    base: '/',
    // 资源内联小文件，减少文件数量
    assetsInlineLimit: 4096,
  }
})
