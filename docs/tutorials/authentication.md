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

## Next Steps

Now that you understand authentication, you can:
1. **Customize user fields**: Add more information to user profiles
2. **Add role-based access**: Create different user roles (admin, moderator, etc.)
3. **Implement social login**: Add more OAuth providers (Facebook, GitHub, etc.)
4. **Add two-factor authentication**: Extra security layer
5. **Create user management**: Admin panel for managing users

The authentication system is designed to be secure, flexible, and easy to use. It handles all the complex security details so you can focus on building your app's features! 