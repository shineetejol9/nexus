/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#060809',
        panel: '#0d1114',
        panel2: '#12171b',
        border: 'rgba(239,232,218,0.09)',
        paper: '#efe8da',
        sage: '#ff7a2f',
        toad: '#c8372d',
        volt: '#9fe8ff',
        muted: 'rgba(239,232,218,0.55)'
      },
      fontFamily: {
        mono: ['Space Mono', 'monospace'],
        disp: ['Anton', 'sans-serif'],
        beb: ['Bebas Neue', 'sans-serif']
      },
      boxShadow: {
        glow: '0 0 24px rgba(255,122,47,0.18)',
        voltGlow: '0 0 24px rgba(159,232,255,0.16)'
      }
    }
  },
  plugins: []
}
