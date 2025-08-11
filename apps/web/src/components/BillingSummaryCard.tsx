import React from 'react';
import { useBilling } from '../billing/useBilling';
import { Card, CardHeader, CardContent, CardTitle } from '../components/Card';
import { formatCurrency, formatDate } from '../lib/utils';

interface BillingSummaryCardProps {
  className?: string;
}

export function BillingSummaryCard({ className = '' }: BillingSummaryCardProps) {
  const { data, loading, error } = useBilling();

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Billing</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="text-gray-500">Loading billing information...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error && !data) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Billing</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="text-red-500">Error loading billing information</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Billing</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                Current Balance
              </div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {formatCurrency(data.currentBalanceCents)}
              </div>
            </div>
            
            <div>
              <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                Total Usage This Period
              </div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {formatCurrency(data.totalUsageCents)}
              </div>
            </div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Next Billing Date
            </div>
            <div className="mt-1 text-lg font-medium text-gray-900">
              {formatDate(data.nextBillingDate)}
            </div>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="text-sm text-yellow-800">
                ⚠️ Using cached data due to: {error}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}