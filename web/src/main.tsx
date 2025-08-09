import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ReduceMotionProvider } from './motion/ReduceMotionProvider';
import { enableDemoMode } from './motion/demoMode';
import App from './App';
import './styles/demo.css';

// Enable demo mode on startup
enableDemoMode();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ReduceMotionProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ReduceMotionProvider>
  </React.StrictMode>,
);