import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HeroElement, HeroText } from '../components/HeroAnimations'

const HomePage = () => {
  return (
    <div className="page">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.8 }}
          style={{
            textAlign: 'center',
            maxWidth: '600px',
          }}
        >
          <HeroText 
            id="main-title" 
            as="h1"
            style={{
              fontSize: '3rem',
              marginBottom: '1rem',
              fontWeight: 'bold',
              background: 'linear-gradient(45deg, #FFD700, #FFA500)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Goldleaves
          </HeroText>
          
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            style={{
              fontSize: '1.2rem',
              marginBottom: '2rem',
              opacity: 0.9,
            }}
          >
            Experience beautiful route transitions and hero animations
          </motion.p>

          <HeroElement 
            id="cta-button"
            style={{
              display: 'inline-block',
              marginBottom: '2rem',
            }}
          >
            <Link
              to="/about"
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
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)'
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.3)'
              }}
            >
              Learn More
            </Link>
          </HeroElement>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            style={{
              display: 'flex',
              gap: '1rem',
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            <Link
              to="/dashboard"
              style={{
                padding: '8px 16px',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '20px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'white',
                fontSize: '0.9rem',
                backdropFilter: 'blur(5px)',
              }}
            >
              Dashboard
            </Link>
            <Link
              to="/profile"
              style={{
                padding: '8px 16px',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '20px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'white',
                fontSize: '0.9rem',
                backdropFilter: 'blur(5px)',
              }}
            >
              Profile
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}

export default HomePage