# Billing Upgrade Flow Implementation

This document describes the implementation of the upgrade flow that connects the frontend UI to Stripe checkout.

## 🎯 Features Implemented

### Backend API
- **POST /api/v1/billing/checkout** - Creates Stripe checkout sessions
- **GET /billing/success** - Payment success return page
- **GET /billing/cancel** - Payment cancelled return page
- Authentication and tenancy validation
- BILLING_MOCK=1 environment variable support

### Frontend Integration
- Usage dashboard with upgrade button
- 429 rate limit modal with upgrade CTA
- Global fetch wrapper with error handling
- Automatic redirect to Stripe checkout
- Success and cancel return pages

### Testing
- Comprehensive backend tests
- Frontend integration tests
- Mock and real Stripe integration paths

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Set billing mock mode for development/testing
export BILLING_MOCK=1
```

### 2. Start the Server
```bash
# From the project root
python -m uvicorn routers.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the Frontend
- Usage Dashboard: `http://localhost:8000/static/usage.html`
- API Documentation: `http://localhost:8000/docs`

## 📡 API Endpoints

### Create Checkout Session
```http
POST /api/v1/billing/checkout
Content-Type: application/json
Authorization: Bearer <jwt-token>

{
  "plan": "Pro" | "Team"
}
```

**Response (200 OK):**
```json
{
  "url": "https://checkout.stripe.com/pay/cs_test_..."
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied for tenant
- `422 Unprocessable Entity` - Invalid plan

### Return Pages
- `GET /billing/success?session_id=<id>&plan=<plan>` - Success page
- `GET /billing/cancel` - Cancellation page

## 🔧 Configuration

### Environment Variables
```bash
# Enable billing mock mode (development)
BILLING_MOCK=1

# Production Stripe configuration (when BILLING_MOCK=0)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
FRONTEND_URL=https://app.goldleaves.com
```

### Plans Configuration
The system supports two subscription plans:
- **Pro** - $29/month, unlimited documents, 10,000 API calls
- **Team** - $99/month, unlimited everything, team collaboration

## 🧪 Testing

### Run Backend Tests
```bash
python -m pytest tests/test_billing.py -v
```

### Run Frontend Tests
Open `http://localhost:8000/static/usage.html` in browser and check console for test results.

### Validate Implementation
```bash
python validate_billing.py
```

## 🔄 Usage Flow

### 1. User Hits Rate Limit (429)
- API returns 429 status
- Frontend shows rate limit modal
- User can select plan and upgrade

### 2. Usage Page Upgrade
- User visits usage dashboard
- Selects desired plan
- Clicks "Upgrade Now" button

### 3. Checkout Process
1. Frontend calls `POST /api/v1/billing/checkout`
2. Backend validates authentication/authorization
3. Backend creates Stripe checkout session
4. Frontend redirects to `response.url`
5. User completes payment on Stripe
6. Stripe redirects to success/cancel page

## 🔐 Security

### Authentication
- All billing endpoints require valid JWT token
- Token extracted from `Authorization: Bearer <token>` header
- Invalid/missing tokens return 401 Unauthorized

### Authorization
- Tenancy validation ensures user access to organization
- Multi-tenant setup supported via `get_current_tenant` dependency
- Unauthorized access returns 403 Forbidden

### Input Validation
- Plan validation ensures only "Pro" or "Team" plans
- Pydantic schemas validate all request/response data
- SQL injection protection via ORM

## 🎨 Frontend Architecture

### ApiClient Class
Global fetch wrapper that:
- Adds authentication headers automatically
- Handles 429 responses by showing modal
- Provides consistent error handling
- Surfaces errors gracefully to UI

### CheckoutHandler Class
Manages checkout flow:
- Creates checkout sessions via API
- Handles redirect to Stripe
- Manages plan selection
- Shows error messages

### 429 Modal
Rate limit modal that:
- Displays when API returns 429
- Allows plan selection
- Triggers checkout flow
- Closeable by user

## 🧩 Architecture

```
Frontend (Static HTML/JS)
    ↓ POST /api/v1/billing/checkout
FastAPI Router (routers/billing.py)
    ↓ Authentication & Authorization
Service Layer (services/billing_service.py)
    ↓ BILLING_MOCK=1 check
Stripe Service (Mock or Real)
    ↓ Return checkout URL
Frontend Redirect → Stripe Checkout
    ↓ Payment completion
Return Pages (/billing/success|cancel)
```

## 🔧 Development

### Adding New Plans
1. Update `PlanType` enum in `schemas/billing.py`
2. Add plan validation in `BillingService.create_checkout_session`
3. Update frontend plan selection options
4. Add plan-specific pricing in Stripe integration

### Customizing Mock URLs
Modify `StripeService._create_mock_checkout_session` in `services/billing_service.py`:

```python
# Custom mock URL format
checkout_url = f"https://your-mock-domain.com/checkout?plan={plan}&session={session_id}"
```

### Real Stripe Integration
Replace placeholder in `StripeService._create_real_checkout_session`:

```python
import stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
        'price': get_price_id_for_plan(plan),
        'quantity': 1,
    }],
    mode='subscription',
    success_url=f"{os.getenv('FRONTEND_URL')}/billing/success",
    cancel_url=f"{os.getenv('FRONTEND_URL')}/billing/cancel",
    metadata={'user_id': user_id, 'tenant_id': tenant_id}
)

return {"url": session.url}
```

## 📝 File Structure
```
├── routers/
│   ├── billing.py              # Billing API router
│   ├── dependencies.py         # Auth/tenant dependencies
│   └── main.py                 # Main FastAPI app (static files)
├── schemas/
│   └── billing.py              # Pydantic schemas
├── services/
│   └── billing_service.py      # Business logic & Stripe
├── static/
│   ├── usage.html              # Usage dashboard
│   ├── billing-success.html    # Success page
│   ├── billing-cancel.html     # Cancel page
│   └── frontend-tests.js       # Frontend tests
├── tests/
│   └── test_billing.py         # Backend tests
└── validate_billing.py         # Validation script
```

## 🐛 Troubleshooting

### Common Issues

**401 Unauthorized**
- Check JWT token is valid and not expired
- Verify Authorization header format: `Bearer <token>`
- Ensure auth middleware is configured correctly

**403 Forbidden**
- Verify user has access to the tenant/organization
- Check tenant validation logic in `get_current_tenant`

**Mock URLs not working**
- Ensure `BILLING_MOCK=1` is set in environment
- Check mock URL generation in billing service

**Frontend not loading**
- Verify static files are mounted correctly in main.py
- Check browser console for JavaScript errors
- Ensure paths match between frontend and backend

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 Success Metrics

The implementation successfully delivers:
- ✅ No breaking route changes (only additions)
- ✅ Works with BILLING_MOCK=1
- ✅ Authentication/authorization enforcement
- ✅ 429 modal integration
- ✅ Usage page upgrade button
- ✅ Stripe checkout redirect
- ✅ Success/cancel return pages
- ✅ Comprehensive test coverage
- ✅ Graceful error handling

## 📞 Support

For questions or issues with the billing implementation:
1. Check the validation script: `python validate_billing.py`
2. Review test coverage: `python -m pytest tests/test_billing.py -v`
3. Inspect API documentation: `http://localhost:8000/docs`
