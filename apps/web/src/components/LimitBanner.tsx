import React from 'react';

interface LimitBannerProps {
  show: boolean;
  upgradeUrl?: string;
}

export default function LimitBanner({ show, upgradeUrl = '/billing/upgrade' }: LimitBannerProps) {
  if (!show) return null;

  return (
    <div
      className="limit-banner"
      style={{
        backgroundColor: '#fef3cd',
        border: '1px solid #faebcc',
        borderRadius: '4px',
        padding: '12px 16px',
        margin: '16px 0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px'
      }}
      role="alert"
      aria-live="polite"
    >
      <div style={{ flex: 1 }}>
        <strong style={{ color: '#8a6d3b', fontSize: '14px', fontWeight: 600 }}>
          ⚠️ Plan Limit Approaching
        </strong>
        <p style={{ color: '#8a6d3b', fontSize: '14px', margin: '4px 0 0 0' }}>
          You&apos;re nearing your plan&apos;s usage limit. Consider upgrading to avoid service interruption.
        </p>
      </div>
      <a
        href={upgradeUrl}
        style={{
          backgroundColor: '#337ab7',
          color: 'white',
          textDecoration: 'none',
          padding: '6px 12px',
          borderRadius: '4px',
          fontSize: '14px',
          fontWeight: 500,
          transition: 'background-color 0.2s'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#286090';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = '#337ab7';
        }}
      >
        Upgrade Plan
      </a>
    </div>
  );
}