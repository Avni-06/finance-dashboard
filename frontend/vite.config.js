import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: { react: ["react", "react-dom", "react-router-dom"], charts: ["recharts"] },
      },
    },
  },
  server: {
    port: 5173,
    // In dev, /api calls go to Flask so no CORS setup is needed locally
    proxy: {
      "/api": { target: "http://localhost:5000", changeOrigin: true },
    },
  },
});
