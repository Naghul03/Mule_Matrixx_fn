/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#090907',
          secondary: '#12110E',
          card: '#161511',
          hover: '#1E1B15',
        },
        earth: {
          light: '#8E734C',
          DEFAULT: '#6C5636',
          dark: '#4B3A22',
        },
        amber: {
          light: '#D3BA94',
          DEFAULT: '#B99D73',
          dark: '#937951',
        },
        warm: {
          white: '#F5F5F0',
          muted: '#D0D0C8',
        },
        muted: {
          gray: '#9E9E96',
          dark: '#5C5C54',
          border: '#28251E',
          borderLight: '#3D382E',
        },
        status: {
          success: '#4E9E67',
          warning: '#E29B38',
          danger: '#D65353',
          info: '#6E8FB7',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

