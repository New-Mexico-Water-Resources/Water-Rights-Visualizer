import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: "./",
  server: {
    fs: {
      allow: [".."],
    },
  },
  build: {
    rollupOptions: {
      input: {
        app: "./index.html",
        changelog: "./CHANGELOG.md",
      },
    },
  },
  assetsInclude: ["**/*.md"],
});
