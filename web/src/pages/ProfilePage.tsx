import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HeroElement } from '../components/HeroAnimations'

const ProfilePage = () => {
  return (
    <div className="page" style={{ alignItems: 'flex-start', paddingTop: '2rem' }}>
      <div className="container">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          style={{
            maxWidth: '600px',
            margin: '0 auto',
            textAlign: 'center',
          }}
        >
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            style={{ marginBottom: '2rem' }}
          >
            <HeroElement
              id="profile-avatar"
              style={{
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                background: 'linear-gradient(45deg, #FFD700, #FFA500)',
                margin: '0 auto 1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '3rem',
                fontWeight: 'bold',
                color: 'white',
                boxShadow: '0 8px 32px rgba(255, 215, 0, 0.3)',
              }}
            >
              JD
            </HeroElement>
            
            <h1 style={{
              fontSize: '2rem',
              marginBottom: '0.5rem',
              color: 'white',
              fontWeight: 'bold',
            }}>
              John Doe
            </h1>
            
            <p style={{ 
              opacity: 0.8, 
              fontSize: '1.1rem',
              marginBottom: '0.5rem',
            }}>
              Frontend Developer
            </p>
            
            <p style={{ 
              opacity: 0.7, 
              fontSize: '0.9rem',
            }}>
              john.doe@goldleaves.com
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem',
            }}
          >
            {[
              { label: 'Projects', value: '12' },
              { label: 'Experience', value: '5y' },
              { label: 'Rating', value: '4.9★' },
              { label: 'Team', value: 'Frontend' },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6 + i * 0.1, duration: 0.4 }}
                whileHover={{ scale: 1.05 }}
                style={{
                  padding: '1rem',
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '10px',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                }}
              >
                <div style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: 'bold', 
                  color: '#FFD700',
                  marginBottom: '0.25rem',
                }}>
                  {stat.value}
                </div>
                <div style={{ 
                  fontSize: '0.8rem', 
                  opacity: 0.8,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}>
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.6 }}
            style={{
              padding: '1.5rem',
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '15px',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              marginBottom: '2rem',
              textAlign: 'left',
            }}
          >
            <h3 style={{ 
              marginBottom: '1rem', 
              color: 'white',
              fontSize: '1.2rem',
            }}>
              About
            </h3>
            <p style={{ 
              opacity: 0.8, 
              lineHeight: '1.6',
              fontSize: '0.95rem',
            }}>
              Passionate frontend developer with expertise in React, TypeScript, and modern 
              animation libraries. Loves creating beautiful user experiences with smooth 
              transitions and thoughtful interactions.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.6 }}
            style={{
              display: 'flex',
              gap: '1rem',
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            <HeroElement 
              id="dashboard-action"
              style={{ display: 'inline-block' }}
            >
              <Link
                to="/dashboard"
                style={{
                  display: 'inline-block',
                  padding: '10px 20px',
                  background: 'rgba(255, 215, 0, 0.2)',
                  border: '1px solid rgba(255, 215, 0, 0.4)',
                  borderRadius: '25px',
                  color: '#FFD700',
                  fontSize: '0.9rem',
                  fontWeight: '500',
                  backdropFilter: 'blur(5px)',
                }}
              >
                ← Dashboard
              </Link>
            </HeroElement>
            
            <Link
              to="/"
              style={{
                display: 'inline-block',
                padding: '10px 20px',
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '25px',
                color: 'white',
                fontSize: '0.9rem',
                fontWeight: '500',
                backdropFilter: 'blur(5px)',
              }}
            >
              Home
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}

export default ProfilePage