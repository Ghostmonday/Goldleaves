import { ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useLocation } from 'react-router-dom'

interface RouteTransitionProps {
  children: ReactNode
}

// Route transition variants
const routeVariants = {
  initial: {
    opacity: 0,
    scale: 0.95,
    y: 20,
  },
  in: {
    opacity: 1,
    scale: 1,
    y: 0,
  },
  out: {
    opacity: 0,
    scale: 1.05,
    y: -20,
  },
}

// Transition configuration
const routeTransition = {
  type: 'tween' as const,
  ease: 'anticipate' as const,
  duration: 0.4,
}

/**
 * RouteTransition wrapper component that provides smooth animations
 * between route changes using Framer Motion
 */
export const RouteTransition = ({ children }: RouteTransitionProps) => {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        initial="initial"
        animate="in"
        exit="out"
        variants={routeVariants}
        transition={routeTransition}
        style={{
          width: '100%',
          height: '100%',
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}