/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../dashboard/templates/**/*.html',
    '../admin/templates/**/*.html',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        raap: {
          primary: '#0ea5e9',
          secondary: '#14b8a6',
          dark: '#0f172a',
          darker: '#020617',
          card: '#1e293b',
          border: '#334155'
        }
      }
    }
  },
  plugins: []
}
