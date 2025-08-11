import { useState, useEffect } from 'react';
import { BillingSummary, UseBillingResult } from './types';

/**
 * Custom hook for fetching billing summary data
 */
export function useBilling(): UseBillingResult {
  const [data, setData] = useState<BillingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBilling = async () => {
      setLoading(true);
      setError(null);

      try {
        // Check if live billing is enabled
        const useLiveBilling = process.env.NEXT_PUBLIC_USE_LIVE_BILLING === '1';
        
        if (useLiveBilling) {
          const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
          const response = await fetch(`${apiBase}/api/v1/billing/summary`);
          
          if (!response.ok) {
            throw new Error(`Failed to fetch billing data: ${response.status}`);
          }
          
          const billingData = await response.json();
          
          // Convert from backend format to frontend format
          setData({
            totalUsageCents: billingData.total_usage_cents,
            currentBalanceCents: billingData.current_balance_cents,
            nextBillingDate: billingData.next_billing_date,
          });
        } else {
          // Return mock data
          const now = new Date();
          const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
          
          setData({
            totalUsageCents: 15400,  // $154.00
            currentBalanceCents: 2599,  // $25.99
            nextBillingDate: nextMonth.toISOString(),
          });
        }
      } catch (err) {
        console.error('Error fetching billing data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        
        // Fallback to mock data on error
        const now = new Date();
        const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
        
        setData({
          totalUsageCents: 15400,
          currentBalanceCents: 2599,
          nextBillingDate: nextMonth.toISOString(),
        });
      } finally {
        setLoading(false);
      }
    };

    fetchBilling();
  }, []);

  return { data, loading, error };
}