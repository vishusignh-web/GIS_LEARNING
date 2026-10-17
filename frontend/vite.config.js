import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server runs on 5173, which must match ALLOWED_ORIGINS in the backend .env
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
