# Database Setup for Gold Leaves

This document outlines how to set up the database for the Gold Leaves project.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)

## Quick Setup with Docker

1. **Start PostgreSQL with Docker Compose:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Verify the database is running:**
   ```bash
   python scripts/setup_database.py
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

## Manual PostgreSQL Setup

1. **Install PostgreSQL** on your system

2. **Create the database:**
   ```sql
   CREATE DATABASE goldleaves;
   ```

3. **Update `.env` file** with your database credentials:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/goldleaves
   ```

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migrations
```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

### Check migration status
```bash
alembic current
alembic history --verbose
```

## Database Schema

### Users Table
The main user table includes:
- `id`: Primary key
- `username`: Unique username (max 50 chars)
- `email`: Unique email address (max 255 chars)
- `hashed_password`: Bcrypt hashed password
- `is_active`: Whether the user account is active
- `is_verified`: Whether the user has verified their email
- `verification_token`: Token for email verification
- `token_expires_at`: Expiration time for verification token
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

## Troubleshooting

### Connection Issues
1. Ensure PostgreSQL is running
2. Check your DATABASE_URL in `.env`
3. Verify database credentials
4. Check firewall settings

### Migration Issues
1. Ensure database is accessible
2. Check for pending migrations: `alembic current`
3. Verify model changes in `apps/backend/models/`

### Testing Database Setup
Run the database setup script:
```bash
python scripts/setup_database.py
```

This will:
- ✅ Validate configuration
- ✅ Test database connection
- ✅ List existing tables
- ✅ Show users table structure (if exists)
