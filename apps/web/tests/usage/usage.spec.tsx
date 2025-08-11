import React from 'react';
import { render, screen } from '@testing-library/react';
import { useUsage } from '@/usage/useUsage';
import UsagePage from '@/pages/usage/index';

// Mock the useUsage hook
jest.mock('@/usage/useUsage');
const mockUseUsage = useUsage as jest.MockedFunction<typeof useUsage>;

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/usage',
  }),
}));

const mockUsageData = {
  totals: {
    apiCalls: 5430,
    estCostCents: 2715, // $27.15
  },
  daily: [
    { date: '2024-01-01', calls: 850 },
    { date: '2024-01-02', calls: 720 },
    { date: '2024-01-03', calls: 900 },
    { date: '2024-01-04', calls: 650 },
    { date: '2024-01-05', calls: 780 },
    { date: '2024-01-06', calls: 830 },
    { date: '2024-01-07', calls: 700 },
  ],
  byRoute: [
    {
      route: '/api/auth/login',
      calls: 1629,
      last_used: '2024-01-07T10:30:00Z',
    },
    {
      route: '/api/documents/upload',
      calls: 1357,
      last_used: '2024-01-07T09:15:00Z',
    },
    {
      route: '/api/documents/analyze',
      calls: 1086,
      last_used: '2024-01-07T08:45:00Z',
    },
    {
      route: '/api/users/profile',
      calls: 814,
      last_used: '2024-01-06T16:20:00Z',
    },
    {
      route: '/api/admin/stats',
      calls: 544,
      last_used: '2024-01-05T14:10:00Z',
    },
  ],
};

describe('Usage Dashboard', () => {
  beforeEach(() => {
    mockUseUsage.mockReturnValue(mockUsageData);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the usage dashboard page', () => {
    render(<UsagePage />);
    
    expect(screen.getByText('Usage Dashboard')).toBeInTheDocument();
  });

  it('displays summary cards with correct totals', () => {
    render(<UsagePage />);
    
    // Check total API calls
    expect(screen.getByText('Total API Calls')).toBeInTheDocument();
    expect(screen.getByText('5,430')).toBeInTheDocument();
    
    // Check estimated cost
    expect(screen.getByText('Estimated Cost')).toBeInTheDocument();
    expect(screen.getByText('$27.15')).toBeInTheDocument();
  });

  it('renders the 7-day sparkline chart', () => {
    render(<UsagePage />);
    
    expect(screen.getByText('7-Day Usage Trend')).toBeInTheDocument();
    
    // Check for the SVG sparkline (by role or title)
    const sparkline = screen.getByRole('img', { name: /usage trend over last 7 days/i });
    expect(sparkline).toBeInTheDocument();
    expect(sparkline.tagName).toBe('svg');
  });

  it('displays usage by route table with correct data', () => {
    render(<UsagePage />);
    
    // Check table header
    expect(screen.getByText('Usage by Route')).toBeInTheDocument();
    expect(screen.getByText('Route')).toBeInTheDocument();
    expect(screen.getByText('Calls')).toBeInTheDocument();
    expect(screen.getByText('Last Used')).toBeInTheDocument();
    
    // Check route data
    expect(screen.getByText('/api/auth/login')).toBeInTheDocument();
    expect(screen.getByText('1,629')).toBeInTheDocument();
    
    expect(screen.getByText('/api/documents/upload')).toBeInTheDocument();
    expect(screen.getByText('1,357')).toBeInTheDocument();
    
    expect(screen.getByText('/api/documents/analyze')).toBeInTheDocument();
    expect(screen.getByText('1,086')).toBeInTheDocument();
    
    expect(screen.getByText('/api/users/profile')).toBeInTheDocument();
    expect(screen.getByText('814')).toBeInTheDocument();
    
    expect(screen.getByText('/api/admin/stats')).toBeInTheDocument();
    expect(screen.getByText('544')).toBeInTheDocument();
  });

  it('uses mock data by default (fallback behavior)', () => {
    // Reset the mock to return different data to test fallback
    const fallbackData = {
      totals: { apiCalls: 0, estCostCents: 0 },
      daily: [],
      byRoute: [],
    };
    mockUseUsage.mockReturnValue(fallbackData);

    render(<UsagePage />);
    
    // Should still render without errors
    expect(screen.getByText('Usage Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Total API Calls')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('renders navigation correctly', () => {
    render(<UsagePage />);
    
    // Check navigation
    expect(screen.getByText('🌿 Goldleaves')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Usage' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Documents' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument();
  });
});

describe('useUsage hook behavior', () => {
  it('should use mock data when USE_LIVE_USAGE is not set', () => {
    // This tests the actual hook behavior with mock data
    const originalEnv = process.env.NEXT_PUBLIC_USE_LIVE_USAGE;
    delete process.env.NEXT_PUBLIC_USE_LIVE_USAGE;

    // Restore the original implementation for this test
    jest.unmock('@/usage/useUsage');
    
    const { useUsage: actualUseUsage } = require('@/usage/useUsage');
    const result = actualUseUsage();

    expect(result.totals.apiCalls).toBeGreaterThan(0);
    expect(result.totals.estCostCents).toBeGreaterThan(0);
    expect(result.daily).toHaveLength(7);
    expect(result.byRoute.length).toBeGreaterThan(0);

    // Restore
    if (originalEnv !== undefined) {
      process.env.NEXT_PUBLIC_USE_LIVE_USAGE = originalEnv;
    }
  });
});