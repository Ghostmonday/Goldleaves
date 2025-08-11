// Global fetch wrapper that handles plan limit exceeded responses

interface PlanLimitModal {
  show: (upgradeUrl?: string) => void;
  hide: () => void;
}

// Global modal handler - can be replaced with actual modal implementation
let planLimitModal: PlanLimitModal = {
  show: (upgradeUrl = '/billing/upgrade') => {
    // Fallback modal using browser alert if no custom modal is set
    const upgrade = confirm(
      'You have reached your plan limit. Your account is temporarily restricted. ' +
      'Would you like to upgrade your plan to continue using the service?'
    );
    if (upgrade) {
      window.location.href = upgradeUrl;
    }
  },
  hide: () => {
    // Default implementation does nothing since we use browser confirm
  }
};

// Allow setting a custom modal handler
export function setPlanLimitModal(modal: PlanLimitModal) {
  planLimitModal = modal;
}

// Wrapped fetch function
async function wrappedFetch(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  const response = await globalThis.fetch(input, init);

  // Handle 429 with plan_limit_exceeded error
  if (response.status === 429) {
    try {
      const clonedResponse = response.clone();
      const data = await clonedResponse.json();
      
      if (data.error === 'plan_limit_exceeded') {
        planLimitModal.show();
      }
    } catch (err) {
      // If we can't parse JSON, just treat as normal 429
      console.warn('Could not parse 429 response as JSON:', err);
    }
  }

  return response;
}

// Export the wrapped fetch as default
export default wrappedFetch;

// Also export it as fetch for convenience
export const fetch = wrappedFetch;

// Type definitions for better TypeScript support
export type FetchFunction = typeof wrappedFetch;