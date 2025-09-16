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
        login: "./src/frontend/html/login.html",
        contest: "./src/frontend/html/contest.html",
        contestList: "./src/frontend/html/contestList.html",
        submission: "./src/frontend/html/submission.html",
      },
    },
  },
})
