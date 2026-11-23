import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: "/DevLens-AI/",
  plugins: [react(), tailwindcss()],
  test: {
    environment: "jsdom",
    pool: "threads",
    maxWorkers: 1,
    fileParallelism: false,
  },
});
