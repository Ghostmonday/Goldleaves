import { render, screen } from '@testing-library/react';
import LimitBanner from '../src/components/LimitBanner';

describe('LimitBanner', () => {
  it('should not render when show is false', () => {
    render(<LimitBanner show={false} />);
    
    expect(screen.queryByText('Plan Limit Approaching')).not.toBeInTheDocument();
  });

  it('should render when show is true', () => {
    render(<LimitBanner show={true} />);
    
    expect(screen.getByText(/Plan Limit Approaching/)).toBeInTheDocument();
    expect(screen.getByText(/nearing your plan's usage limit/)).toBeInTheDocument();
    expect(screen.getByText('Upgrade Plan')).toBeInTheDocument();
  });

  it('should use default upgrade URL', () => {
    render(<LimitBanner show={true} />);
    
    const upgradeLink = screen.getByText('Upgrade Plan');
    expect(upgradeLink).toHaveAttribute('href', '/billing/upgrade');
  });

  it('should use custom upgrade URL', () => {
    render(<LimitBanner show={true} upgradeUrl="/custom/upgrade" />);
    
    const upgradeLink = screen.getByText('Upgrade Plan');
    expect(upgradeLink).toHaveAttribute('href', '/custom/upgrade');
  });

  it('should have proper accessibility attributes', () => {
    render(<LimitBanner show={true} />);
    
    const banner = screen.getByRole('alert');
    expect(banner).toHaveAttribute('aria-live', 'polite');
  });
});