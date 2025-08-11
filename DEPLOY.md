# Deployment Guide

## Staging Setup

This guide covers deploying the Goldleaves application to staging using Fly.io.

### Prerequisites

1. **Install flyctl**
   ```bash
   # macOS
   curl -L https://fly.io/install.sh | sh
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   curl -L https://fly.io/install.sh | sh
   ```

2. **Authenticate with Fly.io**
   ```bash
   # Set your API token as environment variable
   export FLY_API_TOKEN=your_fly_api_token_here
   
   # Or authenticate interactively
   fly auth login
   ```

### Staging Deployment Steps

1. **Create the Fly.io app**
   ```bash
   fly apps create goldleaves-staging
   ```

2. **Set environment variables**
   ```bash
   # Database configuration
   fly secrets set DATABASE_URL="postgresql://user:password@host:port/database" -a goldleaves-staging
   
   # Cache configuration
   fly secrets set REDIS_URL="redis://host:port" -a goldleaves-staging
   
   # Application secrets
   fly secrets set SECRET_KEY="your-secret-key-here" -a goldleaves-staging
   
   # AI service configuration
   fly secrets set OPENAI_API_KEY="your-openai-api-key" -a goldleaves-staging
   
   # Monitoring and error tracking
   fly secrets set SENTRY_DSN="your-sentry-dsn" -a goldleaves-staging
   
   # Payment processing (Stripe)
   fly secrets set STRIPE_SECRET_KEY="sk_test_..." -a goldleaves-staging
   fly secrets set STRIPE_WEBHOOK_SECRET="whsec_..." -a goldleaves-staging
   
   # File storage (S3-compatible)
   fly secrets set S3_BUCKET="your-bucket-name" -a goldleaves-staging
   fly secrets set S3_REGION="us-east-1" -a goldleaves-staging
   fly secrets set S3_ACCESS_KEY_ID="your-access-key" -a goldleaves-staging
   fly secrets set S3_SECRET_ACCESS_KEY="your-secret-key" -a goldleaves-staging
   
   # Application domain
   fly secrets set APP_DOMAIN="goldleaves-staging.fly.dev" -a goldleaves-staging
   
   # Observability (OpenTelemetry)
   fly secrets set OTEL_EXPORTER_OTLP_ENDPOINT="https://your-otel-endpoint" -a goldleaves-staging
   fly secrets set OTEL_SERVICE_NAME="goldleaves-staging" -a goldleaves-staging
   
   # Metrics
   fly secrets set METRICS_ENABLED="true" -a goldleaves-staging
   ```

3. **Deploy the application**
   ```bash
   fly deploy --config infra/fly.toml -a goldleaves-staging
   ```

4. **Verify deployment**
   ```bash
   # Check app status
   fly status -a goldleaves-staging
   
   # View logs
   fly logs -a goldleaves-staging
   
   # Test health endpoint
   curl https://goldleaves-staging.fly.dev/health
   ```

### Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `SECRET_KEY` | Application secret key for JWT signing | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes |
| `SENTRY_DSN` | Sentry DSN for error tracking | No |
| `STRIPE_SECRET_KEY` | Stripe secret key for payments | Yes |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | Yes |
| `S3_BUCKET` | S3 bucket name for file storage | Yes |
| `S3_REGION` | S3 region | Yes |
| `S3_ACCESS_KEY_ID` | S3 access key | Yes |
| `S3_SECRET_ACCESS_KEY` | S3 secret key | Yes |
| `APP_DOMAIN` | Application domain | Yes |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry endpoint | No |
| `OTEL_SERVICE_NAME` | Service name for tracing | No |
| `METRICS_ENABLED` | Enable metrics collection | No |

### Troubleshooting

1. **Deployment fails**: Check logs with `fly logs -a goldleaves-staging`
2. **Health check fails**: Ensure the `/health` endpoint is accessible
3. **Database connection issues**: Verify `DATABASE_URL` is correct and accessible
4. **Environment variables**: Use `fly secrets list -a goldleaves-staging` to verify secrets are set

### CI/CD Integration

The application includes GitHub Actions workflow for automated staging deployments. Deployments are triggered by:
- Git tags matching `v*` pattern
- Manual workflow dispatch

The workflow will:
1. Build and push Docker image to container registry
2. Deploy to Fly.io using the configuration in `infra/fly.toml`