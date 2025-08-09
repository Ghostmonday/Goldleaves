import { useState, useEffect } from 'react';
import { UseUsageResult, DailyUsagePoint, RouteUsageRow } from './types';

// Mock data for development and testing
const getMockData = (): UseUsageResult => {
  const today = new Date();
  const dailyData: DailyUsagePoint[] = [];
  
  // Generate 7 days of mock daily usage data
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    dailyData.push({
      date: date.toISOString().split('T')[0],
      calls: Math.floor(Math.random() * 1000) + 100 // Random between 100-1100
    });
  }

  const totalCalls = dailyData.reduce((sum, day) => sum + day.calls, 0);
  const usageRateCents = parseInt(process.env.USAGE_RATE_CENTS || '5', 10);

  const mockRoutes: RouteUsageRow[] = [
    {
      route: '/api/auth/login',
      calls: Math.floor(totalCalls * 0.3),
      last_used: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      route: '/api/documents/upload',
      calls: Math.floor(totalCalls * 0.25),
      last_used: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      route: '/api/documents/analyze',
      calls: Math.floor(totalCalls * 0.2),
      last_used: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      route: '/api/users/profile',
      calls: Math.floor(totalCalls * 0.15),
      last_used: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      route: '/api/admin/stats',
      calls: Math.floor(totalCalls * 0.1),
      last_used: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString()
    }
  ];

  return {
    totals: {
      apiCalls: totalCalls,
      estCostCents: Math.floor(totalCalls * usageRateCents)
    },
    daily: dailyData,
    byRoute: mockRoutes
  };
};

// TODO: Implement live data fetching
const getLiveData = async (): Promise<UseUsageResult> => {
  // Placeholder for future API calls to backend endpoints
  // Example endpoints:
  // - GET /api/usage/totals
  // - GET /api/usage/daily?days=7
  // - GET /api/usage/by-route
  
  throw new Error('Live data not yet implemented');
};

export const useUsage = (): UseUsageResult => {
  const [data, setData] = useState<UseUsageResult>(getMockData());
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const useLiveData = process.env.NEXT_PUBLIC_USE_LIVE_USAGE === '1' || 
                       process.env.USE_LIVE_USAGE === '1';

    if (useLiveData) {
      setIsLoading(true);
      getLiveData()
        .then(setData)
        .catch((error) => {
          console.warn('Failed to load live usage data, falling back to mock data:', error);
          setData(getMockData());
        })
        .finally(() => setIsLoading(false));
    } else {
      // Use mock data by default
      setData(getMockData());
    }
  }, []);

  return data;
};