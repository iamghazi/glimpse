/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#2463eb',
        'primary-hover': '#1d4ed8',
        'secondary': '#7c3aed',
        'secondary-hover': '#6d28d9',
        'background': '#f3f4f6',
        'surface': '#ffffff',
        'success': '#10b981',
        'error': '#ef4444',
      },
      fontFamily: {
        'display': ['Inter', 'sans-serif']
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        }
      },
      animation: {
        shimmer: 'shimmer 2s infinite'
      }
    }
  },
  plugins: []
}
