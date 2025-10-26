import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes with proper precedence
 * Combines clsx for conditional classes and tailwind-merge for deduplication
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Elite utility functions for advanced styling
export function createGradient(colors: string[], direction: string = 'to right') {
  return `linear-gradient(${direction}, ${colors.join(', ')})`;
}

export function createGlassEffect(opacity: number = 0.1, blur: number = 10) {
  return {
    background: `rgba(255, 255, 255, ${opacity})`,
    backdropFilter: `blur(${blur}px)`,
    border: '1px solid rgba(255, 255, 255, 0.2)',
  };
}

export function createGlowEffect(color: string, intensity: number = 0.5) {
  return {
    boxShadow: `0 0 20px ${color}${Math.round(intensity * 255).toString(16).padStart(2, '0')}`,
  };
}

export function createShimmerEffect() {
  return {
    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 2s infinite',
  };
}

// Elite animation presets
export const eliteAnimations = {
  fadeInUp: 'animate-fade-in-up',
  fadeInDown: 'animate-fade-in-down',
  slideInLeft: 'animate-slide-left',
  slideInRight: 'animate-slide-right',
  scaleIn: 'animate-scale-in',
  bounceIn: 'animate-bounce-in',
  float: 'animate-float',
  glow: 'animate-glow',
  shimmer: 'animate-shimmer',
  gradient: 'animate-gradient',
} as const;

// Elite color presets
export const eliteColors = {
  primary: {
    light: '#0ea5e9',
    dark: '#0284c7',
    gradient: 'from-primary-500 to-primary-600',
  },
  secondary: {
    light: '#d946ef',
    dark: '#c026d3',
    gradient: 'from-secondary-500 to-secondary-600',
  },
  accent: {
    light: '#f97316',
    dark: '#ea580c',
    gradient: 'from-accent-500 to-accent-600',
  },
  success: {
    light: '#22c55e',
    dark: '#16a34a',
    gradient: 'from-success-500 to-success-600',
  },
  warning: {
    light: '#f59e0b',
    dark: '#d97706',
    gradient: 'from-warning-500 to-warning-600',
  },
  error: {
    light: '#ef4444',
    dark: '#dc2626',
    gradient: 'from-error-500 to-error-600',
  },
} as const;

// Elite spacing presets
export const eliteSpacing = {
  xs: '0.5rem',
  sm: '0.75rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
  '3xl': '4rem',
  '4xl': '6rem',
} as const;

// Elite border radius presets
export const eliteRadius = {
  none: '0',
  sm: '0.25rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.5rem',
  '3xl': '2rem',
  full: '9999px',
} as const;

// Elite shadow presets
export const eliteShadows = {
  sm: 'shadow-sm',
  md: 'shadow-md',
  lg: 'shadow-lg',
  xl: 'shadow-xl',
  '2xl': 'shadow-2xl',
  glass: 'shadow-glass',
  elite: 'shadow-elite',
  eliteLg: 'shadow-elite-lg',
  glow: 'shadow-glow',
  glowLg: 'shadow-glow-lg',
} as const;


