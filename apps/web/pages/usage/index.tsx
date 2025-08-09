import React from 'react';
import { Layout } from '@/components/Layout';
import { Spark } from '@/components/Spark';
import { useUsage } from '@/usage/useUsage';

const formatCurrency = (cents: number): string => {
  return `$${(cents / 100).toFixed(2)}`;
};

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString();
};

const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
  
  if (diffInHours < 1) return 'Less than an hour ago';
  if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
  
  return formatDate(dateString);
};

const SummaryCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
}> = ({ title, value, subtitle }) => (
  <div className="bg-white overflow-hidden shadow-sm rounded-lg">
    <div className="p-5">
      <div className="flex items-center">
        <div className="flex-1">
          <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
          <dd className="text-2xl font-bold text-gray-900">{value}</dd>
          {subtitle && (
            <dd className="text-sm text-gray-600 mt-1">{subtitle}</dd>
          )}
        </div>
      </div>
    </div>
  </div>
);

const UsagePage: React.FC = () => {
  const { totals, daily, byRoute } = useUsage();
  
  // Extract values for sparkline
  const sparklineData = daily.map(point => point.calls);
  
  return (
    <Layout title="Usage Dashboard">
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <SummaryCard
            title="Total API Calls"
            value={totals.apiCalls.toLocaleString()}
            subtitle="Last 7 days"
          />
          <SummaryCard
            title="Estimated Cost"
            value={formatCurrency(totals.estCostCents)}
            subtitle="Based on usage rate"
          />
        </div>

        {/* 7-Day Sparkline Chart */}
        <div className="bg-white overflow-hidden shadow-sm rounded-lg">
          <div className="p-5">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              7-Day Usage Trend
            </h3>
            <div className="flex items-center justify-center">
              <Spark
                data={sparklineData}
                width={400}
                height={80}
                stroke="#3b82f6"
                strokeWidth={3}
                title="7-day API usage trend"
                aria-label={`Usage trend over last 7 days, ranging from ${Math.min(...sparklineData)} to ${Math.max(...sparklineData)} calls per day`}
              />
            </div>
            <div className="mt-4 flex justify-between text-sm text-gray-500">
              <span>7 days ago</span>
              <span>Today</span>
            </div>
          </div>
        </div>

        {/* Usage by Route Table */}
        <div className="bg-white shadow-sm rounded-lg overflow-hidden">
          <div className="p-5 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Usage by Route</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="table-container w-full">
              <thead>
                <tr>
                  <th className="table-header">Route</th>
                  <th className="table-header">Calls</th>
                  <th className="table-header">Last Used</th>
                </tr>
              </thead>
              <tbody>
                {byRoute.map((route, index) => (
                  <tr key={route.route} className="table-row">
                    <td className="table-cell font-mono text-gray-900">
                      {route.route}
                    </td>
                    <td className="table-cell text-gray-900">
                      {route.calls.toLocaleString()}
                    </td>
                    <td className="table-cell text-gray-500">
                      {formatRelativeTime(route.last_used)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Environment Info (for debugging) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-sm text-yellow-800">
              <strong>Development Mode:</strong> Using{' '}
              {process.env.NEXT_PUBLIC_USE_LIVE_USAGE === '1' ? 'live' : 'mock'} data
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default UsagePage;