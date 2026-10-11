import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // /langflow/... → http://localhost:7860/...
      // Strips the /langflow prefix before forwarding to Langflow Desktop
      '/langflow': {
        target: 'http://localhost:7860',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/langflow/, ''),
      },
    },
  },
})
