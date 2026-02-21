import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',   // important so ngrok can connect
    port: 1793,
    allowedHosts: ["*"]
  }
})
