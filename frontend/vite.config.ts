import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Path onde o app é servido. Localmente é "/" (raiz); atrás do gateway
// compartilhado de uma VPS que hospeda múltiplos projetos, é um subpath
// (ex.: "/meupredio/") — ver infra/vps/. Configurável via VITE_BASE_PATH
// para não precisar de um vite.config.ts diferente por ambiente.
const basePath = process.env.VITE_BASE_PATH ?? "/";

// https://vite.dev/config/
export default defineConfig({
  base: basePath,
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: "auto",
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,webmanifest}"],
      },
      manifest: {
        id: basePath,
        name: "MeuPrédio",
        short_name: "MeuPrédio",
        description: "Gestão de condomínios - MeuPrédio",
        start_url: basePath,
        scope: basePath,
        display: "standalone",
        background_color: "#050b1f",
        theme_color: "#050b1f",
        icons: [
          {
            src: "icon-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "icon-512-maskable.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
    }),
  ],
  server: {
    host: true,
    port: 5173,
  },
});
