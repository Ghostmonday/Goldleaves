/**
 * Billing-related TypeScript types
 */

export interface BillingSummary {
  totalUsageCents: number;
  currentBalanceCents: number;
  nextBillingDate: string;
}

export interface UseBillingResult {
  data: BillingSummary | null;
  loading: boolean;
  error: string | null;
}