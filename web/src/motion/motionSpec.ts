/**
 * Motion specification constants for consistent animations across the application.
 * Defines durations, easings, z-indices, breakpoints, and spring presets.
 */

/** Animation duration constants in milliseconds */
export const durations = {
  fast: 200,
  normal: 400,
  slow: 800,
} as const;

/** Standard easing curves for smooth animations */
export const easings = {
  standard: [0.4, 0.0, 0.2, 1] as const,
  emphasized: [0.2, 0.0, 0, 1] as const,
  decel: [0.0, 0.0, 0.2, 1] as const,
} as const;

/** Z-index values for proper layering */
export const zIndices = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  backdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
  toast: 1080,
} as const;

/** Responsive breakpoints in pixels */
export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

/** Framer Motion spring presets for common animations */
export const springs = {
  gentle: {
    type: 'spring' as const,
    stiffness: 120,
    damping: 14,
    mass: 1,
  },
  bouncy: {
    type: 'spring' as const,
    stiffness: 400,
    damping: 17,
    mass: 1,
  },
  snappy: {
    type: 'spring' as const,
    stiffness: 500,
    damping: 30,
    mass: 1,
  },
} as const;

/** Reduced motion preference flags */
export enum ReducedMotion {
  System = 'system',
  Reduce = 'reduce',
  Allow = 'allow',
}

/** Helper to check if reduced motion should be applied */
export const shouldReduceMotion = (mode: ReducedMotion): boolean => {
  if (mode === ReducedMotion.Reduce) return true;
  if (mode === ReducedMotion.Allow) return false;
  
  // System preference
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/** Duration in CSS format (ms to s) */
export const durationToCss = (ms: number): string => `${ms / 1000}s`;

/** Convert easing array to CSS cubic-bezier */
export const easingToCss = (easing: readonly number[]): string => 
  `cubic-bezier(${easing.join(', ')})`;