import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://journalaboutnothing.com",
  trailingSlash: "always",
  build: { format: "directory" },
});
