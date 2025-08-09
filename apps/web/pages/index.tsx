import React from 'react';
import Link from 'next/link';

export default function HomePage() {
  return (
    <div style={{ padding: '40px', fontFamily: 'system-ui, sans-serif', maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ color: '#333', marginBottom: '24px' }}>Goldleaves Web App</h1>
      
      <p style={{ fontSize: '16px', lineHeight: '1.6', color: '#666', marginBottom: '32px' }}>
        Welcome to the Goldleaves platform. This web application provides usage monitoring and plan management features.
      </p>
      
      <div style={{ 
        backgroundColor: '#f8f9fa', 
        padding: '20px', 
        borderRadius: '8px',
        border: '1px solid #dee2e6' 
      }}>
        <h2 style={{ marginTop: 0, marginBottom: '16px', color: '#495057' }}>Available Features</h2>
        
        <Link 
          href="/usage" 
          style={{ 
            display: 'inline-block',
            padding: '12px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '4px',
            fontWeight: '500',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#0056b3';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#007bff';
          }}
        >
          View Usage & Plan Limits
        </Link>
        
        <p style={{ fontSize: '14px', color: '#6c757d', marginTop: '16px', marginBottom: 0 }}>
          Monitor your API usage, view plan limits, and get notifications when approaching caps.
        </p>
      </div>
    </div>
  );
}