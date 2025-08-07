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
# POST /auth/login
{
    "username": "user@example.com",
    "password": "securepassword123"
}

# Response
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 900
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

# Async user authentication
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Async user creation
async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    user = await create_user(db, user_data)
    return user
```

### **JWT Token Management**

Secure token-based authentication with refresh tokens:

```python
from app.core.security.security import create_access_token, create_refresh_token

# Create access token
access_token = create_access_token(data={"sub": user.email})

# Create refresh token
refresh_token = create_refresh_token(data={"sub": user.email})

# Verify token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user
```

### **API Key Management**

Secure API keys for service-to-service communication:

```python
from app.crud.auth.api_key import create_api_key, get_api_keys_by_user

# Create API key
async def create_api_key_for_user(
    db: AsyncSession, 
    user_id: str, 
    name: str
) -> ApiKey:
    api_key = await create_api_key(db, user_id=user_id, name=name)
    return api_key

# Verify API key
async def get_user_by_api_key(
    db: AsyncSession, 
    api_key: str
) -> User | None:
    user = await get_user_by_api_key(db, api_key)
    return user
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
Authorization: Bearer <access_token>

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
    "name": "My API Key"
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
# Refresh Token
POST /auth/refresh
{
    "refresh_token": "refresh_token_here"
}

# User Logout
POST /auth/logout
Authorization: Bearer <access_token>

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
Authorization: Bearer <access_token>

# Confirm Account Deletion
POST /auth/confirm-deletion
{
    "token": "deletion_token_here"
}

# Cancel Account Deletion
POST /auth/cancel-deletion
Authorization: Bearer <access_token>

# Check Deletion Status
GET /auth/deletion-status
Authorization: Bearer <access_token>
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
# Rate limiting is automatically applied to:
# - /auth/login (5 attempts per minute)
# - /auth/register (3 attempts per minute)
# - /auth/forgot-password (3 attempts per minute)
# - /auth/oauth/login (5 attempts per minute)
```

### **Session Management**

Multiple concurrent sessions with automatic cleanup:

```python
# Maximum sessions per user (configurable)
MAX_SESSIONS_PER_USER = 5

# Session cleanup interval
SESSION_CLEANUP_INTERVAL_HOURS = 24
```

### **Audit Logging**

All authentication events are logged:

```python
from app.services.monitoring.audit import log_login, log_logout

# Log successful login
await log_login(db, user_id=user.id, ip_address=request.client.host)

# Log logout
await log_logout(db, user_id=user.id, ip_address=request.client.host)
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

# Session Management
MAX_SESSIONS_PER_USER=5
SESSION_CLEANUP_INTERVAL_HOURS=24

# Email Configuration (for password reset, verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### **OAuth Configuration**

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Apple OAuth
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
```

## 🚀 Advanced Features

### **OAuth Integration**

```python
from app.services.auth.oauth import google_oauth, apple_oauth

# Google OAuth
@router.get("/auth/google")
async def google_login():
    return {"url": google_oauth.get_authorization_url()}

@router.get("/auth/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    user_info = await google_oauth.get_user_info(code)
    user = await get_or_create_oauth_user(db, user_info)
    return create_token_response(user)
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
# API key authentication dependency
async def get_user_by_api_key(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    user = await get_user_by_api_key(db, api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return user

# Use in endpoints
@router.get("/api/data")
async def get_data(
    current_user: User = Depends(get_user_by_api_key)
):
    return {"data": "your data here"}
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