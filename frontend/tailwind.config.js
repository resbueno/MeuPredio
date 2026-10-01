/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Usadas apenas na landing page.
        nunito: ["Nunito", "DIN Round Pro", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        feather: ["Feather Bold", "Nunito", "DIN Round Pro", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      colors: {
        // Extraído da logo oficial (logo_meu_predio.jpg): azul do prédio em
        // destaque (~#1961ed) e navy escuro dos prédios ao fundo (~#050b1f).
        brand: {
          50: "#f4f7fe",
          100: "#e3ecfd",
          200: "#c3d6fa",
          300: "#9ab9f7",
          400: "#6394f3",
          500: "#3574ef",
          600: "#1961ed",
          700: "#1349b3",
          800: "#0e327c",
          900: "#091c48",
        },
        ink: "#050b1f",
      },
    },
  },
  plugins: [],
};
