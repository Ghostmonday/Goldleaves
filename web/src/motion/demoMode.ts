/**
 * Demo mode utilities for enabling and checking demo mode state
 */

let _isDemoMode = false;

/**
 * Enable demo mode by reading environment variables and URL parameters
 */
export function enableDemoMode(): boolean {
  // Check environment variables (Vite format)
  const envDemo = import.meta.env.VITE_DEMO_MODE === '1' || 
                  import.meta.env.DEMO_MODE === '1';
  
  // Check URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const urlDemo = urlParams.get('demo') === '1';
  
  _isDemoMode = envDemo || urlDemo;
  
  if (_isDemoMode) {
    // Add body classes for demo mode
    document.body.classList.add('demo-mode', 'demo-cursor');
  }
  
  return _isDemoMode;
}

/**
 * Check if demo mode is currently enabled
 */
export function isDemoMode(): boolean {
  return _isDemoMode;
}