import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: [
      'ui.gridtokenx-smartmeter-simulator.orb.local',
      '.orb.local'
    ],
    proxy: {
      '/api': {
        target: 'http://simulator:8082',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'http://simulator:8082',
        ws: true,
        changeOrigin: true,
        secure: false,
        timeout: 60000,
        proxyTimeout: 60000,
      },
    },
  },
})
