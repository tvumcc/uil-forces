import { defineConfig } from "vite"
import { svelte } from "@sveltejs/vite-plugin-svelte"

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  base: "./",
  build: {
    rollupOptions: {
      input: {
        home: "./src/frontend/html/home.html",
        login: "./src/frontend/html/login.html"
      },
    },
  },
})
