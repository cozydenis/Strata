import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        strata: {
          // rgb(var() / <alpha-value>) lets Tailwind opacity modifiers (/70 etc.) work
          slate: {
            900: 'rgb(var(--strata-slate-900-rgb) / <alpha-value>)',
            800: 'rgb(var(--strata-slate-800-rgb) / <alpha-value>)',
            700: 'rgb(var(--strata-slate-700-rgb) / <alpha-value>)',
            600: 'rgb(var(--strata-slate-600-rgb) / <alpha-value>)',
            500: 'rgb(var(--strata-slate-500-rgb) / <alpha-value>)',
            400: 'rgb(var(--strata-slate-400-rgb) / <alpha-value>)',
            300: 'rgb(var(--strata-slate-300-rgb) / <alpha-value>)',
            200: 'rgb(var(--strata-slate-200-rgb) / <alpha-value>)',
            100: 'rgb(var(--strata-slate-100-rgb) / <alpha-value>)',
          },
          stone: {
            900: 'rgb(var(--strata-stone-900-rgb) / <alpha-value>)',
            800: 'rgb(var(--strata-stone-800-rgb) / <alpha-value>)',
            700: 'rgb(var(--strata-stone-700-rgb) / <alpha-value>)',
            600: 'rgb(var(--strata-stone-600-rgb) / <alpha-value>)',
          },
          terracotta: 'rgb(var(--strata-terracotta-rgb) / <alpha-value>)',
          amber: 'rgb(var(--strata-amber-rgb) / <alpha-value>)',
          sage: 'rgb(var(--strata-sage-rgb) / <alpha-value>)',
          cream: 'rgb(var(--strata-cream-rgb) / <alpha-value>)',
          ink: 'rgb(var(--strata-ink-rgb) / <alpha-value>)',
          muted: 'rgb(var(--strata-muted-rgb) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      fontSize: {
        '2xs': ['10px', { lineHeight: '1.4' }],
        'xs-11': ['11px', { lineHeight: '1.4' }],
        'sm-12': ['12px', { lineHeight: '1.5' }],
        'base-13': ['13px', { lineHeight: '1.5' }],
        'lg-15': ['15px', { lineHeight: '1.3' }],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
      },
      animation: {
        fadeSlideUp: 'fadeSlideUp 200ms ease-out',
        shimmer: 'shimmer 1.5s infinite linear',
      },
      keyframes: {
        fadeSlideUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backgroundSize: {
        shimmer: '200% 100%',
      },
    },
  },
  plugins: [],
};

export default config;
