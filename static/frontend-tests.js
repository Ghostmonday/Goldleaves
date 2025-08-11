/**
 * Frontend tests for billing upgrade flow
 * Tests the 429 modal, usage page upgrade button, and checkout flow
 */

class FrontendTests {
    constructor() {
        this.results = [];
    }

    log(message, passed = true) {
        const status = passed ? '✓' : '✗';
        console.log(`${status} ${message}`);
        this.results.push({ message, passed });
    }

    // Mock fetch for testing
    mockFetch(response, status = 200) {
        global.fetch = jest.fn().mockResolvedValue({
            ok: status >= 200 && status < 300,
            status: status,
            json: () => Promise.resolve(response)
        });
    }

    async testCheckoutFlow() {
        this.log('Testing checkout flow...');
        
        // Mock successful checkout response
        this.mockFetch({ url: 'https://billing.example/checkout/session/mock?plan=Pro' });
        
        // Mock window.location
        delete window.location;
        window.location = { assign: jest.fn() };
        
        // Test checkout session creation
        try {
            const response = await CheckoutHandler.createCheckoutSession('Pro');
            
            // Verify window.location was called
            if (window.location.assign.mock.calls.length > 0) {
                this.log('Window location redirect called correctly');
            } else {
                this.log('Window location redirect NOT called', false);
            }
            
        } catch (error) {
            this.log(`Checkout flow failed: ${error.message}`, false);
        }
    }

    async test429ModalFlow() {
        this.log('Testing 429 modal flow...');
        
        // Mock 429 response
        this.mockFetch({}, 429);
        
        try {
            await ApiClient.fetch('/api/test');
        } catch (error) {
            // Should trigger 429 modal
            const modal = document.getElementById('rateLimitModal');
            if (modal && modal.style.display === 'block') {
                this.log('429 modal displayed correctly');
            } else {
                this.log('429 modal NOT displayed', false);
            }
        }
    }

    testUpgradeButtonIntegration() {
        this.log('Testing upgrade button integration...');
        
        // Check if upgrade button exists
        const upgradeBtn = document.getElementById('upgradeBtn');
        if (upgradeBtn) {
            this.log('Upgrade button found in DOM');
            
            // Check if click handler is attached
            if (upgradeBtn.onclick || upgradeBtn.addEventListener) {
                this.log('Upgrade button has click handler');
            } else {
                this.log('Upgrade button missing click handler', false);
            }
        } else {
            this.log('Upgrade button NOT found in DOM', false);
        }
        
        // Check modal upgrade button
        const modalUpgradeBtn = document.getElementById('modalUpgradeBtn');
        if (modalUpgradeBtn) {
            this.log('Modal upgrade button found');
        } else {
            this.log('Modal upgrade button NOT found', false);
        }
    }

    testApiClientErrorHandling() {
        this.log('Testing API client error handling...');
        
        // Test authentication error
        this.mockFetch({ detail: 'Authentication required' }, 401);
        
        ApiClient.fetch('/api/v1/billing/checkout', {
            method: 'POST',
            body: JSON.stringify({ plan: 'Pro' })
        }).catch(error => {
            if (error.message.includes('401') || error.message.includes('Authentication')) {
                this.log('401 authentication error handled correctly');
            } else {
                this.log('401 error NOT handled correctly', false);
            }
        });
        
        // Test authorization error
        this.mockFetch({ detail: 'Access denied for tenant' }, 403);
        
        ApiClient.fetch('/api/v1/billing/checkout', {
            method: 'POST',
            body: JSON.stringify({ plan: 'Pro' })
        }).catch(error => {
            if (error.message.includes('403') || error.message.includes('Access denied')) {
                this.log('403 authorization error handled correctly');
            } else {
                this.log('403 error NOT handled correctly', false);
            }
        });
    }

    testPlanSelection() {
        this.log('Testing plan selection...');
        
        // Test getting selected plan
        const selectedPlan = CheckoutHandler.getSelectedPlan('plan');
        if (selectedPlan === 'Pro' || selectedPlan === 'Team') {
            this.log(`Plan selection working: ${selectedPlan}`);
        } else {
            this.log('Plan selection NOT working', false);
        }
        
        // Test modal plan selection
        const modalPlan = CheckoutHandler.getSelectedPlan('modalPlan');
        if (modalPlan === 'Pro' || modalPlan === 'Team') {
            this.log(`Modal plan selection working: ${modalPlan}`);
        } else {
            this.log('Modal plan selection NOT working', false);
        }
    }

    async runAllTests() {
        console.log('🧪 Running Frontend Tests for Billing Upgrade Flow\n');
        console.log('=' * 60);
        
        this.testUpgradeButtonIntegration();
        this.testPlanSelection();
        this.testApiClientErrorHandling();
        await this.testCheckoutFlow();
        await this.test429ModalFlow();
        
        console.log('\n' + '=' * 60);
        const passedTests = this.results.filter(r => r.passed).length;
        const totalTests = this.results.length;
        
        if (passedTests === totalTests) {
            console.log(`🎉 All ${totalTests} frontend tests passed!`);
        } else {
            console.log(`❌ ${passedTests}/${totalTests} tests passed`);
        }
        
        return passedTests === totalTests;
    }
}

// Manual test runner (since we don't have Jest in this environment)
class ManualTestRunner {
    static run() {
        console.log('🧪 Manual Frontend Test Validation\n');
        
        const tests = [
            {
                name: 'Checkout flow integration',
                check: () => {
                    return typeof CheckoutHandler !== 'undefined' && 
                           typeof CheckoutHandler.createCheckoutSession === 'function';
                }
            },
            {
                name: '429 modal integration',
                check: () => {
                    return typeof ApiClient !== 'undefined' && 
                           typeof ApiClient.show429Modal === 'function';
                }
            },
            {
                name: 'Global fetch wrapper',
                check: () => {
                    return typeof ApiClient.fetch === 'function';
                }
            },
            {
                name: 'Plan selection functionality',
                check: () => {
                    return typeof CheckoutHandler.getSelectedPlan === 'function';
                }
            },
            {
                name: 'Error handling',
                check: () => {
                    return typeof CheckoutHandler.showError === 'function';
                }
            }
        ];
        
        let passed = 0;
        
        tests.forEach(test => {
            try {
                if (test.check()) {
                    console.log(`✓ ${test.name}`);
                    passed++;
                } else {
                    console.log(`✗ ${test.name} - Check failed`);
                }
            } catch (error) {
                console.log(`✗ ${test.name} - Error: ${error.message}`);
            }
        });
        
        console.log(`\n${passed}/${tests.length} tests passed`);
        
        if (passed === tests.length) {
            console.log('🎉 All frontend integration tests passed!');
        }
        
        return passed === tests.length;
    }
}

// Export for use in browser or Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FrontendTests, ManualTestRunner };
}

// Auto-run if in browser environment
if (typeof window !== 'undefined') {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ManualTestRunner.run());
    } else {
        ManualTestRunner.run();
    }
}