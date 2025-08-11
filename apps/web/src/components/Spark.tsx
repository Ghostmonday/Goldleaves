import React from 'react';

export interface SparkProps {
  data: number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
  strokeWidth?: number;
  title?: string;
  'aria-label'?: string;
}

export const Spark: React.FC<SparkProps> = ({
  data,
  width = 200,
  height = 50,
  stroke = '#3b82f6', // Default blue color
  fill = 'none',
  strokeWidth = 2,
  title = 'Usage sparkline',
  'aria-label': ariaLabel = 'Usage trend over time'
}) => {
  if (!data || data.length === 0) {
    return (
      <svg width={width} height={height} aria-label="No data available">
        <text
          x={width / 2}
          y={height / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize="12"
          fill="#6b7280"
        >
          No data
        </text>
      </svg>
    );
  }

  // Calculate min and max values for scaling
  const minValue = Math.min(...data);
  const maxValue = Math.max(...data);
  const range = maxValue - minValue || 1; // Avoid division by zero
  
  // Add padding to prevent clipping
  const padding = 4;
  const chartWidth = width - (padding * 2);
  const chartHeight = height - (padding * 2);
  
  // Generate path points
  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth;
    const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;
    return `${x},${y}`;
  });

  const pathData = `M ${points.join(' L ')}`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={ariaLabel}
    >
      <title>{title}</title>
      <path
        d={pathData}
        stroke={stroke}
        strokeWidth={strokeWidth}
        fill={fill}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Add dots at each data point for better visibility */}
      {data.map((value, index) => {
        const x = padding + (index / (data.length - 1)) * chartWidth;
        const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;
        return (
          <circle
            key={index}
            cx={x}
            cy={y}
            r={2}
            fill={stroke}
          />
        );
      })}
    </svg>
  );
};