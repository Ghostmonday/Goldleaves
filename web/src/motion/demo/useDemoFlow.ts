import { useState, useCallback, useEffect, useRef } from 'react';

export interface DemoStep {
  /** CSS selector or element to target */
  target: string;
  /** Step title */
  title: string;
  /** Step description */
  body: string;
  /** Callout placement preference */
  placement?: 'top' | 'right' | 'bottom' | 'left' | 'auto';
}

export interface DemoFlowState {
  steps: DemoStep[];
  currentIndex: number;
  isActive: boolean;
  paused: boolean;
  next: () => void;
  prev: () => void;
  goTo: (index: number) => void;
  close: () => void;
  setPaused: (paused: boolean) => void;
}

interface UseDemoFlowOptions {
  steps: DemoStep[];
  autoAdvanceMs?: number;
  onComplete?: () => void;
}

/**
 * Hook for managing demo flow state and auto-advance behavior
 */
export function useDemoFlow({ 
  steps, 
  autoAdvanceMs, 
  onComplete 
}: UseDemoFlowOptions): DemoFlowState {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isActive, setIsActive] = useState(true);
  const [paused, setPaused] = useState(false);
  const autoAdvanceTimer = useRef<number>();
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const clearAutoAdvance = useCallback(() => {
    if (autoAdvanceTimer.current) {
      clearTimeout(autoAdvanceTimer.current);
      autoAdvanceTimer.current = undefined;
    }
  }, []);

  const startAutoAdvance = useCallback(() => {
    if (!autoAdvanceMs || paused || prefersReducedMotion) return;
    
    clearAutoAdvance();
    autoAdvanceTimer.current = setTimeout(() => {
      setCurrentIndex(prev => {
        const nextIndex = prev + 1;
        if (nextIndex >= steps.length) {
          setIsActive(false);
          onComplete?.();
          return prev;
        }
        return nextIndex;
      });
    }, autoAdvanceMs);
  }, [autoAdvanceMs, paused, prefersReducedMotion, steps.length, onComplete, clearAutoAdvance]);

  const next = useCallback(() => {
    clearAutoAdvance();
    setCurrentIndex(prev => {
      const nextIndex = prev + 1;
      if (nextIndex >= steps.length) {
        setIsActive(false);
        onComplete?.();
        return prev;
      }
      return nextIndex;
    });
  }, [steps.length, onComplete, clearAutoAdvance]);

  const prev = useCallback(() => {
    clearAutoAdvance();
    setCurrentIndex(prev => Math.max(0, prev - 1));
  }, [clearAutoAdvance]);

  const goTo = useCallback((index: number) => {
    clearAutoAdvance();
    if (index >= 0 && index < steps.length) {
      setCurrentIndex(index);
    }
  }, [steps.length, clearAutoAdvance]);

  const close = useCallback(() => {
    clearAutoAdvance();
    setIsActive(false);
  }, [clearAutoAdvance]);

  // Auto-advance effect
  useEffect(() => {
    if (isActive && !paused && autoAdvanceMs && !prefersReducedMotion) {
      startAutoAdvance();
    }
    return clearAutoAdvance;
  }, [currentIndex, isActive, paused, autoAdvanceMs, prefersReducedMotion, startAutoAdvance, clearAutoAdvance]);

  // Cleanup on unmount
  useEffect(() => {
    return clearAutoAdvance;
  }, [clearAutoAdvance]);

  // Handle focus/blur events to pause auto-advance
  useEffect(() => {
    const handleFocus = () => setPaused(false);
    const handleBlur = () => setPaused(true);

    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);

    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, []);

  return {
    steps,
    currentIndex,
    isActive,
    paused,
    next,
    prev,
    goTo,
    close,
    setPaused,
  };
}