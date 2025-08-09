import { useState, useEffect, useCallback } from 'react';
import fetch from '../lib/fetch';

export interface UsageData {
  unit: string;
  soft_cap: number;
  hard_cap: number;
  remaining: number;
}

export interface UseUsageResult {
  usage: UsageData | null;
  loading: boolean;
  error: string | null;
  softCapReached: boolean;
  refetch: () => void;
}

// Simple cache to avoid excessive API calls
export let cachedUsage: UsageData | null = null;
export let cacheTimestamp = 0;
const CACHE_DURATION = 30000; // 30 seconds

// Function to reset cache for testing
export function resetCache() {
  cachedUsage = null;
  cacheTimestamp = 0;
}

export function useUsage(): UseUsageResult {
  const [usage, setUsage] = useState<UsageData | null>(cachedUsage);
  const [loading, setLoading] = useState(!cachedUsage); // Start loading if no cache
  const [error, setError] = useState<string | null>(null);
  const [softCapReached, setSoftCapReached] = useState(false);

  const fetchUsage = useCallback(async () => {
    // Check cache first
    const now = Date.now();
    if (cachedUsage && (now - cacheTimestamp) < CACHE_DURATION) {
      setUsage(cachedUsage);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/billing/summary');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch usage data: ${response.status}`);
      }

      // Check for soft cap header
      const softCapHeader = response.headers.get('X-Plan-SoftCap');
      setSoftCapReached(Boolean(softCapHeader));

      const data = await response.json();
      
      // Transform API response to our interface
      const usageData: UsageData = {
        unit: data.unit || 'requests',
        soft_cap: data.soft_cap || 0,
        hard_cap: data.hard_cap || 0,
        remaining: data.remaining || 0
      };

      // Update cache
      cachedUsage = usageData;
      cacheTimestamp = now;
      
      setUsage(usageData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(message);
      console.error('Failed to fetch usage data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsage();
  }, [fetchUsage]);

  return {
    usage,
    loading,
    error,
    softCapReached,
    refetch: fetchUsage
  };
}