import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HeroElement } from '../components/HeroAnimations'

const DashboardPage = () => {
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i: number) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: i * 0.1,
        duration: 0.5,
      },
    }),
  }

  return (
    <div className="page" style={{ alignItems: 'flex-start', paddingTop: '2rem' }}>
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{ marginBottom: '2rem' }}
        >
          <h1 style={{
            fontSize: '2rem',
            marginBottom: '0.5rem',
            color: 'white',
            fontWeight: 'bold',
          }}>
            Dashboard
          </h1>
          <p style={{ opacity: 0.8, marginBottom: '1rem' }}>
            Your personalized workspace with beautiful animations
          </p>
          <Link 
            to="/"
            style={{
              color: '#FFD700',
              opacity: 0.9,
              fontSize: '0.9rem',
            }}
          >
            ← Back to Home
          </Link>
        </motion.div>

        <motion.div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1.5rem',
            marginBottom: '2rem',
          }}
        >
          {[
            { title: 'Analytics', value: '1,234', trend: '+12%' },
            { title: 'Users', value: '567', trend: '+8%' },
            { title: 'Revenue', value: '$12,345', trend: '+15%' },
            { title: 'Growth', value: '89%', trend: '+5%' },
          ].map((item, i) => (
            <motion.div
              key={item.title}
              custom={i}
              initial="hidden"
              animate="visible"
              variants={cardVariants}
              whileHover={{ scale: 1.02, y: -5 }}
              style={{
                padding: '1.5rem',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '15px',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                cursor: 'pointer',
              }}
            >
              <h3 style={{ 
                fontSize: '0.9rem', 
                opacity: 0.8, 
                marginBottom: '0.5rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>
                {item.title}
              </h3>
              <div style={{ 
                fontSize: '2rem', 
                fontWeight: 'bold', 
                marginBottom: '0.5rem',
                color: 'white',
              }}>
                {item.value}
              </div>
              <div style={{ 
                color: '#4CAF50', 
                fontSize: '0.9rem',
                fontWeight: '500',
              }}>
                {item.trend}
              </div>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          style={{
            padding: '2rem',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '15px',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
          }}
        >
          <h2 style={{ 
            marginBottom: '1rem', 
            color: 'white',
            fontSize: '1.5rem',
          }}>
            Recent Activity
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[
              'User John Doe logged in',
              'New document created',
              'Analytics report generated',
              'System backup completed',
            ].map((activity, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + i * 0.1, duration: 0.4 }}
                style={{
                  padding: '0.75rem',
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  opacity: 0.9,
                }}
              >
                {activity}
              </motion.div>
            ))}
          </div>
        </motion.div>

        <HeroElement 
          id="dashboard-action"
          style={{
            display: 'flex',
            justifyContent: 'center',
            marginTop: '2rem',
          }}
        >
          <Link
            to="/profile"
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              background: 'rgba(255, 215, 0, 0.2)',
              border: '1px solid rgba(255, 215, 0, 0.4)',
              borderRadius: '25px',
              color: '#FFD700',
              fontSize: '1rem',
              fontWeight: '500',
              backdropFilter: 'blur(5px)',
            }}
          >
            View Profile →
          </Link>
        </HeroElement>
      </div>
    </div>
  )
}

export default DashboardPage