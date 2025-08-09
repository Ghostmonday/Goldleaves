/**
 * Usage hook for live metering data
 * Fetches live usage data from API with graceful fallback to mock data
 */

import { useState, useEffect } from 'react';

// Types
interface UsageSummary {
  total_calls: number;
  est_cost_cents: number;
  window_start: string;
  window_end: string;
}

interface DailyUsageItem {
  date: string;
  calls: number;
}

interface DailyUsage {
  usage: DailyUsageItem[];
}

interface UseUsageReturn {
  summary: UsageSummary | null;
  dailyUsage: DailyUsageItem[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

// Mock data fallback
const mockSummary: UsageSummary = {
  total_calls: 1000,
  est_cost_cents: 2000,
  window_start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString(),
  window_end: new Date().toISOString(),
};

const generateMockDailyUsage = (days: number): DailyUsageItem[] => {
  const data: DailyUsageItem[] = [];
  const now = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    data.push({
      date: date.toISOString().split('T')[0],
      calls: Math.floor(Math.random() * 200) + 50, // Random calls between 50-250
    });
  }
  
  return data;
};

// Environment configuration
const USE_LIVE_USAGE = process.env.NEXT_PUBLIC_USE_LIVE_USAGE === '1';
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const USAGE_RATE_CENTS = parseInt(process.env.NEXT_PUBLIC_USAGE_RATE_CENTS || '2', 10);

/**
 * Hook to fetch usage data with live API integration and fallback
 */
export const useUsage = (days: number = 7): UseUsageReturn => {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [dailyUsage, setDailyUsage] = useState<DailyUsageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsageData = async () => {
    setLoading(true);
    setError(null);

    try {
      if (USE_LIVE_USAGE) {
        // Fetch live data from API
        const [summaryResponse, dailyResponse] = await Promise.all([
          fetch(`${API_BASE}/api/v1/usage/summary`, {
            headers: {
              'Authorization': `Bearer ${getAuthToken()}`,
              'Content-Type': 'application/json',
            },
          }),
          fetch(`${API_BASE}/api/v1/usage/daily?days=${days}`, {
            headers: {
              'Authorization': `Bearer ${getAuthToken()}`,
              'Content-Type': 'application/json',
            },
          }),
        ]);

        if (summaryResponse.ok && dailyResponse.ok) {
          const summaryData: UsageSummary = await summaryResponse.json();
          const dailyData: DailyUsage = await dailyResponse.json();

          // Apply usage rate if different from API
          const adjustedSummary = {
            ...summaryData,
            est_cost_cents: summaryData.total_calls * USAGE_RATE_CENTS,
          };

          setSummary(adjustedSummary);
          setDailyUsage(dailyData.usage);
        } else {
          throw new Error('Failed to fetch usage data from API');
        }
      } else {
        // Use mock data
        setSummary(mockSummary);
        setDailyUsage(generateMockDailyUsage(days));
      }
    } catch (err) {
      console.warn('Failed to fetch live usage data, falling back to mock data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      
      // Graceful fallback to mock data
      setSummary(mockSummary);
      setDailyUsage(generateMockDailyUsage(days));
    } finally {
      setLoading(false);
    }
  };

  const refetch = () => {
    fetchUsageData();
  };

  useEffect(() => {
    fetchUsageData();
  }, [days]); // Re-fetch when days parameter changes

  return {
    summary,
    dailyUsage,
    loading,
    error,
    refetch,
  };
};

/**
 * Get authentication token from storage or context
 * This is a placeholder - implement based on your auth system
 */
function getAuthToken(): string {
  // Placeholder implementation
  // In a real app, this would get the token from:
  // - localStorage/sessionStorage
  // - Auth context
  // - Cookies
  // - etc.
  return localStorage.getItem('auth_token') || '';
}

/**
 * Format cost in cents to currency display
 */
export const formatCost = (cents: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(cents / 100);
};

/**
 * Format large numbers with appropriate units
 */
export const formatCalls = (calls: number): string => {
  if (calls >= 1000000) {
    return `${(calls / 1000000).toFixed(1)}M`;
  } else if (calls >= 1000) {
    return `${(calls / 1000).toFixed(1)}K`;
  }
  return calls.toString();
};

export default useUsage;