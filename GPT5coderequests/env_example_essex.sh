# .env.example
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1

# AWS S3
S3_BUCKET=my-bucket
S3_REGION=us-east-1

# Feature Flags
RLS_ENABLED=false
TENANT_ISOLATION_MODE=row

# Rate Limiting
TIER_RATE_LIMITS={"free": 100, "pro": 1000, "enterprise": 10000}

# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=true

# API Keys (if needed)
API_KEY=your-api-key
SECRET_KEY=your-secret-key