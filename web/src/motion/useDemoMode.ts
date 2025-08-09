import { useState, useEffect } from 'react';
import { isDemoModeEnabled, enableDemoMode, disableDemoMode } from './demoMode';

/**
 * React hook for demo mode state management.
 */
export const useDemoMode = () => {
  const [enabled, setEnabled] = useState(isDemoModeEnabled);

  useEffect(() => {
    if (enabled) {
      enableDemoMode();
    } else {
      disableDemoMode();
    }
  }, [enabled]);

  const toggle = () => setEnabled(!enabled);

  return { enabled, toggle };
};