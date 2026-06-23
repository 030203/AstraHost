import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  base: "/static/copilot/",
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5100,
    proxy: {
      "/chat": "http://127.0.0.1:5001",
      "/conversations": "http://127.0.0.1:5001",
      "/suggestions": "http://127.0.0.1:5001",
      "/skills": "http://127.0.0.1:5001",
      "/__dev_reload__": "http://127.0.0.1:5001",
      "/health": "http://127.0.0.1:5001"
    }
  },
  build: {
    outDir: "../static/copilot",
    emptyOutDir: true
  }
});

