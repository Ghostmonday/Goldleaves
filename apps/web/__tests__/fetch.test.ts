import wrappedFetch, { setPlanLimitModal } from '../src/lib/fetch';

describe('fetch wrapper', () => {
  let originalFetch: typeof global.fetch;
  let mockModal: { show: jest.Mock; hide: jest.Mock };

  beforeEach(() => {
    originalFetch = global.fetch;
    global.fetch = jest.fn();
    
    mockModal = {
      show: jest.fn(),
      hide: jest.fn()
    };
    setPlanLimitModal(mockModal);
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  it('should pass through normal responses unchanged', async () => {
    const mockResponse = {
      status: 200,
      ok: true,
      json: async () => ({ data: 'test' })
    };
    
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

    const response = await wrappedFetch('/test');
    
    expect(response).toBe(mockResponse);
    expect(mockModal.show).not.toHaveBeenCalled();
  });

  it('should handle 429 with plan_limit_exceeded error', async () => {
    const mockResponse = {
      status: 429,
      ok: false,
      clone: () => ({
        json: async () => ({ error: 'plan_limit_exceeded' })
      })
    };
    
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

    const response = await wrappedFetch('/test');
    
    expect(response).toBe(mockResponse);
    expect(mockModal.show).toHaveBeenCalledTimes(1);
  });

  it('should ignore 429 without plan_limit_exceeded error', async () => {
    const mockResponse = {
      status: 429,
      ok: false,
      clone: () => ({
        json: async () => ({ error: 'rate_limited' })
      })
    };
    
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

    const response = await wrappedFetch('/test');
    
    expect(response).toBe(mockResponse);
    expect(mockModal.show).not.toHaveBeenCalled();
  });

  it('should handle JSON parsing errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    
    const mockResponse = {
      status: 429,
      ok: false,
      clone: () => ({
        json: async () => { throw new Error('Invalid JSON'); }
      })
    };
    
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

    const response = await wrappedFetch('/test');
    
    expect(response).toBe(mockResponse);
    expect(mockModal.show).not.toHaveBeenCalled();
    expect(consoleSpy).toHaveBeenCalledWith('Could not parse 429 response as JSON:', expect.any(Error));
    
    consoleSpy.mockRestore();
  });

  it('should pass through fetch parameters correctly', async () => {
    const mockResponse = { status: 200, ok: true };
    (global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse);

    const init = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test: 'data' })
    };

    await wrappedFetch('/test', init);
    
    expect(global.fetch).toHaveBeenCalledWith('/test', init);
  });
});