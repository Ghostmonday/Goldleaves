/**
 * Usage module exports
 * Live metering endpoints integration with graceful fallback
 */

export { useUsage, formatCost, formatCalls } from './useUsage';
export { UsagePage } from './UsagePage';

// Types - define them here to avoid duplication
export interface UsageSummary {
  total_calls: number;
  est_cost_cents: number;
  window_start: string;
  window_end: string;
}

export interface DailyUsageItem {
  date: string;
  calls: number;
}

export interface DailyUsage {
  usage: DailyUsageItem[];
}

export interface UseUsageReturn {
  summary: UsageSummary | null;
  dailyUsage: DailyUsageItem[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}