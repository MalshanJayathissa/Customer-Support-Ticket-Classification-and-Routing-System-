import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,

        rewrite: (path) => path.replace(/^\/api/, ""),

        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq) => {
            const key = process.env.API_KEY;

            if (key) {
              proxyReq.setHeader("X-API-Key", key);
            }
          });
        },
      },
    },
  },
});