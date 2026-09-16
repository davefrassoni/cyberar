import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
export default defineConfig({
  plugins: [vue()],
  base: "/cyberar/",
  server: {
    proxy: {
      "/cyberar/api": { target: "http://127.0.0.1:8063" },
      "/cyberar/ws": { target: "ws://127.0.0.1:8063", ws: true },
    },
  },
});
