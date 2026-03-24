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
          slate: {
            900: 'var(--strata-slate-900)',
            800: 'var(--strata-slate-800)',
            700: 'var(--strata-slate-700)',
            600: 'var(--strata-slate-600)',
            500: 'var(--strata-slate-500)',
            400: 'var(--strata-slate-400)',
            300: 'var(--strata-slate-300)',
            200: 'var(--strata-slate-200)',
            100: 'var(--strata-slate-100)',
          },
          stone: {
            900: 'var(--strata-stone-900)',
            800: 'var(--strata-stone-800)',
            700: 'var(--strata-stone-700)',
            600: 'var(--strata-stone-600)',
          },
          terracotta: 'var(--strata-terracotta)',
          amber: 'var(--strata-amber)',
          cream: 'var(--strata-cream)',
          ink: 'var(--strata-ink)',
          muted: 'var(--strata-muted)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
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
