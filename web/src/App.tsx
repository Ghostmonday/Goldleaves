import { Routes, Route, Link } from 'react-router-dom'
import { AnimateIn } from './motion/components/AnimateIn'
import { FocusHalo } from './motion/components/FocusHalo'
import MotionDemo from './pages/MotionDemo'

function App() {
  return (
    <div style={{ padding: '2rem' }}>
      <AnimateIn variant="slideUp" delay={100}>
        <header style={{ marginBottom: '2rem' }}>
          <h1 style={{ 
            margin: 0, 
            color: 'var(--color-primary)',
            fontSize: '2.5rem'
          }}>
            🌿 Goldleaves Motion System
          </h1>
          <p style={{ 
            color: 'var(--color-text-secondary)',
            fontSize: '1.1rem',
            margin: '0.5rem 0 1rem 0'
          }}>
            Framer Motion + Lottie integration with accessibility features
          </p>
        </header>
      </AnimateIn>

      <AnimateIn variant="fade" delay={300}>
        <nav style={{ marginBottom: '2rem' }}>
          <FocusHalo>
            <Link 
              to="/" 
              style={{
                textDecoration: 'none',
                color: 'var(--color-primary)',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                border: '1px solid var(--color-border-primary)',
                marginRight: '1rem',
                display: 'inline-block'
              }}
            >
              Home
            </Link>
          </FocusHalo>
          
          <FocusHalo>
            <Link 
              to="/demo/motion" 
              style={{
                textDecoration: 'none',
                color: 'var(--color-primary)',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                border: '1px solid var(--color-border-primary)',
                display: 'inline-block'
              }}
            >
              Motion Demo
            </Link>
          </FocusHalo>
        </nav>
      </AnimateIn>

      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/demo/motion" element={<MotionDemo />} />
        </Routes>
      </main>
    </div>
  )
}

function Home() {
  return (
    <AnimateIn variant="slideUp" delay={400}>
      <div>
        <h2>Welcome to Goldleaves</h2>
        <p>
          This is a demonstration of the motion system featuring:
        </p>
        <ul>
          <li>Framer Motion animations with variants</li>
          <li>Reduced motion accessibility support</li>
          <li>Lazy-loaded Lottie animations</li>
          <li>Focus management and keyboard navigation</li>
          <li>Demo mode with guided highlights</li>
        </ul>
        <p>
          Visit the <Link to="/demo/motion">Motion Demo</Link> page to see all features in action.
        </p>
      </div>
    </AnimateIn>
  )
}

export default App