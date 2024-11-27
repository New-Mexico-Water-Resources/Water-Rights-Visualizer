import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import markdown from "vite-plugin-md";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), markdown()],
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
        changelog: "../CHANGELOG.md",
      },
    },
  },
  assetsInclude: ["**/*.md"],
});
