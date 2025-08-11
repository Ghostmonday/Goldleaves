import { ReactNode } from 'react'
import { motion } from 'framer-motion'

interface HeroElementProps {
  id: string
  children: ReactNode
  className?: string
  style?: React.CSSProperties
}

/**
 * HeroElement component for creating shared element transitions
 * between routes. Uses Framer Motion's layoutId for smooth morphing.
 */
export const HeroElement = ({ id, children, className, style }: HeroElementProps) => {
  return (
    <motion.div
      layoutId={id}
      className={className}
      style={style}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 30,
      }}
    >
      {children}
    </motion.div>
  )
}

interface HeroImageProps {
  id: string
  src: string
  alt: string
  className?: string
  style?: React.CSSProperties
}

/**
 * HeroImage component for image transitions between routes
 */
export const HeroImage = ({ id, src, alt, className, style }: HeroImageProps) => {
  return (
    <motion.img
      layoutId={id}
      src={src}
      alt={alt}
      className={className}
      style={style}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 30,
      }}
    />
  )
}

interface HeroTextProps {
  id: string
  children: ReactNode
  as?: keyof React.JSX.IntrinsicElements
  className?: string
  style?: React.CSSProperties
}

/**
 * HeroText component for text transitions between routes
 */
export const HeroText = ({ 
  id, 
  children, 
  as: Component = 'div', 
  className, 
  style 
}: HeroTextProps) => {
  const MotionComponent = motion[Component as keyof typeof motion] as any
  
  return (
    <MotionComponent
      layoutId={id}
      className={className}
      style={style}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 30,
      }}
    >
      {children}
    </MotionComponent>
  )
}