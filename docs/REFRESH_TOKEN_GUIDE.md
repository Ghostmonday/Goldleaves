# Refresh Token Implementation - Usage Guide

## Overview

The refresh token implementation provides secure JWT token rotation with database-backed validation. This ensures long-term authentication security while maintaining user sessions.

## Components Created

### 1. RefreshToken Model (`apps/backend/models/refresh_token.py`)
- Database table for storing refresh tokens
- Relationships with User model
- Expiration and active status tracking

### 2. Auth Service (`apps/backend/services/auth_service.py`)
- `create_access_token()` - Creates JWT access tokens (15 min)
- `create_refresh_token()` - Creates JWT refresh tokens (30 days)
- `verify_password()` - Bcrypt password verification
- `hash_password()` - Bcrypt password hashing
- `decode_token()` - JWT token validation

### 3. Token Refresh Endpoint (`apps/backend/api/routers/token_refresh.py`)
- `POST /auth/token/refresh` - Refresh token endpoint
- Complete validation and token rotation
- Error handling and logging

### 4. Database Migrations
- Initial users table migration
- Refresh tokens table migration
- Proper indexes and foreign keys

## API Usage

### Request
```http
POST /auth/token/refresh
Content-Type: application/json

{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Successful Response
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 900
}
```

### Error Response
```json
{
    "detail": "Token expired"
}
```

## Security Features

### Token Rotation
- Old refresh token is revoked when used
- New access and refresh tokens are issued
- Prevents token replay attacks

### Database Validation
- Refresh tokens stored in database
- Can be revoked server-side
- Expiration tracking
- User activity validation

### JWT Security
- Signed with secret key
- Type validation (access vs refresh)
- Expiration timestamps
- User ID validation

## Integration Example

```python
# In your authentication flow
from apps.backend.services.auth_service import (
    create_access_token, 
    create_refresh_token,
    verify_password
)
from apps.backend.models import User, RefreshToken

# During login
def login_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        # Create tokens
        access_token = create_access_token(user.id)
        refresh_token, expires_at = create_refresh_token(user.id)
        
        # Store refresh token
        db_token = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            is_active=True
        )
        db.add(db_token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900
        }
```

## Frontend Integration

```javascript
// Store tokens
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);

// Automatic refresh on 401
axios.interceptors.response.use(
    response => response,
    async error => {
        if (error.response?.status === 401) {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const response = await axios.post('/auth/token/refresh', {
                        refresh_token: refreshToken
                    });
                    
                    localStorage.setItem('access_token', response.data.access_token);
                    localStorage.setItem('refresh_token', response.data.refresh_token);
                    
                    // Retry original request
                    error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
                    return axios.request(error.config);
                } catch (refreshError) {
                    // Redirect to login
                    window.location.href = '/login';
                }
            }
        }
        return Promise.reject(error);
    }
);
```

## Database Setup

After creating the models, run migrations:

```bash
# Create and run migrations
alembic upgrade head

# Verify tables exist
python scripts/setup_database.py
```

## Testing

Run the test suite:

```bash
pytest tests/test_token_refresh.py -v
```

## Next Steps

1. **Run Database Migrations**: `alembic upgrade head`
2. **Test the Endpoint**: Use the provided test cases
3. **Integrate with Login**: Add refresh token creation to login flow
4. **Frontend Integration**: Implement automatic token refresh
5. **Monitoring**: Add metrics for token refresh events

The implementation is production-ready with comprehensive error handling, security features, and proper database management.
