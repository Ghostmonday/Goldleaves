/**
 * Usage page component demonstrating the useUsage hook
 * Shows live usage totals and 7-day chart when USE_LIVE_USAGE=1
 */

import React from 'react';
import { useUsage, formatCost, formatCalls } from './useUsage';

interface UsagePageProps {
  className?: string;
}

export const UsagePage: React.FC<UsagePageProps> = ({ className = '' }) => {
  const { summary, dailyUsage, loading, error, refetch } = useUsage(7);

  if (loading) {
    return (
      <div className={`usage-page ${className}`}>
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading usage data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`usage-page ${className}`}>
      <div className="usage-header">
        <h1>Usage Dashboard</h1>
        {error && (
          <div className="error-banner">
            <p>⚠️ Using fallback data due to API error: {error}</p>
            <button onClick={refetch} className="retry-button">
              Retry
            </button>
          </div>
        )}
      </div>

      {/* Usage Summary */}
      {summary && (
        <div className="usage-summary">
          <h2>Current Period Summary</h2>
          <div className="summary-cards">
            <div className="summary-card">
              <h3>Total Calls</h3>
              <p className="metric">{formatCalls(summary.total_calls)}</p>
            </div>
            <div className="summary-card">
              <h3>Estimated Cost</h3>
              <p className="metric">{formatCost(summary.est_cost_cents)}</p>
            </div>
            <div className="summary-card">
              <h3>Period</h3>
              <p className="period">
                {new Date(summary.window_start).toLocaleDateString()} - {' '}
                {new Date(summary.window_end).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Daily Usage Chart */}
      <div className="daily-usage">
        <h2>7-Day Usage Trend</h2>
        <div className="chart-container">
          <SimpleBarChart data={dailyUsage} />
        </div>
        <div className="usage-table">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Calls</th>
              </tr>
            </thead>
            <tbody>
              {dailyUsage.map((item) => (
                <tr key={item.date}>
                  <td>{new Date(item.date).toLocaleDateString()}</td>
                  <td>{formatCalls(item.calls)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/**
 * Simple bar chart component for daily usage
 */
interface SimpleBarChartProps {
  data: Array<{ date: string; calls: number }>;
}

const SimpleBarChart: React.FC<SimpleBarChartProps> = ({ data }) => {
  if (!data.length) return <div>No data available</div>;

  const maxCalls = Math.max(...data.map(d => d.calls));

  return (
    <div className="simple-bar-chart">
      {data.map((item) => {
        const height = (item.calls / maxCalls) * 100;
        return (
          <div key={item.date} className="bar-container">
            <div 
              className="bar" 
              style={{ height: `${height}%` }}
              title={`${item.date}: ${item.calls} calls`}
            />
            <div className="bar-label">
              {new Date(item.date).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default UsagePage;