import React from 'react';
import { useUsage } from '../../src/usage/useUsage';
import LimitBanner from '../../src/components/LimitBanner';

export default function UsagePage() {
  const { usage, loading, error, softCapReached, refetch } = useUsage();

  if (loading && !usage) {
    return (
      <div style={{ padding: '20px', fontFamily: 'system-ui, sans-serif' }}>
        <h1>Usage Overview</h1>
        <div>Loading usage data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', fontFamily: 'system-ui, sans-serif' }}>
        <h1>Usage Overview</h1>
        <div style={{ color: '#d9534f', padding: '12px', backgroundColor: '#f2dede', border: '1px solid #ebccd1', borderRadius: '4px' }}>
          Error loading usage data: {error}
        </div>
        <button 
          onClick={refetch}
          style={{ 
            marginTop: '12px',
            padding: '8px 16px',
            backgroundColor: '#337ab7',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  const usagePercentage = usage ? Math.round((usage.hard_cap - usage.remaining) / usage.hard_cap * 100) : 0;
  const remainingPercentage = 100 - usagePercentage;

  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui, sans-serif', maxWidth: '800px' }}>
      <h1 style={{ marginBottom: '24px', color: '#333' }}>Usage Overview</h1>
      
      {/* Soft cap banner */}
      <LimitBanner show={softCapReached} />
      
      {usage && (
        <div 
          style={{ 
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '24px',
            marginBottom: '20px'
          }}
        >
          <h2 style={{ marginTop: 0, marginBottom: '16px', color: '#495057' }}>Plan Limits Summary</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Soft Cap</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#fd7e14' }}>
                {usage.soft_cap.toLocaleString()} {usage.unit}
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Hard Cap</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc3545' }}>
                {usage.hard_cap.toLocaleString()} {usage.unit}
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>Remaining</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
                {usage.remaining.toLocaleString()} {usage.unit}
              </div>
            </div>
          </div>

          {/* Usage progress bar */}
          <div style={{ marginTop: '20px' }}>
            <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '8px' }}>
              Usage Progress ({usagePercentage}% used)
            </div>
            <div 
              style={{ 
                width: '100%',
                height: '20px',
                backgroundColor: '#e9ecef',
                borderRadius: '10px',
                overflow: 'hidden',
                position: 'relative'
              }}
            >
              <div 
                style={{ 
                  width: `${usagePercentage}%`,
                  height: '100%',
                  backgroundColor: usagePercentage > 80 ? '#dc3545' : usagePercentage > 60 ? '#fd7e14' : '#28a745',
                  transition: 'width 0.3s ease'
                }}
              />
              <div 
                style={{ 
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: usagePercentage > 50 ? 'white' : '#333'
                }}
              >
                {remainingPercentage}% remaining
              </div>
            </div>
          </div>

          {/* Refresh button */}
          <div style={{ marginTop: '20px', textAlign: 'right' }}>
            <button 
              onClick={refetch}
              disabled={loading}
              style={{ 
                padding: '8px 16px',
                backgroundColor: loading ? '#6c757d' : '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '14px'
              }}
            >
              {loading ? 'Refreshing...' : 'Refresh Usage'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}