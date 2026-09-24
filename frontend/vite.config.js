import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api calls to the FastAPI backend so the frontend
// can just call fetch("/api/...") in both dev and production.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
