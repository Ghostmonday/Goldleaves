# === OURS ===
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

# === THEIRS ===
# Goldleaves Deployment Guide

This guide covers the deployment process for the Goldleaves API, including local development, staging, and production environments.

## Prerequisites

- Docker and Docker Compose
- PostgreSQL database
- Redis instance (for rate limiting and background tasks)
- S3-compatible storage (optional)
- Python 3.11+

## Local Development

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ghostmonday/Goldleaves.git
   cd Goldleaves
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

3. **Start services with Docker Compose:**
   ```bash
   docker compose up
   ```

   This will start:
   - PostgreSQL database
   - Redis instance
   - API server
   - Background worker (if configured)

4. **Access the application:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Manual Setup (without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database:**
   ```bash
   # Ensure PostgreSQL is running
   createdb goldleaves
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start the API server:**
   ```bash
   uvicorn routers.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Database Management

### Run Migrations

For development:
```bash
alembic upgrade head
```

For production:
```bash
# In production container or environment
docker compose exec api alembic upgrade head
```

### Create New Migration

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Reset Database (Development Only)

```bash
alembic downgrade base
alembic upgrade head
```

## Background Workers

### Start Worker Locally

With Docker Compose:
```bash
docker compose up worker
```

Manual start:
```bash
docker compose run --rm worker celery -A workers.app worker -l info
```

### Worker Monitoring

Start Celery Flower for monitoring:
```bash
docker compose run --rm worker celery -A workers.app flower
```

Access Flower dashboard: http://localhost:5555

### Available Queues

- `default`: General background tasks
- `documents`: Document processing tasks

## Configuration

### Required Environment Variables

#### Core Application
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT tokens (min 32 characters)
- `REDIS_URL`: Redis connection string

#### Platform Integration
- `S3_BUCKET`: S3 bucket name (optional)
- `S3_REGION`: AWS region
- `S3_ACCESS_KEY_ID`: AWS access key
- `S3_SECRET_ACCESS_KEY`: AWS secret key

#### Observability
- `SENTRY_DSN`: Sentry error tracking URL (optional)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry collector endpoint (optional)
- `OTEL_SERVICE_NAME`: Service name for tracing (default: goldleaves-api)

### Environment-Specific Configs

#### Development
```env
ENVIRONMENT=development
DEBUG=true
ENABLE_DOCS=true
LOG_LEVEL=DEBUG
```

#### Staging
```env
ENVIRONMENT=staging
DEBUG=false
ENABLE_DOCS=true
LOG_LEVEL=INFO
```

#### Production
```env
ENVIRONMENT=production
DEBUG=false
ENABLE_DOCS=false
LOG_LEVEL=WARNING
```

## Deployment

### Staging Deployment

1. **Build and deploy:**
   ```bash
   docker compose -f docker-compose.staging.yml up -d
   ```

2. **Run migrations:**
   ```bash
   docker compose -f docker-compose.staging.yml exec api alembic upgrade head
   ```

3. **Verify deployment:**
   ```bash
   curl https://staging-api.goldleaves.com/health
   ```

### Production Deployment

1. **Deploy with production configuration:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

2. **Run migrations:**
   ```bash
   docker compose -f docker-compose.prod.yml exec api alembic upgrade head
   ```

3. **Start background workers:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d worker
   ```

## Staging Secrets Checklist

Ensure these secrets are configured in your staging environment:

### Application Secrets
- [ ] `JWT_SECRET` - JWT signing secret (32+ characters)
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `REDIS_URL` - Redis connection string
- [ ] `SECRET_KEY` - Application secret key

### External Services
- [ ] `S3_ACCESS_KEY_ID` - AWS S3 access key
- [ ] `S3_SECRET_ACCESS_KEY` - AWS S3 secret key
- [ ] `SENTRY_DSN` - Sentry error tracking URL
- [ ] `OTEL_EXPORTER_OTLP_HEADERS` - OpenTelemetry authentication headers

### Email Configuration (if applicable)
- [ ] `SMTP_PASSWORD` - SMTP server password
- [ ] `EMAIL_PASSWORD` - Email account password

### API Keys
- [ ] `OPENAI_API_KEY` - OpenAI API key (if using AI features)
- [ ] `WEBHOOK_SECRET` - Webhook verification secret

### Validation

After setting secrets, verify:
```bash
# Check health endpoint
curl https://staging-api.goldleaves.com/health

# Check authentication
curl -H "Authorization: Bearer <token>" https://staging-api.goldleaves.com/api/v1/me

# Check background tasks
curl https://staging-api.goldleaves.com/metrics
```

## Monitoring and Maintenance

### Health Checks

- **Application health:** `/health`
- **System metrics:** `/metrics`
- **Prometheus metrics:** `/metrics/prometheus`

### Log Monitoring

View application logs:
```bash
docker compose logs -f api
docker compose logs -f worker
```

### Database Maintenance

Regular maintenance tasks:
```bash
# Database backup
pg_dump goldleaves > backup_$(date +%Y%m%d).sql

# Analyze tables
docker compose exec db psql -U postgres -d goldleaves -c "ANALYZE;"
```

### Worker Management

Monitor and manage Celery workers:
```bash
# List active tasks
celery -A workers.app inspect active

# Purge queues (use with caution)
celery -A workers.app purge

# Restart workers
docker compose restart worker
```

## Troubleshooting

### Common Issues

1. **Database connection failed:**
   - Verify `DATABASE_URL` format
   - Check database server is running
   - Verify network connectivity

2. **Redis connection failed:**
   - Check `REDIS_URL` configuration
   - Verify Redis server is running
   - Rate limiting will no-op if Redis unavailable

3. **S3 upload failures:**
   - Verify AWS credentials
   - Check bucket permissions
   - Confirm bucket exists in specified region

4. **Background tasks not processing:**
   - Check worker logs: `docker compose logs worker`
   - Verify Redis connection
   - Check queue status: `celery -A workers.app inspect active`

### Performance Tuning

1. **Database optimization:**
   - Monitor slow queries
   - Add appropriate indexes
   - Configure connection pooling

2. **Rate limiting tuning:**
   - Adjust capacity and refill rates per tenant
   - Monitor rate limit metrics
   - Scale Redis if needed

3. **Worker scaling:**
   - Monitor queue lengths
   - Scale worker instances based on load
   - Tune `worker_prefetch_multiplier`

### Recovery Procedures

1. **Application crash recovery:**
   ```bash
   docker compose restart api
   docker compose logs -f api
   ```

2. **Database recovery:**
   ```bash
   # Restore from backup
   psql goldleaves < backup_YYYYMMDD.sql
   alembic upgrade head
   ```

3. **Clear stuck tasks:**
   ```bash
   celery -A workers.app purge
   docker compose restart worker
   ```

## Security Considerations

- Rotate secrets regularly
- Use strong passwords and keys
- Enable HTTPS in production
- Monitor access logs
- Keep dependencies updated
- Regular security audits

For additional support, contact the development team or check the project documentation.

