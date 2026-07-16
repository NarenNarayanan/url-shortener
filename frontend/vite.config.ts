import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true, // listen on 0.0.0.0 so the Docker container is reachable from the host
    port: 5173,
    watch: {
      usePolling: true, // needed for reliable file-change detection inside Docker on some hosts
    },
  },
});
