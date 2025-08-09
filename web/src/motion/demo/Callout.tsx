import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import { useReduceMotion } from '../ReduceMotionProvider';

interface CalloutProps {
  /** Target element or CSS selector */
  target: Element | string;
  /** Callout placement */
  placement?: 'top' | 'right' | 'bottom' | 'left' | 'auto';
  /** Current step index */
  stepIndex: number;
  /** Step title */
  title: string;
  /** Step body content */
  body: string;
  /** Next step callback */
  onNext?: () => void;
  /** Previous step callback */
  onPrev?: () => void;
  /** Auto advance time in ms */
  autoAdvanceMs?: number;
  /** Close/skip callback */
  onClose: () => void;
  /** Whether this is the first step */
  isFirst?: boolean;
  /** Whether this is the last step */
  isLast?: boolean;
  /** Pause callback for hover */
  onPause?: (paused: boolean) => void;
}

type PlacementType = 'top' | 'right' | 'bottom' | 'left';

/**
 * Positioned callout component with arrow pointing to target
 */
export function Callout({
  target,
  placement = 'auto',
  stepIndex,
  title,
  body,
  onNext,
  onPrev,
  autoAdvanceMs,
  onClose,
  isFirst = false,
  isLast = false,
  onPause,
}: CalloutProps) {
  const { prefersReducedMotion } = useReduceMotion();
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [actualPlacement, setActualPlacement] = useState<PlacementType>('bottom');
  const [targetElement, setTargetElement] = useState<Element | null>(null);
  const calloutRef = useRef<HTMLDivElement>(null);

  // Find target element
  useEffect(() => {
    const element = typeof target === 'string' ? document.querySelector(target) : target;
    setTargetElement(element);

    if (!element) {
      console.warn(`Callout target not found:`, target);
    }
  }, [target]);

  // Calculate position and placement
  useEffect(() => {
    if (!targetElement || !calloutRef.current) return;

    const calculatePosition = () => {
      const targetRect = targetElement.getBoundingClientRect();
      const calloutRect = calloutRef.current!.getBoundingClientRect();
      const viewport = {
        width: window.innerWidth,
        height: window.innerHeight,
      };

      let finalPlacement: PlacementType = placement === 'auto' ? 'bottom' : placement;
      let top = 0;
      let left = 0;

      // Auto-placement logic
      if (placement === 'auto') {
        const spaceTop = targetRect.top;
        const spaceBottom = viewport.height - targetRect.bottom;
        const spaceLeft = targetRect.left;
        const spaceRight = viewport.width - targetRect.right;

        if (spaceBottom >= 200) finalPlacement = 'bottom';
        else if (spaceTop >= 200) finalPlacement = 'top';
        else if (spaceRight >= 300) finalPlacement = 'right';
        else if (spaceLeft >= 300) finalPlacement = 'left';
        else finalPlacement = 'bottom'; // fallback
      }

      // Calculate position based on placement
      switch (finalPlacement) {
        case 'top':
          top = targetRect.top + window.scrollY - calloutRect.height - 16;
          left = targetRect.left + window.scrollX + targetRect.width / 2 - calloutRect.width / 2;
          break;
        case 'bottom':
          top = targetRect.bottom + window.scrollY + 16;
          left = targetRect.left + window.scrollX + targetRect.width / 2 - calloutRect.width / 2;
          break;
        case 'left':
          top = targetRect.top + window.scrollY + targetRect.height / 2 - calloutRect.height / 2;
          left = targetRect.left + window.scrollX - calloutRect.width - 16;
          break;
        case 'right':
          top = targetRect.top + window.scrollY + targetRect.height / 2 - calloutRect.height / 2;
          left = targetRect.right + window.scrollX + 16;
          break;
      }

      // Keep callout within viewport bounds
      const margin = 16;
      left = Math.max(margin, Math.min(left, viewport.width - calloutRect.width - margin));
      top = Math.max(margin, Math.min(top, window.scrollY + viewport.height - calloutRect.height - margin));

      setPosition({ top, left });
      setActualPlacement(finalPlacement);
    };

    calculatePosition();

    // Throttled handlers
    let resizeTimer: number;
    const handleResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(calculatePosition, 100);
    };

    let scrollTimer: number;
    const handleScroll = () => {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(calculatePosition, 16);
    };

    window.addEventListener('resize', handleResize, { passive: true });
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(resizeTimer);
      clearTimeout(scrollTimer);
    };
  }, [targetElement, placement]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowRight':
        case ' ':
        case 'Enter':
          e.preventDefault();
          if (!isLast) onNext?.();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (!isFirst) onPrev?.();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, onNext, onPrev, isFirst, isLast]);

  const motionProps = prefersReducedMotion
    ? {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
        transition: { duration: 0.15 },
      }
    : {
        initial: { opacity: 0, scale: 0.9, y: 20 },
        animate: { opacity: 1, scale: 1, y: 0 },
        exit: { opacity: 0, scale: 0.9, y: 20 },
        transition: { duration: 0.2, ease: 'easeOut' },
      };

  // Arrow styles based on placement
  const arrowStyle = {
    top: {
      bottom: '-8px',
      left: '50%',
      transform: 'translateX(-50%)',
      borderLeft: '8px solid transparent',
      borderRight: '8px solid transparent',
      borderTop: '8px solid white',
    },
    bottom: {
      top: '-8px',
      left: '50%',
      transform: 'translateX(-50%)',
      borderLeft: '8px solid transparent',
      borderRight: '8px solid transparent',
      borderBottom: '8px solid white',
    },
    left: {
      right: '-8px',
      top: '50%',
      transform: 'translateY(-50%)',
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
      borderLeft: '8px solid white',
    },
    right: {
      left: '-8px',
      top: '50%',
      transform: 'translateY(-50%)',
      borderTop: '8px solid transparent',
      borderBottom: '8px solid transparent',
      borderRight: '8px solid white',
    },
  };

  if (!targetElement) return null;

  return createPortal(
    <AnimatePresence>
      <motion.div
        ref={calloutRef}
        className="demo-callout"
        style={{
          position: 'absolute',
          top: position.top,
          left: position.left,
          zIndex: 9999,
          background: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          padding: '24px',
          maxWidth: '320px',
          minWidth: '280px',
        }}
        {...motionProps}
        onMouseEnter={() => onPause?.(true)}
        onMouseLeave={() => onPause?.(false)}
        tabIndex={0}
        role="dialog"
        aria-labelledby={`demo-callout-title-${stepIndex}`}
        aria-describedby={`demo-callout-body-${stepIndex}`}
      >
        {/* Arrow */}
        <div
          className="demo-callout-arrow"
          style={{
            position: 'absolute',
            width: 0,
            height: 0,
            ...arrowStyle[actualPlacement],
          }}
        />

        {/* Content */}
        <div className="demo-callout-content">
          <h3
            id={`demo-callout-title-${stepIndex}`}
            style={{
              margin: '0 0 12px 0',
              fontSize: '18px',
              fontWeight: '600',
              color: '#111827',
            }}
          >
            {title}
          </h3>
          <p
            id={`demo-callout-body-${stepIndex}`}
            style={{
              margin: '0 0 20px 0',
              fontSize: '14px',
              lineHeight: '1.5',
              color: '#6b7280',
            }}
          >
            {body}
          </p>

          {/* Controls */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', gap: '8px' }}>
              {!isFirst && (
                <button
                  onClick={onPrev}
                  style={{
                    padding: '8px 16px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    background: 'white',
                    color: '#374151',
                    fontSize: '14px',
                    cursor: 'pointer',
                  }}
                  tabIndex={0}
                >
                  Previous
                </button>
              )}
              {!isLast && (
                <button
                  onClick={onNext}
                  style={{
                    padding: '8px 16px',
                    border: 'none',
                    borderRadius: '6px',
                    background: '#3b82f6',
                    color: 'white',
                    fontSize: '14px',
                    cursor: 'pointer',
                  }}
                  tabIndex={0}
                  autoFocus
                >
                  Next
                </button>
              )}
              {isLast && (
                <button
                  onClick={onClose}
                  style={{
                    padding: '8px 16px',
                    border: 'none',
                    borderRadius: '6px',
                    background: '#10b981',
                    color: 'white',
                    fontSize: '14px',
                    cursor: 'pointer',
                  }}
                  tabIndex={0}
                  autoFocus
                >
                  Complete
                </button>
              )}
            </div>
            <button
              onClick={onClose}
              style={{
                padding: '4px',
                border: 'none',
                background: 'none',
                color: '#9ca3af',
                fontSize: '16px',
                cursor: 'pointer',
                borderRadius: '4px',
              }}
              tabIndex={0}
              title="Skip demo"
              aria-label="Skip demo"
            >
              ✕
            </button>
          </div>

          {/* Step indicator */}
          <div
            style={{
              marginTop: '16px',
              fontSize: '12px',
              color: '#9ca3af',
              textAlign: 'center',
            }}
          >
            Step {stepIndex + 1}
            {autoAdvanceMs && (
              <span style={{ marginLeft: '8px' }}>
                (Auto-advancing in {Math.round(autoAdvanceMs / 1000)}s)
              </span>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>,
    document.body
  );
}