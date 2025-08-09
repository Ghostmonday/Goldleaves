import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.tsx'
import { ReduceMotionProvider } from './motion/ReduceMotionProvider.tsx'
import { isDemoModeEnabled, enableDemoMode } from './motion/demoMode.ts'
import './styles/tokens.css'
import './index.css'

// Enable demo mode if configured
if (isDemoModeEnabled()) {
  enableDemoMode()
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ReduceMotionProvider>
        <App />
      </ReduceMotionProvider>
    </BrowserRouter>
  </React.StrictMode>,
)