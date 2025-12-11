import { defineConfig } from "vite"
import { svelte } from "@sveltejs/vite-plugin-svelte"
import fg from "fast-glob"
import path from "path"

const htmlFiles = fg.sync("src/frontend/html/**/*.html")
const input = Object.fromEntries(
  htmlFiles.map((file: any) => {
    const name = path.basename(file, ".html")
    return [name, path.resolve(file)]
  })
)

export default defineConfig({
  plugins: [svelte()],
  base: "./",
  build: {
    rollupOptions: {
      input,
    },
  },
})
