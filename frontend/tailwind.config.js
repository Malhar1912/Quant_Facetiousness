/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: "#08111F", light: "#10233D" },
        electric: "#2F80FF",
        cyan: { soft: "#59C3FF", ice: "#84CFFF" },
        aqua: "#00FFFF",
        coral: "#ffb4ab",
        surface: { DEFAULT: "#101416", dim: "#101416", bright: "#363a3c",
          "container-lowest": "#0b0f10", "container-low": "#181c1e",
          container: "#1c2022", "container-high": "#262b2c",
          "container-highest": "#313537" },
        "on-surface": { DEFAULT: "#e0e3e5", variant: "#c2c6d7" },
        primary: { DEFAULT: "#aec6ff", container: "#4f8eff",
          fixed: "#d8e2ff", "fixed-dim": "#aec6ff" },
        secondary: { DEFAULT: "#84cfff", container: "#1c9ad4",
          fixed: "#c7e7ff", "fixed-dim": "#84cfff" },
        tertiary: { DEFAULT: "#b4c8e2", container: "#7f93aa" },
        error: { DEFAULT: "#ffb4ab", container: "#93000a" },
        outline: { DEFAULT: "#8c90a0", variant: "#414754" },
      },
      fontFamily: {
        grotesk: ["Space Grotesk", "monospace"],
        manrope: ["Manrope", "sans-serif"],
      },
      spacing: { gutter: "20px", margin: "32px" },
      animation: {
        "pulse-glow": "pulse-glow 3s infinite",
        "fade-in": "fade-in 0.5s ease-out",
        "slide-up": "slide-up 0.4s ease-out",
      },
      keyframes: {
        "pulse-glow": {
          "0%": { boxShadow: "0 0 0 0 rgba(47,128,255,0.4)" },
          "70%": { boxShadow: "0 0 0 10px rgba(47,128,255,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(47,128,255,0)" },
        },
        "fade-in": { "0%": { opacity: 0 }, "100%": { opacity: 1 } },
        "slide-up": {
          "0%": { opacity: 0, transform: "translateY(20px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
