import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Локальная разработка: проксируем /api на backend.
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
