import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "var(--bg-primary)",
          secondary: "var(--bg-secondary)",
          tertiary: "var(--bg-tertiary)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
        },
        accent: "var(--accent)",
        success: "var(--success)",
        warning: "var(--warning)",
        error: "var(--error)",
      },
      borderColor: {
        DEFAULT: "var(--border)",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      borderRadius: {
        sm: "2px",
        DEFAULT: "4px",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
} satisfies Config;
