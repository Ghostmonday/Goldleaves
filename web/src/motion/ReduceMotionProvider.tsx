import React, { createContext, useContext, useEffect, useState } from 'react';

interface ReduceMotionContextType {
  prefersReducedMotion: boolean;
}

const ReduceMotionContext = createContext<ReduceMotionContextType>({
  prefersReducedMotion: false,
});

export function useReduceMotion() {
  return useContext(ReduceMotionContext);
}

interface ReduceMotionProviderProps {
  children: React.ReactNode;
}

/**
 * Provider that detects and provides reduced motion preference
 */
export function ReduceMotionProvider({ children }: ReduceMotionProviderProps) {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    
    // Update body data attribute for CSS
    if (mediaQuery.matches) {
      document.body.setAttribute('data-reduce-motion', 'true');
    } else {
      document.body.removeAttribute('data-reduce-motion');
    }

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return (
    <ReduceMotionContext.Provider value={{ prefersReducedMotion }}>
      {children}
    </ReduceMotionContext.Provider>
  );
}