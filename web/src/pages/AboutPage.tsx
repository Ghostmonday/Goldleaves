import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HeroText, HeroElement } from '../components/HeroAnimations'

const AboutPage = () => {
  return (
    <div className="page">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            textAlign: 'center',
            maxWidth: '800px',
          }}
        >
          <HeroText 
            id="main-title" 
            as="h1"
            style={{
              fontSize: '2.5rem',
              marginBottom: '1.5rem',
              fontWeight: 'bold',
              background: 'linear-gradient(45deg, #FFD700, #FFA500)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            About Goldleaves
          </HeroText>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            style={{
              marginBottom: '2rem',
              lineHeight: '1.6',
            }}
          >
            <p style={{ marginBottom: '1rem', opacity: 0.9 }}>
              Goldleaves showcases modern web development techniques with beautiful
              animations and smooth transitions between routes.
            </p>
            <p style={{ opacity: 0.8 }}>
              Built with React, TypeScript, and Framer Motion for the best user experience.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '1.5rem',
              marginBottom: '2rem',
            }}
          >
            <div style={{
              padding: '1.5rem',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '15px',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}>
              <h3 style={{ marginBottom: '0.5rem', color: '#FFD700' }}>
                Route Transitions
              </h3>
              <p style={{ opacity: 0.8, fontSize: '0.9rem' }}>
                Smooth animations between page navigations using Framer Motion
              </p>
            </div>
            
            <div style={{
              padding: '1.5rem',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '15px',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}>
              <h3 style={{ marginBottom: '0.5rem', color: '#FFD700' }}>
                Hero Animations
              </h3>
              <p style={{ opacity: 0.8, fontSize: '0.9rem' }}>
                Shared element transitions that create continuity between pages
              </p>
            </div>
          </motion.div>

          <HeroElement 
            id="cta-button"
            style={{
              display: 'inline-block',
            }}
          >
            <Link
              to="/"
              style={{
                display: 'inline-block',
                padding: '12px 24px',
                background: 'rgba(255, 255, 255, 0.2)',
                border: '2px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '30px',
                color: 'white',
                fontSize: '1.1rem',
                fontWeight: '500',
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease',
              }}
            >
              Back to Home
            </Link>
          </HeroElement>
        </motion.div>
      </div>
    </div>
  )
}

export default AboutPage