import React, { useState } from 'react'
import { AnimateIn } from '../motion/components/AnimateIn'
import { FocusHalo } from '../motion/components/FocusHalo'
import { LottieIcon } from '../motion/components/LottieIcon'
import { useReduceMotion } from '../motion/ReduceMotionProvider'
import { useDemoMode } from '../motion/useDemoMode'
import { markDemoStep } from '../motion/demoMode'

// Simple spinner animation data (lightweight alternative to external Lottie files)
const spinnerAnimation = {
  v: "5.7.4",
  fr: 60,
  ip: 0,
  op: 120,
  w: 100,
  h: 100,
  nm: "Spinner",
  ddd: 0,
  assets: [],
  layers: [
    {
      ddd: 0,
      ind: 1,
      ty: 4,
      nm: "Circle",
      sr: 1,
      ks: {
        o: { a: 0, k: 100 },
        r: {
          a: 1,
          k: [
            { i: { x: [0.833], y: [0.833] }, o: { x: [0.167], y: [0.167] }, t: 0, s: [0] },
            { t: 120, s: [360] }
          ]
        },
        p: { a: 0, k: [50, 50, 0] },
        a: { a: 0, k: [0, 0, 0] },
        s: { a: 0, k: [100, 100, 100] }
      },
      ao: 0,
      shapes: [
        {
          ty: "gr",
          it: [
            {
              d: 1,
              ty: "el",
              s: { a: 0, k: [60, 60] },
              p: { a: 0, k: [0, 0] }
            },
            {
              ty: "st",
              c: { a: 0, k: [0.2, 0.4, 0.8, 1] },
              o: { a: 0, k: 100 },
              w: { a: 0, k: 8 },
              lc: 2,
              lj: 1,
              d: [{ n: "d", nm: "dash", v: { a: 0, k: 20 } }, { n: "g", nm: "gap", v: { a: 0, k: 20 } }]
            },
            {
              ty: "tr",
              p: { a: 0, k: [0, 0] },
              a: { a: 0, k: [0, 0] },
              s: { a: 0, k: [100, 100] },
              r: { a: 0, k: 0 },
              o: { a: 0, k: 100 }
            }
          ]
        }
      ],
      ip: 0,
      op: 900,
      st: 0,
      bm: 0
    }
  ]
}

const MotionDemo: React.FC = () => {
  const { reduced, mode, toggle } = useReduceMotion()
  const { enabled: demoMode, toggle: toggleDemo } = useDemoMode()
  const [selectedVariant, setSelectedVariant] = useState<'fade' | 'slideUp' | 'slideRight' | 'scaleIn'>('fade')

  // Mark demo steps when in demo mode
  React.useEffect(() => {
    if (demoMode && typeof document !== 'undefined') {
      setTimeout(() => {
        const controls = document.querySelector('.demo-controls')
        const variants = document.querySelector('.variant-showcase')
        const lottie = document.querySelector('.lottie-demo')
        
        if (controls) markDemoStep(controls as HTMLElement, 1)
        if (variants) markDemoStep(variants as HTMLElement, 2)
        if (lottie) markDemoStep(lottie as HTMLElement, 3)
      }, 500)
    }
  }, [demoMode])

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <AnimateIn variant="slideUp" delay={100}>
        <h1 style={{ color: 'var(--color-primary)', marginBottom: '2rem' }}>
          Motion System Demo
        </h1>
      </AnimateIn>

      {/* Controls Section */}
      <AnimateIn variant="fade" delay={200}>
        <section 
          className="demo-controls"
          style={{
            padding: '1.5rem',
            background: 'var(--color-bg-secondary)',
            borderRadius: '8px',
            marginBottom: '2rem',
            border: '1px solid var(--color-border-primary)'
          }}
        >
          <h2 style={{ marginTop: 0 }}>Motion Controls</h2>
          
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Reduce Motion: <span style={{ color: 'var(--color-primary)' }}>{mode}</span>
            </label>
            <FocusHalo>
              <button 
                onClick={() => toggle()}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '4px',
                  border: '1px solid var(--color-border-primary)',
                  background: 'var(--color-bg-primary)',
                  color: 'var(--color-text-primary)',
                  cursor: 'pointer'
                }}
              >
                Toggle Motion ({reduced ? 'Reduced' : 'Enabled'})
              </button>
            </FocusHalo>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Demo Mode: {demoMode ? 'ON' : 'OFF'}
            </label>
            <FocusHalo>
              <button 
                onClick={toggleDemo}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '4px',
                  border: '1px solid var(--color-border-primary)',
                  background: demoMode ? 'var(--color-success)' : 'var(--color-bg-primary)',
                  color: demoMode ? 'white' : 'var(--color-text-primary)',
                  cursor: 'pointer'
                }}
              >
                Toggle Demo Mode
              </button>
            </FocusHalo>
          </div>
        </section>
      </AnimateIn>

      {/* Variant Showcase */}
      <AnimateIn variant="slideRight" delay={300}>
        <section 
          className="variant-showcase"
          style={{
            padding: '1.5rem',
            background: 'var(--color-bg-secondary)',
            borderRadius: '8px',
            marginBottom: '2rem',
            border: '1px solid var(--color-border-primary)'
          }}
        >
          <h2 style={{ marginTop: 0 }}>Animation Variants</h2>
          
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Select Variant:
            </label>
            {(['fade', 'slideUp', 'slideRight', 'scaleIn'] as const).map((variant) => (
              <FocusHalo key={variant}>
                <button
                  onClick={() => setSelectedVariant(variant)}
                  style={{
                    padding: '0.5rem 1rem',
                    margin: '0.25rem',
                    borderRadius: '4px',
                    border: '1px solid var(--color-border-primary)',
                    background: selectedVariant === variant ? 'var(--color-primary)' : 'var(--color-bg-primary)',
                    color: selectedVariant === variant ? 'white' : 'var(--color-text-primary)',
                    cursor: 'pointer'
                  }}
                >
                  {variant}
                </button>
              </FocusHalo>
            ))}
          </div>

          <div 
            key={selectedVariant} // Force re-render to replay animation
            style={{
              padding: '2rem',
              background: 'var(--color-bg-primary)',
              borderRadius: '4px',
              border: '1px solid var(--color-border-secondary)',
              textAlign: 'center'
            }}
          >
            <AnimateIn variant={selectedVariant} duration={600}>
              <div style={{
                padding: '1rem',
                background: 'var(--color-primary)',
                color: 'white',
                borderRadius: '4px',
                display: 'inline-block'
              }}>
                {selectedVariant.toUpperCase()} Animation
              </div>
            </AnimateIn>
          </div>
        </section>
      </AnimateIn>

      {/* Lottie Demo */}
      <AnimateIn variant="scaleIn" delay={400}>
        <section 
          className="lottie-demo"
          style={{
            padding: '1.5rem',
            background: 'var(--color-bg-secondary)',
            borderRadius: '8px',
            marginBottom: '2rem',
            border: '1px solid var(--color-border-primary)'
          }}
        >
          <h2 style={{ marginTop: 0 }}>Lottie Animation</h2>
          
          <div style={{ textAlign: 'center' }}>
            <LottieIcon
              src={spinnerAnimation}
              loop={!reduced}
              autoplay={!reduced}
              width={100}
              height={100}
              onComplete={() => console.log('Animation completed!')}
            />
            <p style={{ color: 'var(--color-text-secondary)', marginTop: '1rem' }}>
              {reduced ? 'Static (Reduced Motion)' : 'Animated Spinner'}
            </p>
          </div>
        </section>
      </AnimateIn>

      {/* Staggered Animation Demo */}
      <AnimateIn variant="fade" delay={500}>
        <section style={{
          padding: '1.5rem',
          background: 'var(--color-bg-secondary)',
          borderRadius: '8px',
          border: '1px solid var(--color-border-primary)'
        }}>
          <h2 style={{ marginTop: 0 }}>Staggered Animation</h2>
          
          <AnimateIn variant="slideUp" stagger={100} delay={600}>
            {Array.from({ length: 5 }, (_, i) => (
              <div 
                key={i}
                style={{
                  padding: '1rem',
                  margin: '0.5rem',
                  background: 'var(--color-bg-primary)',
                  borderRadius: '4px',
                  border: '1px solid var(--color-border-secondary)',
                  display: 'inline-block'
                }}
              >
                Item {i + 1}
              </div>
            ))}
          </AnimateIn>
        </section>
      </AnimateIn>

      {demoMode && (
        <AnimateIn variant="fade" delay={700}>
          <div style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '1rem',
            background: 'var(--demo-highlight-color)',
            color: 'black',
            borderRadius: '8px',
            fontWeight: 'bold',
            fontSize: '14px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 'var(--z-toast)'
          }}>
            🎭 Demo Mode Active!<br />
            <small>Guided highlights enabled</small>
          </div>
        </AnimateIn>
      )}
    </div>
  )
}

export default MotionDemo