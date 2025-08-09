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