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
        pset: "./src/frontend/html/problemSet.html",
        psetList: "./src/frontend/html/problemSetList.html",
        adminUserList: "./src/frontend/html/adminUserList.html",
        adminContestList: "./src/frontend/html/adminContestList.html",
        adminContest: "./src/frontend/html/adminContest.html",
        register: "./src/frontend/html/register.html",
        adminProblemSet: "./src/frontend/html/adminProblemSet.html",
        adminSettings: "./src/frontend/html/adminSettings.html",
        adminSubmissionList: "./src/frontend/html/adminSubmissionList.html"
      },
    },
  },
})
