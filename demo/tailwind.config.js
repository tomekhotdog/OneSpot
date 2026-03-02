/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#5BA4D9',
          light: '#E8F2FA',
          dark: '#2E7AB8',
        },
        accent: {
          green: '#4CAF82',
          'green-light': '#E8F5EC',
          amber: '#E8A838',
          red: '#E8645A',
        },
        text: {
          primary: '#1A1A1A',
          secondary: '#6B6B6B',
        },
        bg: {
          page: '#F7F9FB',
          card: '#FFFFFF',
        },
        border: '#E2E8F0',
      },
      fontFamily: {
        sans: ['"DM Sans"', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        body: '14px',
        emphasis: '16px',
        'title-section': '20px',
        'title-page': '28px',
        hero: '40px',
      },
      borderRadius: {
        card: '12px',
        button: '8px',
        pill: '20px',
      },
      maxWidth: {
        content: '480px',
      },
    },
  },
  plugins: [],
}
