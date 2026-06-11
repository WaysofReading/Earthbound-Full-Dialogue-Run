/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Edge-type palette, shared with the graph view (ported from
        // tools/visualize_entity.py EDGE_STYLES).
        edge: {
          unconditional: '#888888',
          flag: '#33aa77',
          menu: '#ee6633',
          case: '#aa44cc',
          call: '#3366cc',
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
