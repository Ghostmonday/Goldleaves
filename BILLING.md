# Billing and Subscription Management

This document describes the billing and subscription management system for the Gold Leaves application, which integrates with Stripe for payment processing and subscription management.

## Overview

The billing system provides:
- Stripe-powered subscription checkout flows
- Webhook-based subscription status updates
- Plan-based feature gating and authorization
- Support for both user-level and organization-level subscriptions
- Idempotent webhook processing for reliability

## Setup

### 1. Environment Configuration

Add the following variables to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...           # Your Stripe secret key
STRIPE_PUBLISHABLE_KEY=pk_test_...      # Your Stripe publishable key
STRIPE_WEBHOOK_SECRET=whsec_...         # Webhook endpoint secret from Stripe
```

### 2. Stripe Dashboard Configuration

1. Create products and prices in your Stripe dashboard:
   - **Pro Plan**: Monthly subscription (e.g., $29/month)
   - **Team Plan**: Monthly subscription (e.g., $99/month)

2. Update the price IDs in `billing/stripe.py`:
   ```python
   price_mapping = {
       PlanType.PRO: "price_1234567890",     # Replace with actual Price ID
       PlanType.TEAM: "price_0987654321",    # Replace with actual Price ID
   }
   ```

3. Configure webhooks in Stripe dashboard:
   - Endpoint URL: `https://yourdomain.com/billing/webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`

### 3. Database Migration

Run the entitlements migration:

```bash
alembic upgrade head
```

## Subscription Plans

### Available Plans

1. **Free Plan**
   - 1,000 API requests per month
   - 1 GB storage
   - 1 team member
   - Basic support

2. **Pro Plan** 
   - 50,000 API requests per month
   - 100 GB storage
   - 5 team members
   - Advanced analytics
   - Priority support

3. **Team Plan**
   - 200,000 API requests per month
   - 500 GB storage
   - 25 team members
   - Advanced analytics
   - Priority support
   - Custom integrations

### Plan Features

Features are stored as JSON in the `entitlements.features` column and can be checked using the entitlement service:

```python
from core.entitlements import EntitlementService

# Check if user has a specific feature
has_analytics = EntitlementService.check_feature_access(
    user, "advanced_analytics", tenant_id=org_id
)

# Get feature limit
api_limit = EntitlementService.get_feature_limit(
    user, "api_requests_per_month", tenant_id=org_id
)
```

## API Endpoints

### Create Checkout Session

**POST** `/billing/checkout`

Creates a Stripe checkout session for subscription upgrade.

```json
{
  "plan": "pro",
  "success_url": "https://yourapp.com/success",
  "cancel_url": "https://yourapp.com/cancel",
  "tenant_id": 123  // Optional, required for team plans
}
```

**Response:**
```json
{
  "url": "https://checkout.stripe.com/pay/cs_...",
  "plan": "pro",
  "message": "Checkout session created for pro plan"
}
```

### Webhook Handler

**POST** `/billing/webhook`

Processes Stripe webhook events. This endpoint is called by Stripe and should not be called directly.

### Get Subscription Status

**GET** `/billing/status`

Returns the current user's subscription status.

**Response:**
```json
{
  "plan": "pro",
  "active": true,
  "features": {
    "api_requests_per_month": 50000,
    "storage_gb": 100,
    "team_members": 5,
    "advanced_analytics": true,
    "priority_support": true
  },
  "seats": 5,
  "stripe_customer_id": "cus_...",
  "stripe_subscription_id": "sub_...",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

## Authorization and Feature Gating

### Plan-Based Authorization

Use the `@requires_plan` decorator to restrict endpoints to specific subscription plans:

```python
from core.entitlements import requires_plan

@router.get("/premium-feature")
@requires_plan("PRO", "TEAM")
def premium_endpoint():
    return {"message": "This requires Pro or Team plan"}

@router.get("/team-feature")
@requires_plan("TEAM", tenant_id_param="org_id")
def team_endpoint(org_id: int):
    return {"message": "This requires Team plan"}
```

### Feature-Based Authorization

Use the `@requires_feature` decorator for granular feature control:

```python
from core.entitlements import requires_feature

@router.get("/analytics")
@requires_feature("advanced_analytics")
def analytics_endpoint():
    return {"data": "analytics_data"}
```

### Manual Authorization Checks

For more complex authorization logic:

```python
from core.entitlements import EntitlementService
from fastapi import Depends, HTTPException

def custom_auth_check(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user has sufficient API quota
    limit = EntitlementService.get_feature_limit(
        user, "api_requests_per_month", db=db
    )
    
    # Your custom logic here
    if user_has_exceeded_quota(user, limit):
        raise HTTPException(403, "API quota exceeded")
    
    return user
```

## Webhook Processing

### Event Types Handled

- **checkout.session.completed**: Activates subscription after successful payment
- **invoice.payment_succeeded**: Renews/activates subscription
- **invoice.payment_failed**: Logs payment failure (subscription remains active for retries)
- **customer.subscription.updated**: Updates subscription status
- **customer.subscription.deleted**: Deactivates subscription

### Idempotency

Webhook processing is idempotent - the same event can be processed multiple times safely. Events are tracked to prevent duplicate processing.

### Error Handling

- Invalid webhooks return 400 Bad Request
- Processing errors are logged but return 200 OK to acknowledge receipt
- Failed payments don't immediately deactivate subscriptions (Stripe handles retries)

## Testing

### Running Tests

```bash
# Run all billing tests
pytest tests/billing/ -v

# Run specific test files
pytest tests/billing/test_stripe.py -v
pytest tests/billing/test_router.py -v
pytest tests/billing/test_entitlements.py -v
```

### Test Mode

When using Stripe test keys, all operations are in test mode:
- Use test card numbers (e.g., `4242424242424242`)
- No real charges are made
- Webhook events can be triggered from Stripe CLI

### Stripe CLI for Testing

Install Stripe CLI and forward webhooks to your local server:

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login to your Stripe account
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/billing/webhook

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.deleted
```

## Security Considerations

1. **Webhook Verification**: All webhooks are cryptographically verified using Stripe's signature
2. **Idempotency**: Events are processed idempotently to handle replays safely  
3. **Authorization**: Plan-based authorization prevents unauthorized access to premium features
4. **Database Constraints**: Unique constraints prevent duplicate entitlements

## Monitoring and Logs

Monitor these aspects in production:

1. **Webhook Processing**: Check logs for failed webhook processing
2. **Subscription Status**: Monitor entitlement activation/deactivation
3. **Failed Payments**: Track payment failures and subscription downgrades
4. **Feature Usage**: Monitor usage against plan limits

## Troubleshooting

### Common Issues

1. **Webhook Not Processing**
   - Check webhook secret configuration
   - Verify endpoint URL is accessible from Stripe
   - Check server logs for processing errors

2. **Entitlement Not Activated**
   - Verify webhook events are being received
   - Check Stripe dashboard for subscription status
   - Review server logs for processing errors

3. **Authorization Failing**
   - Verify user has active entitlement
   - Check plan requirements match user's subscription
   - Ensure organization-level entitlements are properly configured

### Development Tips

1. Use Stripe test mode for development
2. Test webhook replay scenarios
3. Verify authorization at both user and organization levels
4. Test subscription upgrade/downgrade flows
5. Validate feature limits and quotas

## Architecture Notes

### Database Design

- **Entitlements Table**: Central table storing subscription data
- **User/Organization Link**: Supports both user-level and org-level subscriptions
- **Feature Storage**: JSON column for flexible feature configuration
- **Stripe Integration**: Stores customer and subscription IDs for sync

### Service Architecture

- **StripeService**: Handles Stripe API interactions
- **EntitlementService**: Manages authorization and feature checks
- **BillingRouter**: Provides REST API endpoints
- **Authorization Decorators**: Simplify endpoint protection

This architecture ensures the billing system is robust, scalable, and easy to maintain while providing comprehensive subscription management capabilities.