# Authentication System Tutorial

Welcome to the authentication tutorial! This guide will teach you everything about how users can sign up, log in, and manage their accounts in your FastAPI application.

---

## 🔑 Authentication Flows (Visual)

```mermaid
flowchart TD
  subgraph Email/Password
    A1[Register] --> A2[Email Verification]
    A2 --> A3[Login]
    A3 --> A4[Get JWT]
    A4 --> A5[Access Protected Routes]
  end
  subgraph OAuth
    B1[Click Provider] --> B2[Redirect]
    B2 --> B3[Create User if New]
    B3 --> B4[Get JWT]
    B4 --> B5[Access Protected Routes]
  end
```

> **OAuth Password Management**
>
> OAuth users **cannot change their password** via this app. Their password is managed by the provider (Google/Apple). If they want to change it, they must do so through their provider's account settings.

---

## What is Authentication?

Think of authentication like a digital ID card system. When someone wants to use your app, they need to prove who they are. The authentication system handles:
- **Sign up**: Creating new accounts
- **Log in**: Proving you are who you say you are
- **Password management**: Resetting forgotten passwords
- **Account security**: Keeping accounts safe

---

## How It Works (The Simple Version)

**Email/Password Flow:**
1. User registers (POST `/api/v1/auth/register`)
2. Receives verification email
3. Verifies email (GET `/api/v1/auth/verify-email?token=...`)
4. Logs in (POST `/api/v1/auth/login`)
5. Receives JWT access/refresh tokens
6. Uses JWT to access protected routes

**OAuth Flow:**
1. User clicks "Sign in with Google/Apple"
2. Redirected to provider, authenticates
3. Provider redirects back with token
4. App verifies token, creates user if new
5. App issues JWT, user is logged in

---

## Features Included

### 🔐 Basic Authentication
- **User Registration**: Create new accounts with email and username
- **User Login**: Secure login with email and password
- **JWT Tokens**: Secure digital keys for accessing the app
- **Email Verification**: Verify email addresses before allowing login

### 🔑 Password Management
- **Password Reset**: Help users who forgot their passwords
- **Password Change**: Let users update their passwords
- **Password Validation**: Ensure passwords are strong and secure

### 🌐 OAuth Integration
- **Google Login**: Let users sign in with their Google account
- **Apple Login**: Let users sign in with their Apple ID
- **Automatic Account Creation**: Create accounts automatically for OAuth users

> **Note:** OAuth users **cannot change their password** via this app. Their password is managed by the provider (Google/Apple). If they want to change it, they must do so through their provider's account settings.

### 🛡️ Security Features
- **Rate Limiting**: Prevent too many login attempts
- **Session Management**: Handle multiple devices and sessions
- **Account Deletion**: GDPR-compliant account deletion
- **Audit Logging**: Track all login attempts and security events

---

## Email/Password Authentication

### 1. Register a New User

**Endpoint:** `POST /api/v1/auth/register`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "myuser",
    "password": "MySecurePassword123!"
  }'
```

**What happens:**
1. System checks if email/username already exists
2. Password is securely hashed (never stored as plain text)
3. Account is created (but not verified yet)
4. Verification email is sent (if email service is configured)
5. User gets a response with their account details

### 2. Verify Email

**Endpoint:** `GET /api/v1/auth/verify-email?token=...`

- User clicks the link in their email to verify their account.
- The backend marks the user as verified.

### 3. Login

**Endpoint:** `POST /api/v1/auth/login`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=MySecurePassword123!"
```

**What happens:**
1. System verifies email and password
2. If correct, creates a JWT access token (valid for 15 minutes)
3. Creates a refresh token (valid for 30 days) stored as a secure cookie
4. Returns the access token for immediate use

### 4. Using the Access Token

Once you have an access token, include it in the `Authorization` header:

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

### 🔑 Access Token vs Refresh Token

| Token Type      | Purpose                                 | Lifetime         | Where Stored         | When to Use                |
|-----------------|-----------------------------------------|------------------|----------------------|----------------------------|
| Access Token    | Grants access to protected API routes   | ~15 minutes      | Client (memory)      | Every API request          |
| Refresh Token   | Get new access tokens without logging in| ~30 days         | Secure HTTP-only cookie | When access token expires  |

- **Access Token**: Short-lived, used for most requests. If expired, you need a new one.
- **Refresh Token**: Long-lived, used to get new access tokens. Never send this to the frontend directly.

---

## 🌐 OAuth Authentication (Google/Apple)

**Endpoint:** `POST /api/v1/auth/oauth/login`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/oauth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "access_token": "google_access_token",
    "email": "user@gmail.com",
    "name": "John Doe"
  }'
```

**What happens:**
1. System verifies the OAuth token with Google/Apple
2. If valid, creates or finds the user account
3. Creates a session and returns access token
4. User is automatically logged in

> **Password Management for OAuth Users:**
> - OAuth users **cannot change their password** in this app. Their password is managed by the provider (Google/Apple).
> - If they want to change it, they must do so through their provider's account settings.

---

## Sequence Diagram: Email/Password Login

```mermaid
sequenceDiagram
  participant User
  participant API
  participant DB
  User->>API: POST /auth/login (email, password)
  API->>DB: Find user by email
  DB-->>API: User record
  API->>API: Verify password
  API->>API: Generate JWT
  API-->>User: Return access/refresh tokens
```

---

## Email Verification

When a user registers, they need to verify their email before they can log in:

1. **User registers** → Verification email sent
2. **User clicks link** → Email verified, account activated
3. **User can now log in** → Full access granted

If email service isn't configured, users are automatically verified (for development).

---

## Password Reset Flow

If a user forgets their password:

1. **Request reset**: User enters their email
2. **Reset email sent**: Contains a secure reset link
3. **Set new password**: User clicks link and sets new password
4. **Login with new password**: User can now log in normally

**Endpoints:**
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`

```bash
# Step 1: Request password reset
curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Step 2: Reset password (after clicking email link)
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset_token_from_email",
    "new_password": "NewSecurePassword123!"
  }'
```

---

## Password Change Flow

If a user wants to change their password (while logged in):

1. **User is logged in**: Must have valid access token
2. **Provide current password**: Verify user knows current password
3. **Set new password**: Update to new secure password
4. **Continue using app**: No need to log in again

**Endpoint:** `POST /api/v1/auth/change-password`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewSecurePassword456!"
  }'
```

**What happens:**
1. System verifies the user is logged in (valid access token)
2. System checks the current password is correct
3. System validates the new password meets security requirements
4. System updates the password in the database
5. User can continue using the app with the new password

**Note**: Password change is different from password reset:
- **Password Reset**: For users who forgot their password (requires email token)
- **Password Change**: For logged-in users who want to update their password (requires current password)

---

## 🔗 Developer References

- **Schemas:** [`app/schemas/user.py`](../../app/schemas/user.py)
- **CRUD Methods:** [`app/crud/user.py`](../../app/crud/user.py)
- **OAuth Logic:** [`app/services/oauth.py`](../../app/services/oauth.py)
- **Email Logic:** [`app/services/email.py`](../../app/services/email.py)
- **Rate Limiting:** [`app/services/rate_limiter.py`](../../app/services/rate_limiter.py)

---

## Configuration

### Environment Variables

You need to set these in your `.env` file:

```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Email (for verification and password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=True

# OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id
APPLE_PRIVATE_KEY=your-apple-private-key

# Rate Limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REGISTER=3/minute
```

---

## Rate Limiting

The system automatically limits how many times users can:
- **Login**: 5 attempts per minute
- **Register**: 3 attempts per minute
- **Request password reset**: 3 attempts per minute
- **Verify email**: 3 attempts per minute

This prevents abuse and keeps your app secure.

---

## 🔑 API Key Authentication

API keys provide a secure way for applications and services to authenticate with your API without user interaction. They're perfect for:
- **Server-to-server communication**
- **Mobile app backends**
- **Third-party integrations**
- **Development tooling**
- **Automated scripts**

### How API Key Authentication Works

```mermaid
flowchart TD
    A[Create API Key] --> B[Store Key Securely]
    B --> C[Use in Requests]
    C --> D[API Validates Key]
    D --> E[Check Scopes]
    E --> F[Access Granted/Denied]
```

### 1. Creating API Keys

**Prerequisite**: You must be logged in with a JWT token to create API keys.

```bash
# 1. First, get a JWT token by logging in
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"

# 2. Create an API key using the JWT token
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Production Integration",
    "scopes": ["read_events", "write_events"],
    "expires_at": "2024-12-31T23:59:59Z"
  }'
```

**Response:**
```json
{
  "api_key": {
    "id": "uuid",
    "label": "Production Integration",
    "scopes": ["read_events", "write_events"],
    "user_id": "user_uuid",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "raw_key": "sk_abc123..."  // Store this securely!
}
```

> **⚠️ Important**: The `raw_key` is only shown once! Store it securely and never commit it to version control.

### 2. Using API Keys for Authentication

API keys use the same `Authorization: Bearer` header format as JWT tokens:

```bash
# Use API key to access protected endpoints
curl -X GET "http://localhost:8000/api/v1/users/me/api-key" \
  -H "Authorization: Bearer sk_abc123..."
```

**Response:**
```json
{
  "id": "key_uuid",
  "scopes": ["read_events", "write_events"],
  "user_id": "user_uuid",
  "key_id": "key_uuid"
}
```

### 3. API Key Management

#### List Your API Keys

```bash
curl -X GET "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Deactivate an API Key

```bash
curl -X DELETE "http://localhost:8000/api/v1/auth/api-keys/{key_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Rotate an API Key

```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-keys/{key_id}/rotate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "api_key": {
    "id": "uuid",
    "label": "Production Integration",
    "scopes": ["read_events", "write_events"],
    "user_id": "user_uuid",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "new_raw_key": "sk_xyz789..."  // New key to use
}
```

### 4. Scope-Based Access Control

API keys support fine-grained permissions through scopes:

```python
from fastapi import Depends
from app.api.api_v1.endpoints.users import get_api_key_user, require_api_scope

# Basic API key authentication
@app.get("/api/v1/events")
async def get_events(api_key_user: APIKeyUser = Depends(get_api_key_user)):
    return {"message": "Authenticated with API key", "user_id": api_key_user.user_id}

# Scope-based access control
@app.post("/api/v1/events")
async def create_event(api_key_user: APIKeyUser = Depends(require_api_scope("write_events"))):
    return {"message": "Event created", "scopes": api_key_user.scopes}
```

### 5. Common API Key Scopes

- `read_events` - Read-only access to events
- `write_events` - Create and update events
- `delete_events` - Delete events
- `admin` - Full administrative access
- `user_management` - Manage user accounts

### 6. API Key Security Features

✅ **Secure Generation**: Cryptographically secure keys with `sk_` prefix  
✅ **Scope-Based Access**: Fine-grained permissions  
✅ **Expiration Support**: Optional key expiration dates  
✅ **Key Rotation**: Generate new keys while keeping the same ID  
✅ **User Isolation**: Users can only manage their own keys  
✅ **Soft Delete**: Keys can be deactivated and restored  
✅ **Audit Logging**: All key operations are logged  

### 7. API Key Best Practices

#### 🔒 Security
1. **Store Keys Securely**: Never commit API keys to version control
2. **Use Environment Variables**: Store keys in `.env` files or secure vaults
3. **Rotate Regularly**: Use the rotation endpoint to update keys periodically
4. **Minimal Scopes**: Only grant the scopes your integration needs
5. **Monitor Usage**: Check audit logs for unusual activity

#### 🛠️ Development
```bash
# Store API key in environment variable
export API_KEY="sk_abc123..."

# Use in requests
curl -X GET "http://localhost:8000/api/v1/users/me/api-key" \
  -H "Authorization: Bearer $API_KEY"
```

#### 📝 Environment Configuration
```bash
# .env file
API_KEY=sk_abc123...
API_BASE_URL=http://localhost:8000/api/v1
```

### 8. API Key vs JWT Tokens

| Feature | API Keys | JWT Tokens |
|---------|----------|------------|
| **Use Case** | Server-to-server, integrations | User sessions, web apps |
| **Lifespan** | Long-lived (months/years) | Short-lived (minutes) |
| **Scopes** | Fine-grained permissions | User roles |
| **Management** | Manual creation/rotation | Automatic refresh |
| **Security** | Single-use, can be rotated | Can be compromised |

### 9. Troubleshooting API Keys

**"Invalid API key" error**
- Check that the key starts with `sk_`
- Verify the key is correct and not truncated
- Ensure the key hasn't been deactivated

**"API key has expired" error**
- The key has passed its expiration date
- Create a new key or contact the key owner

**"API key is inactive" error**
- The key has been deactivated
- Contact the key owner to reactivate it

**"API key missing required scope" error**
- The key doesn't have the required permission
- Request a key with the necessary scopes

---

## Testing the Authentication

### Using the API Documentation

The easiest way to test is through the interactive API docs:

1. Start your server: `uvicorn app.main:app --reload`
2. Open http://localhost:8000/docs in your browser
3. Try the authentication endpoints interactively

### Using curl (Command Line)

You can also test with curl commands:

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPassword123!"
  }'

# 2. Login with the user
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123!"

# 3. Use the returned access token
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. Change password (optional)
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "current_password": "TestPassword123!",
    "new_password": "NewTestPassword456!"
  }'
```

---

## Common Issues and Solutions

### "Email not verified" error
- **Problem**: User tries to log in before verifying email
- **Solution**: Check email for verification link, or configure email service

### "Invalid credentials" error
- **Problem**: Wrong email or password
- **Solution**: Double-check email and password, or use password reset

### "Rate limit exceeded" error
- **Problem**: Too many login attempts
- **Solution**: Wait a few minutes before trying again

### "Token expired" error
- **Problem**: Access token has expired (after 15 minutes)
- **Solution**: Use refresh token to get a new access token, or log in again

---

## 🛠️ Troubleshooting FAQ

**Q: Why am I getting a 401 Unauthorized error?**
- Your access token is missing, expired, or invalid. Make sure to include a valid `Authorization: Bearer ...` header. If expired, use your refresh token to get a new one or log in again.

**Q: Why can't my OAuth user change their password?**
- OAuth users' passwords are managed by Google/Apple/etc. They must change their password with the provider, not in this app.

**Q: Why am I not receiving verification or reset emails?**
- Check your SMTP/email settings in `.env`. In development, you may need to use a real email provider or check your spam folder.

**Q: Why do I get 'Email already registered'?**
- The email is already in use. Try logging in or use password reset.

**Q: Why do I get 'Too many requests' errors?**
- Rate limiting is in effect. Wait a minute and try again.

---

## Security Best Practices

1. **Use HTTPS in production**: Always use HTTPS to protect tokens
2. **Set strong SECRET_KEY**: Generate a random 32-character key
3. **Configure email service**: Enable email verification for security
4. **Monitor rate limits**: Watch for unusual login patterns
5. **Regular password updates**: Encourage users to change passwords regularly

---

## Glossary

- **JWT**: JSON Web Token, a secure way to represent claims between two parties.
- **CRUD**: Create, Read, Update, Delete (basic database operations).
- **Schema**: A Pydantic model that defines the shape of data for validation and serialization.
- **ORM**: Object-Relational Mapper, a tool that lets you interact with the database using Python classes (e.g., SQLAlchemy).
- **Access Token**: Short-lived token for accessing protected routes.
- **Refresh Token**: Long-lived token for getting new access tokens without logging in again.
- **OAuth**: Open standard for authentication via third-party providers (Google, Apple, etc.).

---

## 🔑 API Key Management CLI

The FastAPI template includes a powerful command-line interface for managing API keys. This CLI provides the same functionality as the web API but in a scriptable format perfect for automation and server management.

### Installation

The CLI script is located at `scripts/manage_api_keys.py` and includes a shell wrapper at `scripts/manage_api_keys.sh` for easy execution.

### Basic Commands

```bash
# Show help
./scripts/manage_api_keys.sh --help

# Show help for a specific command
./scripts/manage_api_keys.sh create --help
./scripts/manage_api_keys.sh list --help
./scripts/manage_api_keys.sh deactivate --help
./scripts/manage_api_keys.sh rotate --help
```

### Creating API Keys

```bash
# Create a new API key
./scripts/manage_api_keys.sh create \
  --user-id 123e4567-e89b-12d3-a456-426614174000 \
  --label "Production Integration" \
  --scopes "read_events,write_events"

# Create a key with expiration
./scripts/manage_api_keys.sh create \
  --user-id 123e4567-e89b-12d3-a456-426614174000 \
  --label "Temporary Key" \
  --expires-at "2024-12-31T23:59:59"

# Create a key with no scopes (full access)
./scripts/manage_api_keys.sh create \
  --user-id 123e4567-e89b-12d3-a456-426614174000 \
  --label "Admin Key"
```

**Important**: The raw API key is only shown once when created. Store it securely!

### Listing API Keys

```bash
# List all keys for a user
./scripts/manage_api_keys.sh list \
  --user-id 123e4567-e89b-12d3-a456-426614174000
```

**Example Output:**
```
📋 API keys for user 123e4567-e89b-12d3-a456-426614174000:
--------------------------------------------------------------------------------

1. Production Integration
   ID: 16ceeaae-023e-4300-914d-c6323d26b021
   Status: 🟢 Active
   Scopes: read_events, write_events
   Created: 2024-01-01 12:00:00

2. Temporary Key
   ID: 28dffbbf-1341-5411-b025-2fe33c3e7c132
   Status: 🟢 Active
   Scopes: None
   Created: 2024-01-01 13:00:00
   Expires: 2024-12-31 23:59:59
```

### Deactivating API Keys

```bash
# Deactivate a key (requires key ID)
./scripts/manage_api_keys.sh deactivate \
  --key-id 123e4567-e89b-12d3-a456-426614174000

# Deactivate a key with user verification
./scripts/manage_api_keys.sh deactivate \
  --key-id 123e4567-e89b-12d3-a456-426614174000 \
  --user-id 123e4567-e89b-12d3-a456-426614174000
```

### Rotating API Keys

```bash
# Rotate a key (get a new key with same ID)
./scripts/manage_api_keys.sh rotate \
  --key-id 123e4567-e89b-12d3-a456-426614174000

# Rotate a key with user verification
./scripts/manage_api_keys.sh rotate \
  --key-id 123e4567-e89b-12d3-a456-426614174000 \
  --user-id 123e4567-e89b-12d3-a456-426614174000
```

**Important**: The new raw API key is only shown once when rotated. Store it securely!

### Integration Examples

#### Shell Scripts

```bash
#!/bin/bash
# Create an API key for a user
USER_ID="123e4567-e89b-12d3-a456-426614174000"
API_KEY_OUTPUT=$(./scripts/manage_api_keys.sh create \
  --user-id "$USER_ID" \
  --label "CI/CD Integration" \
  --scopes "read_events")

# Extract the raw key (be careful with this in production!)
RAW_KEY=$(echo "$API_KEY_OUTPUT" | grep "sk_" | head -1 | awk '{print $3}')

echo "API Key created: $RAW_KEY"
```

#### Python Scripts

```python
import subprocess
import json

def create_api_key(user_id: str, label: str, scopes: str = "") -> str:
    """Create an API key and return the raw key."""
    cmd = [
        "./scripts/manage_api_keys.sh",
        "create",
        "--user-id", user_id,
        "--label", label,
        "--scopes", scopes
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to create API key: {result.stderr}")
    
    # Extract the raw key from output
    for line in result.stdout.split('\n'):
        if line.strip().startswith('sk_'):
            return line.strip()
    
    raise Exception("Raw key not found in output")
```

### Security Considerations

1. **Raw Key Storage**: Raw API keys are only shown once. Store them securely in environment variables or secure vaults.

2. **User Verification**: Use the `--user-id` flag with deactivate and rotate commands to ensure you're operating on the correct user's keys.

3. **Scope Management**: Only grant the minimum scopes needed for each integration.

4. **Key Rotation**: Regularly rotate API keys using the rotate command.

### Troubleshooting

#### Common Issues

1. **Module not found**: Make sure you're using the shell wrapper (`manage_api_keys.sh`) or have set `PYTHONPATH` correctly.

2. **Database connection**: Ensure the database is running and accessible.

3. **User not found**: Verify the user ID exists in the database.

4. **Permission denied**: Make sure the script files are executable (`chmod +x scripts/manage_api_keys.sh`).

#### Getting User IDs

To get a user ID for testing, you can:

1. Use the web API to create a user and get their ID
2. Query the database directly: `SELECT id, email FROM users;`
3. Use the admin CLI: `./scripts/admin_cli.sh list-users`

---

## Next Steps

Now that you understand authentication, you can:
1. **Customize user fields**: Add more information to user profiles
2. **Add role-based access**: Create different user roles (admin, moderator, etc.)
3. **Implement social login**: Add more OAuth providers (Facebook, GitHub, etc.)
4. **Add two-factor authentication**: Extra security layer
5. **Create user management**: Admin panel for managing users
6. **Automate API key management**: Use the CLI for CI/CD and automation

The authentication system is designed to be secure, flexible, and easy to use. It handles all the complex security details so you can focus on building your app's features! 