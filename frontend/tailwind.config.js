/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0e0f11',
          secondary: '#15171a',
          card: '#1c1f24',
        },
        border: 'rgba(255,255,255,0.07)',
        text: '#f0f0ee',
        muted: '#8a8d94',
        accent: '#c8f064',
        success: '#5ce8a4',
        warning: '#f5a623',
        danger: '#f07070',
        info: '#6eb5ff',
      },
      fontFamily: {
        heading: ['Syne', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
