# Database Management Guide

This guide covers database operations in your FastAPI application, including models, migrations, CRUD operations, and async database sessions.

## 🗄️ Overview

The database system is built with **async-first architecture** and provides:

- **PostgreSQL Database** with connection pooling
- **Async SQLAlchemy** for all database operations
- **Alembic Migrations** for schema management
- **Domain-Based CRUD** operations organized by business logic
- **Type-Safe Models** with full type annotations
- **Connection Pooling** for optimal performance
- **Audit Logging** for data changes

## 📁 Architecture

The database system is organized in a **domain-based structure**:

```
app/
├── database/              # Database configuration
│   ├── database.py       # Async database setup
│   └── __init__.py       # Database exports
├── models/               # Database models (domain-based)
│   ├── auth/            # Authentication models
│   │   ├── user.py      # User model
│   │   ├── api_key.py   # API key model
│   │   └── refresh_token.py # Refresh token model
│   ├── core/            # Core models
│   │   └── base.py      # Base model with common fields
│   └── system/          # System models
│       └── audit_log.py # Audit logging model
├── crud/                # Database operations (domain-based)
│   ├── auth/            # Authentication CRUD operations
│   │   ├── user.py      # User database operations
│   │   ├── api_key.py   # API key operations
│   │   └── refresh_token.py # Session management
│   └── system/          # System CRUD operations
│       ├── admin.py     # Admin operations
│       └── audit_log.py # Audit logging
└── alembic/             # Database migrations
    ├── env.py           # Migration environment
    ├── script.py.mako   # Migration template
    └── versions/        # Migration files
```

## 🚀 Quick Start

### **1. Database Connection**

```python
from app.database.database import AsyncSessionLocal, get_db

# Get async database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Use in endpoints
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    users = await get_users(db)
    return users
```

### **2. Basic CRUD Operations**

```python
from app.crud.auth.user import get_user_by_email, create_user
from app.schemas.auth.user import UserCreate

# Create user
async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    user = await create_user(db, user_data)
    return user

# Get user by email
async def get_user(db: AsyncSession, email: str) -> User | None:
    user = await get_user_by_email(db, email=email)
    return user
```

### **3. Database Migrations**

```bash
# Create new migration
alembic revision --autogenerate -m "Add user profile fields"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration status
alembic current
```

## 🔧 Core Components

### **Async Database Sessions**

All database operations use **async sessions** for optimal performance:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_async_engine

# Create async engine
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/dbname",
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Use in operations
async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    user = User(**user_data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

### **Domain-Based Models**

Models are organized by business domain:

```python
# User model (app/models/auth/user.py)
from app.models.core.base import Base, SoftDeleteMixin, TimestampMixin
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
import uuid

class User(Base, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(254), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_superuser = Column(Boolean, default=False, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    
    # OAuth fields
    oauth_provider = Column(String(20), nullable=True)
    oauth_id = Column(String(255), nullable=True)
    oauth_email = Column(String(254), nullable=True)
    
    # Token fields for verification and password reset
    verification_token = Column(String(255), nullable=True, unique=True)
    verification_token_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    password_reset_token = Column(String(255), nullable=True, unique=True)
    password_reset_token_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Account deletion fields (GDPR compliance)
    deletion_requested_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deletion_confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deletion_scheduled_for = Column(TIMESTAMP(timezone=True), nullable=True)
    deletion_token = Column(String(255), nullable=True, unique=True)
    deletion_token_expires = Column(TIMESTAMP(timezone=True), nullable=True)
```

### **Type-Safe CRUD Operations**

All CRUD operations are fully typed and async:

```python
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User
from app.schemas.auth.user import UserCreate

# Type alias for async sessions
DBSession = AsyncSession

async def get_user_by_email(db: DBSession, email: str) -> User | None:
    result = await db.execute(
        select(User).filter(User.email == email, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()

async def create_user(db: DBSession, user_data: UserCreate) -> User:
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        is_superuser=user_data.is_superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_user(db: DBSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, str(user.hashed_password)):
        return None
    return user
```

## 📋 Available Operations

### **User Operations**

```python
from app.crud.auth.user import (
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    create_user,
    authenticate_user,
    get_users,
    count_users,
    soft_delete_user,
    restore_user,
    permanently_delete_user,
    get_user_by_oauth_id,
    create_oauth_user,
    verify_user,
    update_verification_token,
    get_user_by_verification_token,
    update_password_reset_token,
    get_user_by_password_reset_token,
    reset_user_password,
    update_user_password,
    update_deletion_token,
    get_user_by_deletion_token,
    schedule_user_deletion,
    confirm_user_deletion,
    cancel_user_deletion,
    get_users_for_deletion_reminder,
    get_users_for_permanent_deletion,
    get_deleted_users,
    count_deleted_users,
    get_user_by_id_any_status
)

# Get user by email
user = await get_user_by_email(db, "user@example.com")

# Get user by username
user = await get_user_by_username(db, "johndoe")

# Get user by ID
user = await get_user_by_id(db, "user-uuid-here")

# Create new user
user_data = UserCreate(
    email="newuser@example.com",
    password="securepassword123",
    username="newuser"
)
user = await create_user(db, user_data)

# Authenticate user
authenticated_user = await authenticate_user(db, "user@example.com", "password")

# Get all users with pagination
users = await get_users(db, skip=0, limit=10)

# Count users
user_count = await count_users(db)

# Soft delete user
await soft_delete_user(db, user.id)

# Restore deleted user
await restore_user(db, user.id)

# Permanently delete user
await permanently_delete_user(db, user.id)

# OAuth operations
oauth_user = await get_user_by_oauth_id(db, "google", "oauth_id_here")
new_oauth_user = await create_oauth_user(
    db, 
    email="oauth@example.com", 
    username="oauth_user",
    oauth_provider="google",
    oauth_id="oauth_id",
    oauth_email="oauth@example.com"
)

# Account deletion operations
await schedule_user_deletion(db, user.id, scheduled_date)
await confirm_user_deletion(db, user.id)
await cancel_user_deletion(db, user.id)

# Get users for deletion processing
reminder_users = await get_users_for_deletion_reminder(db)
permanent_deletion_users = await get_users_for_permanent_deletion(db)

# Get deleted users
deleted_users = await get_deleted_users(db, skip=0, limit=10)
deleted_count = await count_deleted_users(db)
```

### **API Key Operations**

```python
from app.crud.auth.api_key import (
    create_api_key,
    get_user_api_keys,
    get_api_key_by_id,
    deactivate_api_key,
    rotate_api_key,
    verify_api_key_in_db,
    get_api_key_by_hash,
    count_user_api_keys,
    get_all_api_keys,
    count_all_api_keys
)

# Create API key
api_key = await create_api_key(db, api_key_data, user_id=user.id, raw_key="raw_key")

# Get user's API keys
api_keys = await get_user_api_keys(db, user_id=user.id)

# Get API key by ID
api_key = await get_api_key_by_id(db, key_id=api_key.id)

# Deactivate API key
await deactivate_api_key(db, key_id=api_key.id)

# Rotate API key
new_api_key, new_raw_key = await rotate_api_key(db, key_id=api_key.id)

# Verify API key
user = await verify_api_key_in_db(db, api_key="sk_abc123...")

# Get API key by hash
api_key = await get_api_key_by_hash(db, key_hash="hash_here")

# Count user API keys
count = await count_user_api_keys(db, user_id=user.id)

# Get all API keys (admin)
all_keys = await get_all_api_keys(db, skip=0, limit=100)
total_count = await count_all_api_keys(db)
```

### **Session Management**

```python
from app.crud.auth.refresh_token import (
    create_refresh_token,
    get_refresh_token_by_hash,
    revoke_refresh_token,
    get_user_sessions,
    revoke_all_user_sessions,
    cleanup_expired_tokens,
    revoke_refresh_token_by_id,
    get_user_session_count,
    verify_refresh_token_in_db,
    enforce_session_limit
)

# Create refresh token
refresh_token = await create_refresh_token(
    db, 
    user_id=user.id, 
    token_hash="token_hash_here",
    device_info="device_info",
    ip_address="192.168.1.1"
)

# Get refresh token by hash
token = await get_refresh_token_by_hash(db, token_hash="token_hash_here")

# Revoke specific token
await revoke_refresh_token(db, token_hash="token_hash_here")

# Get user sessions
sessions = await get_user_sessions(db, user_id=user.id)

# Revoke all user sessions
revoked_count = await revoke_all_user_sessions(db, user_id=user.id)

# Cleanup expired tokens
cleaned_count = await cleanup_expired_tokens(db)

# Get user session count
session_count = await get_user_session_count(db, user_id=user.id)

# Verify refresh token in database
token = await verify_refresh_token_in_db(db, token_hash="token_hash_here")

# Enforce session limits
await enforce_session_limit(db, user_id=user.id, max_sessions=5)
```

### **Audit Logging**

```python
from app.crud.system.audit_log import (
    create_audit_log,
    get_audit_logs_by_user,
    get_audit_logs_by_event_type,
    get_audit_logs_by_session,
    get_recent_audit_logs,
    get_failed_audit_logs,
    cleanup_old_audit_logs
)

# Log user action
await create_audit_log(
    db,
    event_type="user_login",
    user_id=user.id,
    ip_address="192.168.1.100",
    success=True,
    context={"login_method": "email"}
)

# Log system event
await create_audit_log(
    db,
    event_type="api_key_created",
    user_id=user.id,
    success=True,
    context={"api_key_id": api_key.id}
)

# Get audit logs by user
user_logs = await get_audit_logs_by_user(db, user_id=user.id, limit=100, offset=0)

# Get audit logs by event type
login_logs = await get_audit_logs_by_event_type(db, event_type="user_login", limit=100, offset=0)

# Get audit logs by session
session_logs = await get_audit_logs_by_session(db, session_id="session_id", limit=100, offset=0)

# Get recent audit logs
recent_logs = await get_recent_audit_logs(db, limit=100, offset=0)

# Get failed audit logs
failed_logs = await get_failed_audit_logs(db, limit=100, offset=0)

# Cleanup old audit logs
cleaned_count = await cleanup_old_audit_logs(db, days_to_keep=90)
```

## 🗄️ Database Migrations

### **Creating Migrations**

```bash
# Create migration for model changes
alembic revision --autogenerate -m "Add user profile fields"

# Create empty migration
alembic revision -m "Add custom SQL"

# Create migration with specific dependencies
alembic revision --autogenerate -m "Add user roles" --depends-on=abc123
```

### **Applying Migrations**

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade abc123

# Apply migrations to specific revision
alembic upgrade +2

# Rollback migrations
alembic downgrade -1
alembic downgrade base
```

### **Migration Management**

```bash
# Check current migration
alembic current

# Check migration history
alembic history

# Check migration status
alembic show abc123

# Generate migration SQL
alembic upgrade head --sql
```

### **Example Migration**

```python
# alembic/versions/abc123_add_user_profile.py
"""Add user profile fields

Revision ID: abc123
Revises: def456
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add new columns
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    
    # Create index
    op.create_index(op.f('ix_users_first_name'), 'users', ['first_name'], unique=False)

def downgrade() -> None:
    # Remove index
    op.drop_index(op.f('ix_users_first_name'), table_name='users')
    
    # Remove columns
    op.drop_column('users', 'phone')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
```

## 🔧 Configuration

### **Database Settings**

```python
# app/core/config/config.py
class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/fastapi_template"
    
    # Connection pool settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600  # 1 hour
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True
```

### **Environment Variables**

```bash
# Database connection
DATABASE_URL=postgresql://postgres:password@localhost:5432/your_project

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_POOL_TIMEOUT=30
DB_POOL_PRE_PING=true
```

## 🚀 Advanced Features

### **Connection Pooling**

```python
from app.database.database import engine

# Get pool statistics
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked in: {pool.checkedin()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
```

### **Query Optimization**

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Eager loading with relationships
query = select(User).options(
    selectinload(User.api_keys),
    selectinload(User.refresh_tokens)
)
result = await db.execute(query)
users = result.scalars().all()

# Pagination
query = select(User).offset(skip).limit(limit)
result = await db.execute(query)
users = result.scalars().all()

# Filtering
query = select(User).filter(
    User.is_active == True,
    User.is_verified == True
)
result = await db.execute(query)
active_users = result.scalars().all()
```

### **Bulk Operations**

```python
from sqlalchemy import insert

# Bulk insert
users_data = [
    {"email": "user1@example.com", "username": "user1"},
    {"email": "user2@example.com", "username": "user2"},
    {"email": "user3@example.com", "username": "user3"}
]

await db.execute(insert(User), users_data)
await db.commit()

# Bulk update
from sqlalchemy import update

await db.execute(
    update(User)
    .where(User.is_active == False)
    .values(is_active=True)
)
await db.commit()
```

### **Database Health Checks**

```python
from sqlalchemy import text

async def check_database_health(db: AsyncSession) -> dict[str, Any]:
    try:
        # Test basic connectivity
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        # Test more complex query
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        return {
            "status": "healthy",
            "user_count": user_count,
            "connection": "ok"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }
```

## 🛠️ Troubleshooting

### **Common Issues**

**1. "Connection refused"**
- Check if PostgreSQL is running
- Verify connection string in DATABASE_URL
- Ensure database exists

**2. "Table doesn't exist"**
- Run migrations: `alembic upgrade head`
- Check if tables were created properly

**3. "Pool exhausted"**
- Increase pool size in settings
- Check for connection leaks
- Monitor pool statistics

**4. "Transaction rollback"**
- Check for constraint violations
- Verify data types match schema
- Look for foreign key issues

### **Debug Commands**

```bash
# Check database connection
docker-compose exec postgres psql -U postgres -d your_db -c "SELECT 1;"

# Check tables
docker-compose exec postgres psql -U postgres -d your_db -c "\dt"

# Check migration status
alembic current

# Check pool statistics
python -c "from app.database.database import engine; print(engine.pool.status())"
```

### **Performance Monitoring**

```python
import time
from app.database.database import engine

async def monitor_query_performance():
    start_time = time.time()
    
    # Your database operation
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    execution_time = time.time() - start_time
    print(f"Query executed in {execution_time:.3f} seconds")
    
    # Pool statistics
    pool = engine.pool
    print(f"Pool size: {pool.size()}")
    print(f"Checked out: {pool.checkedout()}")
```

## 📚 Next Steps

1. **Explore the Models**: Check out the models in `app/models/` to understand the data structure
2. **Read the CRUD Guide**: Learn about CRUD operations in `app/crud/`
3. **Check the Testing Guide**: See how to test database operations in [Testing Guide](testing-and-development.md)
4. **Deploy to Production**: Follow the [Deployment Guide](deployment-and-production.md)

---

**Happy coding! 🗄️** 