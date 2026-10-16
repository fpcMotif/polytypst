import { defineConfig } from "vite";
import { varlockVitePlugin } from "@varlock/vite-integration";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [varlockVitePlugin(), react(), tailwindcss()],
  server: {
    port: 5188,
    host: true,
  },
});
