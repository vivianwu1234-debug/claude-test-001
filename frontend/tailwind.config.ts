import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0f1117",
          secondary: "#1a1d26",
          card: "#1e2130",
          hover: "#252840",
          border: "#2a2f45",
        },
        accent: {
          purple: "#7c6ff7",
          blue: "#4f9cf9",
          cyan: "#00d2ff",
          green: "#00c896",
          pink: "#f72585",
          orange: "#ff9f0a",
          red: "#ff453a",
          yellow: "#ffd60a",
        },
        text: {
          primary: "#e8eaf6",
          secondary: "#9095b0",
          muted: "#5a5f7a",
        }
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
export default config;
