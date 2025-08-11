export interface UsageTotals {
  apiCalls: number;
  estCostCents: number;
}

export interface DailyUsagePoint {
  date: string; // ISO date string
  calls: number;
}

export interface RouteUsageRow {
  route: string;
  calls: number;
  last_used: string; // ISO date string
}

export interface UseUsageResult {
  totals: UsageTotals;
  daily: DailyUsagePoint[];
  byRoute: RouteUsageRow[];
}