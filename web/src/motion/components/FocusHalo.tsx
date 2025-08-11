import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useReduceMotion } from '../ReduceMotionProvider';
import { durations, easings, zIndices } from '../motionSpec';

interface FocusHaloProps {
  /** Child element to wrap with focus halo */
  children: React.ReactElement;
  /** Custom halo color (CSS color value) */
  haloColor?: string;
  /** Halo thickness in pixels */
  thickness?: number;
  /** Border radius of the halo */
  borderRadius?: number;
  /** Offset from the element edge */
  offset?: number;
}

/**
 * Component that renders an animated focus ring for keyboard focus only.
 * Uses outline: none on child and draws a motion.div halo on focus-visible.
 * Respects reduced motion preferences.
 */
export const FocusHalo: React.FC<FocusHaloProps> = ({
  children,
  haloColor = '#3b82f6', // Default blue
  thickness = 2,
  borderRadius = 4,
  offset = 2,
}) => {
  const { reduced } = useReduceMotion();
  const [isFocusVisible, setIsFocusVisible] = useState(false);
  const childRef = useRef<HTMLElement>(null);

  // Handle focus-visible detection
  useEffect(() => {
    const element = childRef.current;
    if (!element) return;

    const handleFocus = (event: FocusEvent) => {
      // Only show halo for keyboard focus (focus-visible)
      if (event.target === element && element.matches(':focus-visible')) {
        setIsFocusVisible(true);
      }
    };

    const handleBlur = () => {
      setIsFocusVisible(false);
    };

    element.addEventListener('focus', handleFocus);
    element.addEventListener('blur', handleBlur);

    return () => {
      element.removeEventListener('focus', handleFocus);
      element.removeEventListener('blur', handleBlur);
    };
  }, []);

  // Clone child with ref and remove outline
  const childWithRef = React.cloneElement(children, {
    ref: childRef,
    style: {
      ...children.props.style,
      outline: 'none',
      position: 'relative',
    },
  });

  const haloVariants = {
    hidden: {
      opacity: 0,
      scale: reduced ? 1 : 0.95,
    },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: reduced ? 0 : durations.fast / 1000,
        ease: easings.standard,
      },
    },
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {childWithRef}
      <AnimatePresence>
        {isFocusVisible && (
          <motion.div
            variants={haloVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            style={{
              position: 'absolute',
              top: -offset,
              left: -offset,
              right: -offset,
              bottom: -offset,
              border: `${thickness}px solid ${haloColor}`,
              borderRadius: borderRadius + offset,
              pointerEvents: 'none',
              zIndex: zIndices.tooltip,
            }}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>
    </div>
  );
};

/**
 * Higher-order component version of FocusHalo for easier composition.
 */
export const withFocusHalo = <P extends object>(
  Component: React.ComponentType<P>,
  haloProps?: Omit<FocusHaloProps, 'children'>
) => {
  const WrappedComponent = React.forwardRef<any, P>((props, ref) => (
    <FocusHalo {...haloProps}>
      <Component {...(props as any)} ref={ref} />
    </FocusHalo>
  ));

  WrappedComponent.displayName = `withFocusHalo(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};