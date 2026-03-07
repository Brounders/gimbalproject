import { ThemeMode } from '../components/types';

export interface ThemeTokens {
  colors: {
    background: string;
    surface: string;
    surface2: string;
    border: string;
    borderStrong: string;
    text: string;
    textMuted: string;
    accent: string;
    warning: string;
    danger: string;
    success: string;
    hover: string;
    active: string;
  };
  radius: {
    md: string;
    lg: string;
    xl: string;
  };
  shadow: {
    soft: string;
    card: string;
  };
  typography: {
    base: string;
    secondary: string;
    section: string;
  };
  spacing: {
    s4: string;
    s8: string;
    s12: string;
    s16: string;
    s24: string;
  };
  motion: {
    quick: string;
  };
}

export const designTokens: Record<ThemeMode, ThemeTokens> = {
  dark: {
    colors: {
      background: '#0d1117',
      surface: '#111827',
      surface2: '#1a2233',
      border: '#2a3344',
      borderStrong: '#3a465c',
      text: '#e6edf3',
      textMuted: '#9aa7b8',
      accent: '#10a37f',
      warning: '#f4a524',
      danger: '#ef4444',
      success: '#22c55e',
      hover: '#232d40',
      active: '#2b3750',
    },
    radius: {
      md: '10px',
      lg: '12px',
      xl: '14px',
    },
    shadow: {
      soft: '0 1px 2px rgba(0,0,0,0.25)',
      card: '0 10px 30px rgba(0,0,0,0.25)',
    },
    typography: {
      base: '15px',
      secondary: '12px',
      section: '19px',
    },
    spacing: {
      s4: '4px',
      s8: '8px',
      s12: '12px',
      s16: '16px',
      s24: '24px',
    },
    motion: {
      quick: '180ms',
    },
  },
  light: {
    colors: {
      background: '#f6f8fb',
      surface: '#ffffff',
      surface2: '#f1f5f9',
      border: '#d4dce8',
      borderStrong: '#b5c0d3',
      text: '#111827',
      textMuted: '#5f6b7d',
      accent: '#10a37f',
      warning: '#b7791f',
      danger: '#dc2626',
      success: '#15803d',
      hover: '#e6ebf4',
      active: '#dbe3f1',
    },
    radius: {
      md: '10px',
      lg: '12px',
      xl: '14px',
    },
    shadow: {
      soft: '0 1px 2px rgba(16,24,40,0.07)',
      card: '0 10px 22px rgba(15,23,42,0.08)',
    },
    typography: {
      base: '15px',
      secondary: '12px',
      section: '19px',
    },
    spacing: {
      s4: '4px',
      s8: '8px',
      s12: '12px',
      s16: '16px',
      s24: '24px',
    },
    motion: {
      quick: '180ms',
    },
  },
};

export function toCssVars(theme: ThemeMode): Record<string, string> {
  const t = designTokens[theme];
  return {
    '--color-bg': t.colors.background,
    '--color-surface': t.colors.surface,
    '--color-surface-2': t.colors.surface2,
    '--color-border': t.colors.border,
    '--color-border-strong': t.colors.borderStrong,
    '--color-text': t.colors.text,
    '--color-text-muted': t.colors.textMuted,
    '--color-accent': t.colors.accent,
    '--color-warning': t.colors.warning,
    '--color-danger': t.colors.danger,
    '--color-success': t.colors.success,
    '--color-hover': t.colors.hover,
    '--color-active': t.colors.active,
    '--radius-md': t.radius.md,
    '--radius-lg': t.radius.lg,
    '--radius-xl': t.radius.xl,
    '--shadow-soft': t.shadow.soft,
    '--shadow-card': t.shadow.card,
    '--font-base': t.typography.base,
    '--font-secondary': t.typography.secondary,
    '--font-section': t.typography.section,
    '--space-4': t.spacing.s4,
    '--space-8': t.spacing.s8,
    '--space-12': t.spacing.s12,
    '--space-16': t.spacing.s16,
    '--space-24': t.spacing.s24,
    '--motion-quick': t.motion.quick,
  };
}
