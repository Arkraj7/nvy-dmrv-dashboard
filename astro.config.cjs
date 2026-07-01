import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  output: "static",
  site: "https://urbanforestpark.com",
  build: {
    assets: "assets",
  },
  markdown: { syntaxHighlight: "prism" },
  integrations: [tailwind()],
  vite: {
    optimizeDeps: { exclude: ["@ffmpeg-installer/ffprobe"] },
    ssr: { noExternal: ["astro", "@astrojs/*"] },
  },
});