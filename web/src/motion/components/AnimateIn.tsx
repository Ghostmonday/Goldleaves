import React from 'react';
import { motion, Variants } from 'framer-motion';
import { useReduceMotion } from '../ReduceMotionProvider';
import { durations, easings, springs } from '../motionSpec';

type AnimationVariant = 'fade' | 'slideUp' | 'slideRight' | 'scaleIn';

interface AnimateInProps {
  /** Element type to render */
  as?: keyof JSX.IntrinsicElements;
  /** Animation variant to use */
  variant?: AnimationVariant;
  /** Delay before animation starts (ms) */
  delay?: number;
  /** Animation duration (ms) */
  duration?: number;
  /** Distance for slide animations (px) */
  distance?: number;
  /** Only animate once when coming into view */
  once?: boolean;
  /** Stagger children animation (ms between each child) */
  stagger?: number;
  /** Additional className */
  className?: string;
  /** Child elements */
  children: React.ReactNode;
  /** Additional motion props */
  [key: string]: any;
}

/**
 * Reusable animation component wrapping Framer Motion with common variants.
 * Automatically respects reduced motion preferences.
 */
export const AnimateIn: React.FC<AnimateInProps> = ({
  as = 'div',
  variant = 'fade',
  delay = 0,
  duration = durations.normal,
  distance = 24,
  once = true,
  stagger = 0,
  className,
  children,
  ...motionProps
}) => {
  const { reduced } = useReduceMotion();
  const MotionComponent = motion[as as keyof typeof motion] as any;

  // Create variants based on the selected animation type
  const variants: Variants = React.useMemo(() => {
    const baseTransition = {
      duration: duration / 1000, // Convert to seconds
      ease: easings.standard,
      delay: delay / 1000,
    };

    switch (variant) {
      case 'fade':
        return {
          hidden: { opacity: 0 },
          visible: { 
            opacity: 1,
            transition: baseTransition,
          },
        };
      
      case 'slideUp':
        return {
          hidden: { 
            opacity: 0, 
            y: distance,
          },
          visible: {
            opacity: 1,
            y: 0,
            transition: baseTransition,
          },
        };
      
      case 'slideRight':
        return {
          hidden: {
            opacity: 0,
            x: -distance,
          },
          visible: {
            opacity: 1,
            x: 0,
            transition: baseTransition,
          },
        };
      
      case 'scaleIn':
        return {
          hidden: {
            opacity: 0,
            scale: 0.8,
          },
          visible: {
            opacity: 1,
            scale: 1,
            transition: {
              ...baseTransition,
              ...springs.gentle,
              duration: undefined, // Let spring handle timing
            },
          },
        };
      
      default:
        return {
          hidden: { opacity: 0 },
          visible: { opacity: 1, transition: baseTransition },
        };
    }
  }, [variant, duration, delay, distance]);

  // For reduced motion, show without animation
  if (reduced) {
    const Component = as;
    return <Component className={className} {...motionProps}>{children}</Component>;
  }

  // Handle staggered children
  const containerVariants: Variants | undefined = stagger > 0 ? {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: stagger / 1000,
      },
    },
  } : undefined;

  return (
    <MotionComponent
      initial="hidden"
      animate="visible"
      variants={containerVariants || variants}
      viewport={{ once }}
      className={className}
      {...motionProps}
    >
      {stagger > 0 ? (
        React.Children.map(children, (child, index) => (
          <motion.div key={index} variants={variants}>
            {child}
          </motion.div>
        ))
      ) : (
        children
      )}
    </MotionComponent>
  );
};