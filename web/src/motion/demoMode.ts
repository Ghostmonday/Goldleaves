/**
 * Demo mode utilities for feature-flagged demonstration features.
 * Supports environment variables and query parameters for enabling demo mode.
 */

/**
 * Check if demo mode is enabled via environment variables or query parameters.
 * Supports:
 * - VITE_DEMO_MODE environment variable (for Vite)
 * - NEXT_PUBLIC_DEMO_MODE environment variable (for Next.js)
 * - ?demo=1 query parameter
 */
export const isDemoModeEnabled = (): boolean => {
  // Check Vite environment variables
  if (import.meta.env?.VITE_DEMO_MODE === '1' || import.meta.env?.VITE_DEMO_MODE === 'true') {
    return true;
  }

  // Check query parameters
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('demo') === '1';
  }

  return false;
};

/**
 * Enable demo mode by adding necessary body classes and styles.
 * This should be called on client mount when demo mode is enabled.
 */
export const enableDemoMode = (): void => {
  if (typeof document === 'undefined') return;

  const body = document.body;
  
  // Add demo mode classes
  body.classList.add('demo-mode', 'demo-cursor');
  
  console.log('🎭 Demo mode enabled! Guided highlights and high-contrast cursor are active.');
};

/**
 * Disable demo mode by removing demo classes.
 */
export const disableDemoMode = (): void => {
  if (typeof document === 'undefined') return;

  const body = document.body;
  body.classList.remove('demo-mode', 'demo-cursor');
};

/**
 * Add a demo step class to an element for guided highlighting.
 * @param element - The element to mark as a demo step
 * @param stepNumber - The step number (will create class demo-step-N)
 */
export const markDemoStep = (element: HTMLElement, stepNumber: number): void => {
  element.classList.add(`demo-step-${stepNumber}`);
};

/**
 * Remove demo step class from an element.
 * @param element - The element to unmark
 * @param stepNumber - The step number to remove
 */
export const unmarkDemoStep = (element: HTMLElement, stepNumber: number): void => {
  element.classList.remove(`demo-step-${stepNumber}`);
};

/**
 * React hook for demo mode state management.
 * Note: This function should be imported and used only in React components.
 * For non-React usage, use the standalone functions above.
 */
export const useDemoMode = () => {
  // This will be imported by components that already have React in scope
  throw new Error('useDemoMode should only be used in React components with proper React import');
};