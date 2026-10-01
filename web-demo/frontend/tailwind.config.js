/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      gridTemplateColumns: {
        '20': 'repeat(20, minmax(0, 1fr))',
      },
      colors: {
        tac: {
          bg:      '#050810',
          surface: '#0d1117',
          s2:      '#161b22',
          s3:      '#21262d',
          border:  '#30363d',
          green:   '#00ff88',
          blue:    '#00b4ff',
          amber:   '#ff8800',
          red:     '#ff3355',
          text:    '#e6edf3',
          muted:   '#8b949e',
          dim:     '#484f58',
        }
      },
      fontFamily: {
        tactical: ['Rajdhani', 'Inter', 'sans-serif'],
        mono:     ['JetBrains Mono', 'Courier New', 'monospace'],
        ui:       ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-green': 'pulse-green 2s infinite',
        'slide-in':    'slide-in 0.3s ease-out',
        'fade-in':     'fade-in 0.4s ease-out',
        'fadeIn':      'fade-in 0.3s ease-out',
        'scan':        'scan 3s linear infinite',
        'blink':       'blink 1s step-end infinite',
        'glow':        'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'pulse-green': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(0,255,136,0.4)' },
          '50%':       { boxShadow: '0 0 0 8px rgba(0,255,136,0)' },
        },
        'slide-in': {
          from: { transform: 'translateX(-12px)', opacity: '0' },
          to:   { transform: 'translateX(0)',     opacity: '1' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'scan': {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(400%)' },
        },
        'blink': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
        'glow': {
          from: { textShadow: '0 0 4px #00ff88' },
          to:   { textShadow: '0 0 12px #00ff88, 0 0 20px #00ff8840' },
        },
      },
    },
  },
  plugins: [],
}
