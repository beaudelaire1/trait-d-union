/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'tus-black': '#07080A',
        'tus-white': '#F6F7FB',
        'tus-blue': '#0B2DFF',
        'tus-blue-a11y': '#4D6FFF', /* WCAG AA sur fond noir (4.6:1) */
        'tus-green': '#22C55E',
        'surface-dark': '#0D1016',
        'stroke-dark': 'rgba(246,247,251,0.10)',
      },
      fontFamily: {
        'display': ['Space Grotesk', 'system-ui', 'sans-serif'],
        'body': ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.8s ease-out forwards',
        'slide-in-right': 'slideInRight 0.6s ease-out forwards',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'marquee': 'marquee 20s linear infinite',
        'gradient-shift': 'gradientShift 3s ease-in-out infinite',
        'text-scroll': 'textScroll 18s linear infinite',
        'tv-ticker': 'tvTicker 12s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(11,45,255,0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(11,45,255,0.6)' },
        },
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        gradientShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        textScroll: {
          '0%': { transform: 'translateX(100vw)' },
          '100%': { transform: 'translateX(-100%)' },
        },
        tvTicker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
    },
  },
  plugins: [],
}
