import React, { Suspense, useState, useEffect } from 'react';
import { useReduceMotion } from '../ReduceMotionProvider';

// Lazy import Lottie to reduce bundle size
const Lottie = React.lazy(() => import('lottie-react'));

interface LottieIconProps {
  /** 
   * Animation source - can be:
   * - Dynamic import function: () => import('./animation.json')
   * - Direct URL string
   * - Animation data object
   */
  src: (() => Promise<any>) | string | object;
  /** Whether to loop the animation */
  loop?: boolean;
  /** Whether to autoplay (disabled if reduced motion is enabled) */
  autoplay?: boolean;
  /** Additional CSS class */
  className?: string;
  /** Animation width */
  width?: number | string;
  /** Animation height */
  height?: number | string;
  /** Callback when animation completes */
  onComplete?: () => void;
  /** Fallback content while loading */
  fallback?: React.ReactNode;
}

/**
 * Typed wrapper around lottie-react with lazy import of animation JSON.
 * Automatically respects reduced motion preferences.
 */
export const LottieIcon: React.FC<LottieIconProps> = ({
  src,
  loop = false,
  autoplay = true,
  className,
  width,
  height,
  onComplete,
  fallback = <div style={{ width, height }} className={className} />,
}) => {
  const { reduced } = useReduceMotion();
  const [animationData, setAnimationData] = useState<object | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadAnimation = async () => {
      try {
        setLoading(true);
        setError(null);

        let data: object;

        if (typeof src === 'function') {
          // Dynamic import
          const module = await src();
          data = module.default || module;
        } else if (typeof src === 'string') {
          // URL string
          const response = await fetch(src);
          if (!response.ok) {
            throw new Error(`Failed to load animation: ${response.statusText}`);
          }
          data = await response.json();
        } else {
          // Direct object
          data = src;
        }

        if (mounted) {
          setAnimationData(data);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load animation');
          setLoading(false);
        }
      }
    };

    loadAnimation();

    return () => {
      mounted = false;
    };
  }, [src]);

  // Show fallback while loading
  if (loading) {
    return <>{fallback}</>;
  }

  // Show error state
  if (error || !animationData) {
    return (
      <div 
        style={{ width, height }} 
        className={className}
        title={error || 'Failed to load animation'}
      >
        ⚠️
      </div>
    );
  }

  // For reduced motion, show only the first frame
  if (reduced) {
    return (
      <Suspense fallback={fallback}>
        <Lottie
          animationData={animationData}
          loop={false}
          autoplay={false}
          className={className}
          style={{ width, height }}
          onComplete={onComplete}
        />
      </Suspense>
    );
  }

  return (
    <Suspense fallback={fallback}>
      <Lottie
        animationData={animationData}
        loop={loop}
        autoplay={autoplay}
        className={className}
        style={{ width, height }}
        onComplete={onComplete}
      />
    </Suspense>
  );
};