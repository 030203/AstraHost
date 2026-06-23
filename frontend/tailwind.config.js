/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#fff9f5',
          100: '#fef0e6',
          200: '#fde0ce',
          300: '#f5c9ab',
          400: '#e8a980',
          500: '#d99062',
          600: '#c97a50',   // primary
          700: '#b56540',
          800: '#9a5235',
          900: '#7d422c',
        },
        warm: {
          50:  '#fffcf7',
          100: '#fff8f1',
          200: '#fdf0e2',
          300: '#f6e5d2',
          400: '#e8d5be',
          500: '#d4bfa3',
          600: '#b8a088',
          700: '#8b7359',
          800: '#5c4a3a',
          900: '#3f312c',
        },
      },
      borderRadius: {
        'card': '20px',
        'card-lg': '24px',
        'button': '14px',
        'input': '14px',
        'pill': '999px',
      },
      boxShadow: {
        'card': '0 12px 32px rgba(114, 83, 60, 0.06)',
        'card-md': '0 20px 48px rgba(114, 83, 60, 0.09)',
        'card-lg': '0 28px 64px rgba(114, 83, 60, 0.12)',
        'button': '0 8px 20px rgba(168, 95, 71, 0.16)',
        'button-hover': '0 12px 28px rgba(168, 95, 71, 0.24)',
        'thumbnail': '0 4px 14px rgba(114, 83, 60, 0.10)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', '"PingFang SC"', '"Microsoft YaHei"', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        display: ['Inter', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
      fontSize: {
        'display': ['48px', { lineHeight: '1.05', letterSpacing: '-0.02em', fontWeight: '700' }],
        'display-sm': ['36px', { lineHeight: '1.1', letterSpacing: '-0.015em', fontWeight: '700' }],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease both',
        'slide-up': 'slideUp 0.5s ease both',
        'scale-in': 'scaleIn 0.3s ease both',
      },
      keyframes: {
        fadeIn: {
          'from': { opacity: '0' },
          'to':   { opacity: '1' },
        },
        slideUp: {
          'from': { opacity: '0', transform: 'translateY(16px)' },
          'to':   { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          'from': { opacity: '0', transform: 'scale(0.95)' },
          'to':   { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
