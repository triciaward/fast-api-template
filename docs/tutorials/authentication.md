# Authentication Guide

This guide covers the authentication system in your FastAPI application, including user registration, login, JWT tokens, and API key management.

## 🔐 Overview

The authentication system is built with **async-first architecture** and provides:

- **User Registration & Login** with email/password
- **JWT Token Authentication** with access and refresh tokens
- **API Key Management** for service-to-service communication
- **Session Management** with multiple concurrent sessions
- **Password Reset & Email Verification**
- **OAuth Integration** (Google, Apple)
- **Account Deletion** with grace period
- **Audit Logging** for security events

## 📁 Architecture

The authentication system is organized in a **domain-based structure**:

```
app/
├── api/auth/              # Authentication endpoints
│   ├── login.py           # Login/logout endpoints
│   ├── account_deletion.py # Account deletion
│   ├── email_verification.py # Email verification
│   ├── password_management.py # Password reset
│   ├── session_management.py # Session management
│   └── api_keys.py        # API key management
├── crud/auth/             # Authentication CRUD operations
│   ├── user.py            # User database operations
│   ├── api_key.py         # API key operations
│   └── refresh_token.py   # Session management
├── models/auth/           # Authentication models
│   ├── user.py            # User model
│   ├── api_key.py         # API key model
│   └── refresh_token.py   # Refresh token model
├── schemas/auth/          # Authentication schemas
│   └── user.py            # User schemas
└── services/auth/         # Authentication services
    ├── oauth.py           # OAuth integration
    └── refresh_token.py   # Token management
```

## 🚀 Quick Start

### **1. User Registration**

```python
# POST /auth/register
{
    "email": "user@example.com",
    "password": "securepassword123",
    "username": "johndoe"
}
```

### **2. User Login**

```python
# POST /auth/login (Content-Type: application/x-www-form-urlencoded)
# Fields: username, password
# Example body: username=user@example.com&password=securepassword123

# Response
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}
```

### **3. Protected Endpoints**

```python
# GET /users/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 🔧 Core Components

### **Async Database Operations**

All authentication operations use **async database sessions**:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.auth.user import get_user_by_email, create_user
from app.core.security.security import verify_password

# Async user authentication
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Async user creation
async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    return await create_user(db, user_data)
```

### **JWT Token Management**

Secure token-based authentication with refresh tokens:

```python
from datetime import timedelta
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.security import create_access_token
from app.database.database import get_db
from app.crud.auth.user import get_user_by_id

# Create access token (subject is user ID)
access_token = create_access_token(
    subject=user.id,
    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
)

# Verify token (used by dependencies in the app)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, user_id=str(user_id))
    if user is None:
        raise credentials_exception
    return user
```

### **API Key Management**

Secure API keys for service-to-service communication:

```python
# Endpoints:
# - POST /auth/api-keys        (create; returns { api_key: {...}, raw_key: "..." })
# - GET /auth/api-keys         (list)
# - DELETE /auth/api-keys/{id} (deactivate)
# - POST /auth/api-keys/{id}/rotate (rotate; returns new_raw_key once)

# Create payload example:
{
    "label": "My API Key",
    "scopes": ["read", "write"],
    "expires_at": "2025-01-01T00:00:00Z"  # optional
}

# Use API keys via Authorization header:
# Authorization: Bearer <raw_api_key>
```

### Scoped API keys on system endpoints

The template secures sensitive system endpoints with scoped API keys:

- Required scopes
  - `system:read` for detailed health and metrics
  - `tasks:read` / `tasks:write` for Celery task routes

- Protected routes
  - `GET /system/health/detailed`, `GET /system/health/database`, `GET /system/health/metrics`, `GET /system/health/test-sentry` → `system:read`
  - `GET /system/status`, `GET /system/tasks/active`, `GET /system/tasks/{task_id}/status` → `tasks:read`
  - `POST /system/tasks/submit`, `DELETE /system/tasks/{task_id}/cancel`, and other task-submission routes → `tasks:write`

- Public routes remain unauthenticated
  - `GET /system/health`, `GET /system/health/simple`, `GET /system/health/ready`, `GET /system/health/live`

Usage:

```http
GET /system/health/detailed
Authorization: Bearer <api_key_with_system:read>
```

## 📋 Available Endpoints

### **Authentication Endpoints**

```python
# User Registration
POST /auth/register
{
    "email": "user@example.com",
    "password": "securepassword123",
    "username": "johndoe"
}

# User Login
POST /auth/login
{
    "username": "user@example.com",
    "password": "securepassword123"
}

# OAuth Login
POST /auth/oauth/login
{
    "provider": "google",
    "access_token": "oauth_access_token_here"
}

# OAuth Providers
GET /auth/oauth/providers
```

### **Password Management**

```python
# Request Password Reset
POST /auth/forgot-password
{
    "email": "user@example.com"
}

# Reset Password
POST /auth/reset-password
{
    "token": "reset_token_here",
    "new_password": "newpassword123"
}

# Change Password (requires authentication)
POST /auth/change-password
Authorization: Bearer <access_token>
{
    "current_password": "oldpassword123",
    "new_password": "newpassword123"
}
```

### **Email Verification**

```python
# Request Email Verification
POST /auth/resend-verification
{
    "email": "user@example.com"
}

# Verify Email
POST /auth/verify-email
{
    "token": "verification_token_here"
}
```

### **API Key Management**

```python
# Create API Key
POST /auth/api-keys
Authorization: Bearer <access_token>
{
    "label": "My API Key",
    "scopes": ["read"],
    "expires_at": null
}

# List API Keys
GET /auth/api-keys
Authorization: Bearer <access_token>

# Delete API Key
DELETE /auth/api-keys/{key_id}
Authorization: Bearer <access_token>

# Rotate API Key
POST /auth/api-keys/{key_id}/rotate
Authorization: Bearer <access_token>
```

### **Session Management**

```python
# Refresh Token (uses HttpOnly cookie set during login)
POST /auth/refresh

# User Logout
POST /auth/logout
# (no Authorization header required; revokes session via refresh cookie)

# List Active Sessions
GET /auth/sessions
Authorization: Bearer <access_token>

# Revoke Session
DELETE /auth/sessions/{session_id}
Authorization: Bearer <access_token>

# Revoke All Sessions
DELETE /auth/sessions
Authorization: Bearer <access_token>
```

### **Account Deletion**

```python
# Request Account Deletion
POST /auth/request-deletion
{
    "email": "user@example.com"
}

# Confirm Account Deletion
POST /auth/confirm-deletion
{
    "token": "deletion_token_here"
}

# Cancel Account Deletion
POST /auth/cancel-deletion
{
    "email": "user@example.com"
}

# Check Deletion Status
GET /auth/deletion-status
# query param: ?email=user@example.com
```

## 🔒 Security Features

### **Password Security**

```python
from app.core.security.security import get_password_hash, verify_password

# Hash password
hashed_password = get_password_hash("plaintext_password")

# Verify password
is_valid = verify_password("plaintext_password", hashed_password)
```

### **Rate Limiting**

Built-in rate limiting for authentication endpoints:

```python
# Disabled by default (ENABLE_RATE_LIMITING = False). When enabled:
# - /auth/login                5/minute
# - /auth/register             3/minute
# - /auth/resend-verification  3/minute
# - /auth/forgot-password      3/minute
# - /auth/oauth/login          10/minute
# - /auth/request-deletion     3/minute
# - /auth/confirm-deletion     3/minute
# - /auth/cancel-deletion      3/minute
```

### **Session Management**

Multiple concurrent sessions with automatic cleanup:

```python
# Maximum sessions per user (configurable)
MAX_SESSIONS_PER_USER = 5

# Session cleanup interval
SESSION_CLEANUP_INTERVAL_HOURS = 24

# Refresh token cookie settings
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_COOKIE_HTTPONLY = True
REFRESH_TOKEN_COOKIE_SECURE = False  # set True in production
REFRESH_TOKEN_COOKIE_SAMESITE = "lax"
REFRESH_TOKEN_COOKIE_PATH = "/auth"
```

### **Audit Logging**

All authentication events are logged:

```python
from app.services.monitoring.audit import log_login_attempt, log_logout

# Log successful login
await log_login_attempt(db, request, user=user, success=True)

# Log logout
await log_logout(db, request, user=user)
```

## 🔧 Configuration

### **Environment Variables**

```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
ALGORITHM=HS256

# Refresh Token Configuration
REFRESH_TOKEN_EXPIRE_DAYS=30
REFRESH_TOKEN_COOKIE_NAME=refresh_token
REFRESH_TOKEN_COOKIE_SECURE=false
REFRESH_TOKEN_COOKIE_HTTPONLY=true
REFRESH_TOKEN_COOKIE_PATH=/auth

# Session Management
MAX_SESSIONS_PER_USER=5
SESSION_CLEANUP_INTERVAL_HOURS=24

# Email Configuration (for password reset, verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### **OAuth Configuration**

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Apple OAuth
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id
APPLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

## 🚀 Advanced Features

### **OAuth Integration**

```python
# Client obtains an ID/access token from the provider and posts it
POST /auth/oauth/login
{
  "provider": "google" | "apple",
  "access_token": "<id_or_access_token_here>"
}

# List configured providers
GET /auth/oauth/providers
```

### **Custom Authentication**

```python
# Custom authentication dependency
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Use in endpoints
@router.get("/admin/users")
async def get_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_all_users(db)
```

### **API Key Authentication**

```python
# Send Authorization: Bearer <raw_api_key>
from app.api.users.auth import get_api_key_user

@router.get("/users/me/api-key")
async def read_current_user_api_key(
    api_key_user: APIKeyUser = Depends(get_api_key_user),
):
    return api_key_user
```

To require a specific scope within an endpoint, use:

```python
from app.api.users.auth import require_api_scope
from app.schemas.auth.user import APIKeyUser

@router.get("/system/health/detailed")
async def detailed_health_check(
    _: APIKeyUser = Depends(require_api_scope("system:read")),
):
    ...
```

## 🛠️ Troubleshooting

### **Common Issues**

**1. "Could not validate credentials"**
- Check that the token is valid and not expired
- Verify the SECRET_KEY is correct
- Ensure the user still exists in the database

**2. "Email already registered"**
- The email is already in use
- Use a different email or reset the existing account

**3. "Invalid password"**
- Check password complexity requirements
- Ensure the password matches the stored hash

**4. "Rate limit exceeded"**
- Wait before trying again
- Check rate limiting configuration

### **Debug Commands**

```bash
# Check user in database
docker-compose exec postgres psql -U postgres -d your_db -c "SELECT * FROM users WHERE email = 'user@example.com';"

# Check API keys
docker-compose exec postgres psql -U postgres -d your_db -c "SELECT * FROM api_keys;"

# Check audit logs
docker-compose exec postgres psql -U postgres -d your_db -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;"
```

## 📚 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs to test authentication endpoints
2. **Read the Database Guide**: Learn about database operations in [Database Management](database-management.md)

4. **Deploy to Production**: Follow the [Deployment Guide](deployment-and-production.md)

---

**Happy coding! 🔐** 