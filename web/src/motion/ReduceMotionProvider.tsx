import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { ReducedMotion, shouldReduceMotion } from './motionSpec';

interface ReduceMotionContextValue {
  /** Whether motion should be reduced based on current mode */
  reduced: boolean;
  /** Current motion preference mode */
  mode: ReducedMotion;
  /** Toggle to next mode or set specific mode */
  toggle: (next?: ReducedMotion) => void;
}

const ReduceMotionContext = createContext<ReduceMotionContextValue | null>(null);

const STORAGE_KEY = 'reduce-motion-preference';

interface ReduceMotionProviderProps {
  children: React.ReactNode;
}

/**
 * Provider that manages reduced motion preferences with system detection,
 * user override, and localStorage persistence.
 */
export const ReduceMotionProvider: React.FC<ReduceMotionProviderProps> = ({ children }) => {
  // Initialize from localStorage or default to system
  const [mode, setMode] = useState<ReducedMotion>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && Object.values(ReducedMotion).includes(stored as ReducedMotion)) {
        return stored as ReducedMotion;
      }
    } catch {
      // localStorage might not be available
    }
    return ReducedMotion.System;
  });

  const [reduced, setReduced] = useState(() => shouldReduceMotion(mode));

  // Update reduced state when mode changes
  useEffect(() => {
    setReduced(shouldReduceMotion(mode));
  }, [mode]);

  // Listen for system preference changes when in system mode
  useEffect(() => {
    if (mode !== ReducedMotion.System) return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = () => setReduced(mediaQuery.matches);
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [mode]);

  // Update document element data attribute for CSS hooks
  useEffect(() => {
    document.documentElement.setAttribute('data-reduce-motion', reduced.toString());
  }, [reduced]);

  // Persist mode to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // localStorage might not be available
    }
  }, [mode]);

  const toggle = useCallback((next?: ReducedMotion) => {
    if (next) {
      setMode(next);
      return;
    }

    // Cycle through modes: system -> reduce -> allow -> system
    switch (mode) {
      case ReducedMotion.System:
        setMode(ReducedMotion.Reduce);
        break;
      case ReducedMotion.Reduce:
        setMode(ReducedMotion.Allow);
        break;
      case ReducedMotion.Allow:
        setMode(ReducedMotion.System);
        break;
    }
  }, [mode]);

  return (
    <ReduceMotionContext.Provider value={{ reduced, mode, toggle }}>
      {children}
    </ReduceMotionContext.Provider>
  );
};

/**
 * Hook to access reduced motion context.
 * @returns Object with reduced state, mode, and toggle function
 */
export const useReduceMotion = (): ReduceMotionContextValue => {
  const context = useContext(ReduceMotionContext);
  if (!context) {
    throw new Error('useReduceMotion must be used within a ReduceMotionProvider');
  }
  return context;
};