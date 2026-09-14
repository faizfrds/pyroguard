/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        pyro: {
          dark: "#0b0f19",
          card: "#111827",
          border: "#1f293d",
          accent: "#f97316",
          critical: "#ef4444",
          high: "#f97316",
          moderate: "#eab308",
          low: "#22c55e"
        }
      },
    },
  },
  plugins: [],
};

