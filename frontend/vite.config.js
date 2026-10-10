
import react from ' @vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath } from 'node:url'

// Load environment variables from the backend's .env file.
const backendEnvDir = fileURLToPath(new URL('../backend', import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, backendEnvDir, '')

  if (!env.API_KEY) {
    throw new Error('API_KEY is missing from backend/.env')
  }

  return {
    plugins: [react()],

    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,

          // Convert /api/predict to /predict for FastAPI.
          rewrite: (path) => path.replace(/^\/api/, ''),

          // Add the API key on the server, not in browser code.
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq) => {
              proxyReq.setHeader('X-API-Key', env.API_KEY)
            })
          },
        },
      },
    },
  }
})
