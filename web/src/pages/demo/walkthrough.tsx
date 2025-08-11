import { useEffect } from 'react';
import { useDemoFlow, DemoStep } from '../../motion/demo/useDemoFlow';
import { Hotspot } from '../../motion/demo/Hotspot';
import { Callout } from '../../motion/demo/Callout';
import { isDemoMode } from '../../motion/demoMode';

const demoSteps: DemoStep[] = [
  {
    target: '.demo-step-1',
    title: 'Welcome to the Demo',
    body: 'This is the first step of our guided tour. We\'ll walk you through the key features of this application.',
    placement: 'bottom',
  },
  {
    target: '.demo-step-2',
    title: 'Key Information',
    body: 'This section contains important information about how the demo system works and its accessibility features.',
    placement: 'auto',
  },
  {
    target: '.demo-step-3',
    title: 'Interactive Elements',
    body: 'Buttons and interactive elements are highlighted to show users where they can take action.',
    placement: 'top',
  },
  {
    target: '.demo-step-4',
    title: 'Additional Actions',
    body: 'Multiple interactive elements can be part of the same flow, showing different types of actions available.',
    placement: 'left',
  },
  {
    target: '.demo-step-5',
    title: 'Content Areas',
    body: 'Finally, we can highlight content areas and provide context about what users will find there.',
    placement: 'auto',
  },
];

/**
 * Demo walkthrough page showcasing the overlay system
 */
export default function DemoWalkthrough() {
  const demoFlow = useDemoFlow({
    steps: demoSteps,
    autoAdvanceMs: 5000, // 5 second auto-advance
    onComplete: () => {
      console.log('Demo completed!');
    },
  });

  const currentStep = demoFlow.steps[demoFlow.currentIndex];

  // Force enable demo mode for this page
  useEffect(() => {
    document.body.classList.add('demo-mode', 'demo-cursor');
    return () => {
      document.body.classList.remove('demo-mode', 'demo-cursor');
    };
  }, []);

  return (
    <div>
      <h1 className="demo-step-1" style={{ marginBottom: '24px', color: '#111827' }}>
        Demo Walkthrough
      </h1>
      
      <div style={{ marginBottom: '32px' }}>
        <p className="demo-step-2" style={{ 
          marginBottom: '20px', 
          lineHeight: '1.6',
          fontSize: '16px'
        }}>
          This page demonstrates a 5-step guided walkthrough using the demo overlay system. 
          The system includes hotspot highlights and positioned callouts that respect your 
          accessibility preferences, including reduced motion and keyboard navigation.
        </p>
        
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#eff6ff', 
          borderRadius: '8px',
          marginBottom: '24px'
        }}>
          <h3 style={{ margin: '0 0 12px 0', color: '#1e40af' }}>
            Accessibility Features
          </h3>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#1e40af' }}>
            <li>Keyboard navigation: Enter/Space to advance, Arrow Left for previous, Escape to close</li>
            <li>Screen reader compatible with proper ARIA labels and roles</li>
            <li>Respects prefers-reduced-motion for animations</li>
            <li>High contrast mode support</li>
            <li>Focus management and tab trapping</li>
          </ul>
        </div>
      </div>

      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ marginBottom: '16px' }}>Sample Interface Elements</h2>
        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
          <button 
            className="demo-step-3"
            style={{
              padding: '12px 24px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '500'
            }}
            onClick={() => console.log('Primary action clicked')}
          >
            Primary Action
          </button>
          <button 
            className="demo-step-4"
            style={{
              padding: '12px 24px',
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '500'
            }}
            onClick={() => console.log('Secondary action clicked')}
          >
            Secondary Action
          </button>
        </div>
      </div>

      <div 
        className="demo-step-5"
        style={{
          padding: '24px',
          backgroundColor: '#f9fafb',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          marginBottom: '32px'
        }}
      >
        <h3 style={{ margin: '0 0 16px 0', color: '#111827' }}>
          Important Content Section
        </h3>
        <p style={{ 
          margin: '0 0 16px 0', 
          lineHeight: '1.6',
          color: '#6b7280'
        }}>
          This is a sample content area that would contain important information 
          for users. The demo system can highlight any element on the page and 
          provide contextual information about it.
        </p>
        <div style={{
          padding: '12px',
          backgroundColor: '#dbeafe',
          borderRadius: '6px',
          fontSize: '14px',
          color: '#1e40af'
        }}>
          <strong>Tip:</strong> Demo callouts can be positioned automatically 
          or manually placed relative to their target elements.
        </div>
      </div>

      {/* Demo Controls */}
      <div style={{
        position: 'fixed',
        bottom: '20px',
        left: '20px',
        right: '20px',
        backgroundColor: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        padding: '16px',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
        zIndex: 10000
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
            Demo Controls
          </h4>
          <span style={{ fontSize: '14px', color: '#6b7280' }}>
            Step {demoFlow.currentIndex + 1} of {demoFlow.steps.length}
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={demoFlow.prev}
            disabled={demoFlow.currentIndex === 0}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              backgroundColor: demoFlow.currentIndex === 0 ? '#f9fafb' : 'white',
              color: demoFlow.currentIndex === 0 ? '#9ca3af' : '#374151',
              cursor: demoFlow.currentIndex === 0 ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            Previous
          </button>
          
          <button
            onClick={demoFlow.next}
            disabled={demoFlow.currentIndex === demoFlow.steps.length - 1}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '6px',
              backgroundColor: demoFlow.currentIndex === demoFlow.steps.length - 1 ? '#f9fafb' : '#3b82f6',
              color: demoFlow.currentIndex === demoFlow.steps.length - 1 ? '#9ca3af' : 'white',
              cursor: demoFlow.currentIndex === demoFlow.steps.length - 1 ? 'not-allowed' : 'pointer',
              fontSize: '14px'
            }}
          >
            Next
          </button>
          
          <button
            onClick={demoFlow.close}
            style={{
              padding: '8px 16px',
              border: '1px solid #dc2626',
              borderRadius: '6px',
              backgroundColor: 'white',
              color: '#dc2626',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Skip Demo
          </button>
          
          <div style={{ marginLeft: 'auto', fontSize: '12px', color: '#6b7280' }}>
            {demoFlow.paused ? 'Paused' : 'Auto-advancing...'}
          </div>
        </div>
      </div>

      {/* Render demo overlays when active */}
      {demoFlow.isActive && isDemoMode() && (
        <>
          <Hotspot
            stepIndex={demoFlow.currentIndex}
            active={true}
            target={currentStep.target}
            label={currentStep.title}
          />
          <Callout
            target={currentStep.target}
            placement={currentStep.placement}
            stepIndex={demoFlow.currentIndex}
            title={currentStep.title}
            body={currentStep.body}
            onNext={demoFlow.next}
            onPrev={demoFlow.prev}
            onClose={demoFlow.close}
            autoAdvanceMs={5000}
            isFirst={demoFlow.currentIndex === 0}
            isLast={demoFlow.currentIndex === demoFlow.steps.length - 1}
            onPause={demoFlow.setPaused}
          />
        </>
      )}
    </div>
  );
}