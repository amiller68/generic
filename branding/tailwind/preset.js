const tokens = require('../core/tokens.json');

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Use CSS variables for theming
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        ring: 'hsl(var(--ring))',
        // Base gray scale for utility
        gray: tokens.colors.base.gray
      },
      fontFamily: {
        sans: tokens.typography.fonts.sans,
        mono: tokens.typography.fonts.mono,
      },
      fontSize: tokens.typography.sizes,
      spacing: tokens.spacing,
      borderRadius: tokens.borderRadius,
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.4s ease-out',
        'spin': 'spin 1s linear infinite',
        // Advanced animations for TS projects
        'blob': 'blob 15s infinite ease-in-out',
        'blob-reverse': 'blob-reverse 18s infinite ease-in-out',
        'float': 'float 12s ease-in-out infinite',
        'drift': 'drift 20s ease-in-out infinite',
        'orbit': 'orbit 25s linear infinite',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' }
        },
        'slide-up': {
          from: {
            opacity: '0',
            transform: 'translateY(10px)'
          },
          to: {
            opacity: '1',
            transform: 'translateY(0)'
          }
        },
        'spin': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' }
        },
        // Advanced animations
        'blob': {
          '0%, 100%': {
            transform: 'translate(0, 0) scale(1)',
          },
          '33%': {
            transform: 'translate(300px, -300px) scale(1.2)',
          },
          '66%': {
            transform: 'translate(-200px, 200px) scale(0.8)',
          }
        },
        'blob-reverse': {
          '0%, 100%': {
            transform: 'translate(0, 0) scale(1)',
          },
          '33%': {
            transform: 'translate(-300px, 200px) scale(1.2)',
          },
          '66%': {
            transform: 'translate(200px, -300px) scale(0.8)',
          }
        },
        'float': {
          '0%, 100%': {
            transform: 'translateY(0px)',
          },
          '50%': {
            transform: 'translateY(-200px)',
          }
        },
        'drift': {
          '0%, 100%': {
            transform: 'translate(0, 0)',
          },
          '25%': {
            transform: 'translate(400px, -200px)',
          },
          '50%': {
            transform: 'translate(-300px, 300px)',
          },
          '75%': {
            transform: 'translate(200px, 150px)',
          }
        },
        'orbit': {
          from: {
            transform: 'rotate(0deg) translateX(250px) rotate(0deg)',
          },
          to: {
            transform: 'rotate(360deg) translateX(250px) rotate(-360deg)',
          }
        }
      }
    },
  },
  plugins: [],
}