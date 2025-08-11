import { render, screen, waitFor } from '@testing-library/react';
import UsagePage from '../pages/usage/index';

// Mock the useUsage hook
jest.mock('../src/usage/useUsage', () => ({
  useUsage: jest.fn()
}));

import { useUsage } from '../src/usage/useUsage';

const mockUseUsage = useUsage as jest.MockedFunction<typeof useUsage>;

describe('UsagePage', () => {
  beforeEach(() => {
    mockUseUsage.mockClear();
  });

  it('should show loading state', () => {
    mockUseUsage.mockReturnValue({
      usage: null,
      loading: true,
      error: null,
      softCapReached: false,
      refetch: jest.fn()
    });

    render(<UsagePage />);
    
    expect(screen.getByText('Loading usage data...')).toBeInTheDocument();
  });

  it('should show error state', () => {
    const mockRefetch = jest.fn();
    mockUseUsage.mockReturnValue({
      usage: null,
      loading: false,
      error: 'Network error',
      softCapReached: false,
      refetch: mockRefetch
    });

    render(<UsagePage />);
    
    expect(screen.getByText('Error loading usage data: Network error')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('should display usage data and caps', async () => {
    const mockUsage = {
      unit: 'requests',
      soft_cap: 8000,
      hard_cap: 10000,
      remaining: 2000
    };

    mockUseUsage.mockReturnValue({
      usage: mockUsage,
      loading: false,
      error: null,
      softCapReached: false,
      refetch: jest.fn()
    });

    render(<UsagePage />);
    
    expect(screen.getByText('Usage Overview')).toBeInTheDocument();
    expect(screen.getByText('Plan Limits Summary')).toBeInTheDocument();
    
    // Check if caps are displayed
    expect(screen.getByText('8,000 requests')).toBeInTheDocument(); // soft cap
    expect(screen.getByText('10,000 requests')).toBeInTheDocument(); // hard cap
    expect(screen.getByText('2,000 requests')).toBeInTheDocument(); // remaining
    
    // Check usage percentage (80% used, 20% remaining)
    expect(screen.getByText('Usage Progress (80% used)')).toBeInTheDocument();
    expect(screen.getByText('20% remaining')).toBeInTheDocument();
  });

  it('should show soft cap banner when softCapReached is true', () => {
    const mockUsage = {
      unit: 'requests',
      soft_cap: 8000,
      hard_cap: 10000,
      remaining: 1000
    };

    mockUseUsage.mockReturnValue({
      usage: mockUsage,
      loading: false,
      error: null,
      softCapReached: true,
      refetch: jest.fn()
    });

    render(<UsagePage />);
    
    expect(screen.getByText(/Plan Limit Approaching/)).toBeInTheDocument();
  });

  it('should not show soft cap banner when softCapReached is false', () => {
    const mockUsage = {
      unit: 'requests',
      soft_cap: 8000,
      hard_cap: 10000,
      remaining: 5000
    };

    mockUseUsage.mockReturnValue({
      usage: mockUsage,
      loading: false,
      error: null,
      softCapReached: false,
      refetch: jest.fn()
    });

    render(<UsagePage />);
    
    expect(screen.queryByText(/Plan Limit Approaching/)).not.toBeInTheDocument();
  });
});