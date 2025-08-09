import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import DemoWalkthrough from './pages/demo/walkthrough';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui, sans-serif' }}>
      <header style={{ marginBottom: '40px' }}>
        <h1 style={{ margin: '0 0 16px 0', color: '#111827' }}>
          🌿 Goldleaves Demo
        </h1>
        <nav>
          <Link 
            to="/" 
            style={{ 
              marginRight: '16px', 
              color: '#3b82f6',
              textDecoration: 'none'
            }}
          >
            Home
          </Link>
          <Link 
            to="/demo/walkthrough" 
            style={{ 
              color: '#3b82f6',
              textDecoration: 'none'
            }}
          >
            Demo Walkthrough
          </Link>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/demo/walkthrough" element={<DemoWalkthrough />} />
      </Routes>
    </div>
  );
}

function Home() {
  return (
    <div>
      <h2 className="demo-step-1" style={{ marginBottom: '16px' }}>
        Welcome to Goldleaves
      </h2>
      <p className="demo-step-2" style={{ marginBottom: '16px', lineHeight: '1.6' }}>
        This is a sample application demonstrating the demo mode overlay system.
        The system provides guided tours with keyboard accessibility and respects
        reduced motion preferences.
      </p>
      
      <div style={{ marginBottom: '24px' }}>
        <button 
          className="demo-step-3"
          style={{
            padding: '12px 24px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            marginRight: '12px'
          }}
        >
          Sample Button
        </button>
        <button 
          className="demo-step-4"
          style={{
            padding: '12px 24px',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Another Action
        </button>
      </div>

      <div 
        className="demo-step-5"
        style={{
          padding: '16px',
          backgroundColor: '#f3f4f6',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}
      >
        <h3 style={{ margin: '0 0 8px 0' }}>Sample Content Area</h3>
        <p style={{ margin: 0, fontSize: '14px', color: '#6b7280' }}>
          This content area demonstrates how demo mode can highlight different
          sections of your application interface.
        </p>
      </div>

      <div style={{ marginTop: '40px', padding: '20px', backgroundColor: '#fef3c7', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 12px 0', color: '#92400e' }}>
          Try the Demo Mode
        </h3>
        <p style={{ margin: '0 0 16px 0', color: '#92400e' }}>
          Navigate to the <Link to="/demo/walkthrough" style={{ color: '#92400e', fontWeight: '600' }}>Demo Walkthrough</Link> page 
          to see the overlay system in action, or add <code>?demo=1</code> to the URL to enable demo mode.
        </p>
        <p style={{ margin: 0, fontSize: '14px', color: '#92400e' }}>
          Use keyboard navigation: <kbd>Enter/Space</kbd> to advance, <kbd>Arrow Left</kbd> to go back, 
          and <kbd>Escape</kbd> to skip the demo.
        </p>
      </div>
    </div>
  );
}

export default App;