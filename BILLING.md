# BILLING.md

## Stripe Webhook Integration

This document outlines the Stripe webhook setup and configuration for handling billing events in the Goldleaves application.

### Overview

The billing system integrates with Stripe to handle subscription events and automatically update user entitlements. The system processes two main webhook events:

- `checkout.session.completed` - When a user successfully completes checkout
- `customer.subscription.updated` - When subscription status changes (renewals, cancellations, plan changes)

### Configuration

#### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PRICE_PRO=price_your_pro_plan_price_id
STRIPE_PRICE_TEAM=price_your_team_plan_price_id
```

#### Stripe Dashboard Setup

1. **Create Webhook Endpoint**
   - Go to Stripe Dashboard → Developers → Webhooks
   - Click "Add endpoint"
   - URL: `https://yourdomain.com/billing/webhook`
   - Events to send:
     - `checkout.session.completed`
     - `customer.subscription.updated`

2. **Get Webhook Secret**
   - After creating the webhook, click on it
   - Copy the "Signing secret" and set it as `STRIPE_WEBHOOK_SECRET`

3. **Create Products and Prices**
   - Create products for Pro and Team plans
   - Create recurring prices for each product
   - Copy the price IDs and set them as `STRIPE_PRICE_PRO` and `STRIPE_PRICE_TEAM`

### Plan Mapping

The system maps Stripe price IDs to internal plan types:

| Plan Type | Features | Limits |
|-----------|----------|---------|
| **Free** | Basic templates | 5 documents, 1 collaborator, 1GB storage |
| **Pro** | Basic + Advanced templates, AI assistance | 100 documents, 5 collaborators, 10GB storage |
| **Team** | Pro + Team management, Advanced analytics | 1000 documents, 25 collaborators, 100GB storage |

### API Endpoints

#### POST /billing/webhook

Handles Stripe webhook events.

**Headers:**
- `Stripe-Signature` - Webhook signature for verification

**Responses:**
- `200` - Webhook processed successfully
- `400` - Invalid signature or payload
- `409` - Event already processed (idempotent)

#### GET /billing/summary

Returns current billing information for the tenant.

**Headers:**
- `X-Tenant-ID` - Tenant identifier

**Response:**
```json
{
  "tenant_id": "tenant_123",
  "plan": "pro",
  "is_active": true,
  "is_expired": false,
  "cycle_start": "2024-01-01T00:00:00Z",
  "cycle_end": "2024-02-01T00:00:00Z",
  "limits": {
    "max_documents": 100,
    "max_collaborators": 5,
    "storage_gb": 10,
    "features": ["basic_templates", "advanced_templates", "ai_assistance"]
  },
  "customer_id": "cus_stripe_customer_id",
  "subscription_id": "sub_stripe_subscription_id"
}
```

#### GET /billing/success

Returns success confirmation after checkout completion.

**Query Parameters:**
- `session_id` - Stripe checkout session ID (optional)

**Headers:**
- `X-Tenant-ID` - Tenant identifier

**Response:**
```json
{
  "success": true,
  "message": "Successfully upgraded to Pro plan!",
  "plan": {
    "name": "Pro",
    "limits": {
      "max_documents": 100,
      "max_collaborators": 5,
      "storage_gb": 10,
      "features": ["basic_templates", "advanced_templates", "ai_assistance"]
    },
    "cycle_end": "2024-02-01T00:00:00Z"
  },
  "session_id": "cs_stripe_session_id"
}
```

### Database Schema

The system uses an `entitlements` table to store billing information:

```sql
CREATE TABLE entitlements (
    id VARCHAR PRIMARY KEY,
    tenant_id VARCHAR NOT NULL,
    customer_id VARCHAR,
    subscription_id VARCHAR,
    plan VARCHAR NOT NULL DEFAULT 'free',
    cycle_start TIMESTAMP WITH TIME ZONE,
    cycle_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_entitlement_tenant ON entitlements(tenant_id);
CREATE INDEX idx_entitlement_customer ON entitlements(customer_id);
CREATE INDEX idx_entitlement_subscription ON entitlements(subscription_id);
```

### Security

#### Webhook Signature Verification

All webhook requests are verified using Stripe's signature verification to ensure they come from Stripe and haven't been tampered with.

#### Multi-tenant Safety

The system ensures multi-tenant safety by:

1. **Tenant Resolution**: Resolving tenant ID from Stripe metadata or customer mapping
2. **Tenant Isolation**: Only updating entitlements for the correct tenant
3. **Access Control**: Requiring tenant identification in API requests

### Error Handling

#### Webhook Processing

- **Invalid Signature**: Returns 400 error
- **Invalid JSON**: Returns 400 error  
- **Processing Errors**: Returns 200 to prevent Stripe retries, logs error internally
- **Unknown Events**: Returns 200, logs event type

#### Idempotency

The system tracks processed event IDs to ensure idempotent processing:

- Events are marked as processed after successful handling
- Replay of the same event returns 200 with "already processed" message
- Old event IDs are cleaned up periodically to prevent memory growth

### Local Development

#### Using Stripe CLI

1. **Install Stripe CLI**
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe
   
   # Other platforms: https://stripe.com/docs/stripe-cli
   ```

2. **Login to Stripe**
   ```bash
   stripe login
   ```

3. **Forward webhooks to local development**
   ```bash
   stripe listen --forward-to localhost:8000/billing/webhook
   ```

4. **Copy webhook secret**
   The CLI will output a webhook secret starting with `whsec_`. Set this as your `STRIPE_WEBHOOK_SECRET`.

#### Testing Webhooks

1. **Simulate checkout completion**
   ```bash
   stripe trigger checkout.session.completed
   ```

2. **Simulate subscription update**
   ```bash
   stripe trigger customer.subscription.updated
   ```

### Production Deployment

#### Webhook URL

Ensure your production webhook URL is accessible:
- Use HTTPS
- Ensure the `/billing/webhook` endpoint is not behind authentication
- Verify firewall rules allow Stripe's IP ranges

#### Database Migration

Run the database migration to create the entitlements table:

```bash
# Using Alembic (if configured)
alembic upgrade head

# Or run the SQL directly
psql -d your_database -f migrations/add_entitlements_table.sql
```

#### Environment Variables

Ensure all production environment variables are set:
- `STRIPE_SECRET_KEY` - Your live Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Your production webhook secret
- `STRIPE_PRICE_PRO` - Live Pro plan price ID
- `STRIPE_PRICE_TEAM` - Live Team plan price ID

### Monitoring

#### Webhook Delivery

Monitor webhook delivery in the Stripe Dashboard:
- Go to Developers → Webhooks
- Click on your webhook endpoint
- View delivery attempts and response codes

#### Application Logs

Monitor application logs for:
- Webhook processing errors
- Signature verification failures
- Tenant resolution issues
- Database update failures

#### Key Metrics

Track these metrics:
- Webhook success rate
- Processing latency
- Failed signature verifications
- Entitlement update success rate

### Troubleshooting

#### Common Issues

1. **Webhook Signature Verification Fails**
   - Check that `STRIPE_WEBHOOK_SECRET` is correct
   - Ensure webhook is configured for correct endpoint
   - Verify webhook secret matches the endpoint

2. **Tenant Not Found**
   - Ensure checkout sessions include `tenant_id` in metadata
   - Verify customer-to-tenant mapping logic
   - Check that customers are properly linked to tenants

3. **Plan Not Recognized**
   - Verify `STRIPE_PRICE_PRO` and `STRIPE_PRICE_TEAM` are correct
   - Check that products have the expected price IDs
   - Ensure subscription items reference correct prices

4. **Database Errors**
   - Verify entitlements table exists
   - Check database permissions
   - Ensure connection string is correct

#### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will log detailed webhook processing information.

### Frontend Integration

#### Success Page

After successful checkout, redirect users to:
```
/billing/success?session_id={CHECKOUT_SESSION_ID}
```

The page will display:
- Confirmation message
- New plan details
- Updated limits and features

#### Usage Page Updates

The usage page should refresh entitlement data after successful checkout by:
1. Polling `/billing/summary` endpoint
2. Updating displayed limits and current usage
3. Enabling new features based on plan

### Support

For additional support:
- Check Stripe webhook logs in dashboard
- Review application logs
- Contact development team with webhook event IDs for specific issues