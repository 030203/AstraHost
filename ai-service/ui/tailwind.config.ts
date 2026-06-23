import type { Config } from "tailwindcss";
import forms from "@tailwindcss/forms";

export default {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "#FCFAF8",
          panel: "#F3ECE5",
          canvas: "#FFF9F4",
          soft: "#EDE2D8",
          line: "#DCCEC2",
          text: "#342821",
          mute: "#8B7567"
        },
        brand: {
          DEFAULT: "#C9856B",
          soft: "#F3E1D8",
          deep: "#8B5E4F"
        },
        success: "#7D9B76",
        warning: "#D29A5A"
      },
      borderRadius: {
        card: "24px",
        button: "14px",
        input: "16px",
        bubble: "22px"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(105, 78, 61, 0.06)",
        lift: "0 18px 48px rgba(96, 74, 59, 0.1)"
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(18px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        pulse: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.72", transform: "scale(1.08)" }
        }
      },
      animation: {
        "fade-in": "fade-in 0.35s ease-out",
        "slide-up": "slide-up 0.45s ease-out",
        pulse: "pulse 1.6s ease-in-out infinite"
      },
      fontFamily: {
        sans: ["Inter", "\"PingFang SC\"", "\"Microsoft YaHei\"", "sans-serif"]
      }
    }
  },
  plugins: [forms]
} satisfies Config;
