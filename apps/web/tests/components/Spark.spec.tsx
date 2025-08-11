import React from 'react';
import { render, screen } from '@testing-library/react';
import { Spark } from '@/components/Spark';

describe('Spark Component', () => {
  const mockData = [10, 20, 15, 30, 25, 35, 40];

  it('renders SVG sparkline with data', () => {
    render(<Spark data={mockData} />);
    
    const svg = screen.getByRole('img');
    expect(svg).toBeInTheDocument();
    expect(svg.tagName).toBe('svg');
  });

  it('renders with custom dimensions', () => {
    render(<Spark data={mockData} width={300} height={100} />);
    
    const svg = screen.getByRole('img');
    expect(svg).toHaveAttribute('width', '300');
    expect(svg).toHaveAttribute('height', '100');
  });

  it('renders with custom stroke color', () => {
    render(<Spark data={mockData} stroke="#ff0000" />);
    
    const svg = screen.getByRole('img');
    const path = svg.querySelector('path');
    expect(path).toHaveAttribute('stroke', '#ff0000');
  });

  it('handles empty data gracefully', () => {
    render(<Spark data={[]} />);
    
    const svg = screen.getByRole('img');
    expect(svg).toBeInTheDocument();
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  it('handles single data point', () => {
    render(<Spark data={[50]} />);
    
    const svg = screen.getByRole('img');
    expect(svg).toBeInTheDocument();
    // Should render without errors
  });

  it('applies accessibility attributes', () => {
    const title = 'Custom sparkline title';
    const ariaLabel = 'Custom aria label';
    
    render(
      <Spark 
        data={mockData} 
        title={title}
        aria-label={ariaLabel}
      />
    );
    
    const svg = screen.getByRole('img');
    expect(svg).toHaveAttribute('aria-label', ariaLabel);
    expect(svg).toHaveAttribute('title', title);
  });

  it('renders data points as circles', () => {
    render(<Spark data={mockData} />);
    
    const svg = screen.getByRole('img');
    const circles = svg.querySelectorAll('circle');
    expect(circles).toHaveLength(mockData.length);
  });
});