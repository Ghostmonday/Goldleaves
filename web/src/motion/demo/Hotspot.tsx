import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useReduceMotion } from '../ReduceMotionProvider';

interface HotspotProps {
  /** Step index */
  stepIndex: number;
  /** Whether this hotspot is currently active */
  active: boolean;
  /** CSS selector for the target element */
  target: string;
  /** Optional label for accessibility */
  label?: string;
}

/**
 * Pulse highlight component that targets elements with .demo-step-* classes
 */
export function Hotspot({ stepIndex, active, target, label }: HotspotProps) {
  const { prefersReducedMotion } = useReduceMotion();
  const [targetElement, setTargetElement] = useState<Element | null>(null);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0, height: 0 });

  // Find and track target element
  useEffect(() => {
    const element = document.querySelector(target);
    setTargetElement(element);

    if (!element) {
      console.warn(`Hotspot target not found: ${target}`);
      return;
    }

    const updatePosition = () => {
      const rect = element.getBoundingClientRect();
      setPosition({
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
        height: rect.height,
      });
    };

    updatePosition();

    // Throttled resize handler
    let resizeTimer: number;
    const handleResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(updatePosition, 100);
    };

    // Throttled scroll handler
    let scrollTimer: number;
    const handleScroll = () => {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(updatePosition, 16); // ~60fps
    };

    window.addEventListener('resize', handleResize, { passive: true });
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(resizeTimer);
      clearTimeout(scrollTimer);
    };
  }, [target]);

  if (!targetElement || !active) {
    return null;
  }

  const motionProps = prefersReducedMotion
    ? {
        initial: { opacity: 1 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
      }
    : {
        initial: { opacity: 0, scale: 0.8 },
        animate: { 
          opacity: [0.7, 1, 0.7],
          scale: [1, 1.05, 1],
          transition: {
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }
        },
        exit: { opacity: 0, scale: 0.8 },
      };

  return (
    <AnimatePresence>
      {active && (
        <motion.div
          className="demo-hotspot"
          style={{
            position: 'absolute',
            top: position.top - 8,
            left: position.left - 8,
            width: position.width + 16,
            height: position.height + 16,
            pointerEvents: 'none',
            zIndex: 9998,
            border: '2px solid #3b82f6',
            borderRadius: '8px',
            background: 'rgba(59, 130, 246, 0.1)',
            backdropFilter: 'blur(2px)',
          }}
          {...motionProps}
          role="presentation"
          aria-label={label || `Step ${stepIndex + 1} highlight`}
        />
      )}
    </AnimatePresence>
  );
}