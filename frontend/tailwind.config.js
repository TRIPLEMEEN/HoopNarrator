/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary colors
        'hoop-yellow': '#FFD700',
        'hoop-yellow-light': '#FFE44D',
        'hoop-yellow-dark': '#E6C200',
        
        // Secondary colors
        'hoop-blue': '#1E40AF',
        'hoop-blue-light': '#3B82F6',
        'hoop-blue-dark': '#1E3A8A',
        
        // Neutrals
        'hoop-white': '#FFFFFF',
        'hoop-gray-100': '#F3F4F6',
        'hoop-gray-200': '#E5E7EB',
        'hoop-gray-700': '#374151',
        'hoop-gray-900': '#111827',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Bebas Neue', 'sans-serif'],
      },
      animation: {
        'bounce-slow': 'bounce 3s infinite',
      }
    },
  },
  plugins: [],
}
