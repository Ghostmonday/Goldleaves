import { renderHook, waitFor } from '@testing-library/react';
import { useUsage, resetCache } from '../src/usage/useUsage';

// Mock the wrapped fetch module
jest.mock('../src/lib/fetch', () => {
  return jest.fn();
});

import mockFetch from '../src/lib/fetch';

describe('useUsage hook', () => {
  beforeEach(() => {
    (mockFetch as jest.Mock).mockClear();
    resetCache(); // Reset cache for clean test state
  });

  it('should fetch usage data successfully', async () => {
    const mockUsageData = {
      unit: 'requests',
      soft_cap: 8000,
      hard_cap: 10000,
      remaining: 2000
    };

    (mockFetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      headers: {
        get: jest.fn().mockReturnValue(null)
      },
      json: async () => mockUsageData
    });

    const { result } = renderHook(() => useUsage());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.usage).toEqual(mockUsageData);
    expect(result.current.error).toBe(null);
    expect(result.current.softCapReached).toBe(false);
  });

  it('should detect soft cap when header is present', async () => {
    const mockUsageData = {
      unit: 'requests',
      soft_cap: 8000,
      hard_cap: 10000,
      remaining: 1000
    };

    (mockFetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      headers: {
        get: jest.fn().mockReturnValue('true')
      },
      json: async () => mockUsageData
    });

    const { result } = renderHook(() => useUsage());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.softCapReached).toBe(true);
  });

  it('should handle fetch errors', async () => {
    (mockFetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useUsage());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.usage).toBe(null);
  });

  it('should handle HTTP error responses', async () => {
    (mockFetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401
    });

    const { result } = renderHook(() => useUsage());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch usage data: 401');
  });
});