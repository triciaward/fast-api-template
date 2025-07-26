# Database Management Tutorial

Welcome to the database management tutorial! This guide will teach you how to work with the database in your FastAPI application, from basic operations to advanced features like migrations and search.

---

## What is a Database?

Think of a database like a digital filing cabinet. It stores all your app's information in an organized way:
- **Users**: Account information, profiles, settings
- **Data**: Any information your app needs to remember
- **Relationships**: How different pieces of data connect to each other

---

## Database Features Included

### 🗄️ Core Database Features
- **PostgreSQL**: Professional-grade database for reliability
- **SQLAlchemy**: Python library for database operations
- **Connection Pooling**: Efficient database connections
- **Migrations**: Version-controlled database changes

### 🔍 Data Management Features
- **Soft Delete**: Hide data instead of permanently deleting it
- **Search & Filter**: Find data quickly and efficiently
- **Pagination**: Handle large amounts of data
- **Audit Logging**: Track all data changes

### 🛡️ Data Safety Features
- **Data Validation**: Ensure data is correct before saving
- **Type Safety**: Prevent data type errors
- **Backup Support**: Easy database backups
- **Transaction Support**: Ensure data consistency

### 🚀 **CRUD Scaffolding**
- **One-command generation**: Create complete CRUD boilerplate
- **Automatic relationships**: Handle complex data connections
- **Search and filtering**: Built-in search capabilities
- **Admin integration**: Optional admin panel integration

---

## 📁 Database Models Structure

The template uses a modular approach with separated model files:

```
app/models/
├── __init__.py          # Export all models
├── base.py             # Base model and mixins
├── user.py             # User model
├── api_key.py          # API key model
├── audit_log.py        # Audit log model
└── refresh_token.py    # Refresh token model
```

### Base Model and Mixins

The `base.py` file contains shared functionality:

```python
# app/models/base.py
class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models."""
    
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True, index=True)
    deletion_reason = Column(String(500), nullable=True)
    
    def soft_delete(self, deleted_by: uuid.UUID = None, reason: str = None):
        """Mark the record as deleted without actually removing it."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        self.deletion_reason = reason
```

### Individual Model Files

Each model is in its own file for better organization:

```python
# app/models/user.py
class User(Base, SoftDeleteMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    # ... other fields
```

---

## Real Example: Add a `bio` Field to User

Let's walk through a real example of adding a `bio` field to the user model, updating the schema, generating a migration, and using the new field via the API.

### 1. Update the SQLAlchemy Model ([app/models/user.py](../../app/models/user.py))
```python
class User(Base, SoftDeleteMixin):
    # ... existing fields ...
    bio = Column(String, nullable=True)
```

### 2. Update the Pydantic Schema ([app/schemas/user.py](../../app/schemas/user.py))
```python
class UserUpdate(BaseModel):
    bio: Optional[str] = None
```

### 3. Generate a Migration
```bash
alembic revision --autogenerate -m "Add bio field to user"
```

### 4. Apply the Migration
```bash
alembic upgrade head
```

### 5. Test the New Field
```bash
# Update user bio
curl -X PUT "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bio": "I love coding!"}'
```

---

## 🚀 CRUD Scaffolding

The template includes a powerful CRUD scaffolding tool that generates complete CRUD boilerplate with one command.

### Basic Usage

```bash
# Generate a Post model with title, content, and is_published fields
python3 scripts/generate_crud.py Post title:str content:str is_published:bool
```

### Advanced Options

```bash
# Generate a Product model with soft delete and search capabilities
python scripts/generate_crud.py Product name:str price:float description:str --soft-delete --searchable

# Generate an admin-managed Category model
python scripts/generate_crud.py Category name:str slug:str --admin

# Generate a model with slug auto-generation
python scripts/generate_crud.py Article title:str content:str --slug
```

### What Gets Generated

#### 1. Model File (`app/models/post.py`)

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.database.database import Base
from app.models import SoftDeleteMixin

class Post(Base, SoftDeleteMixin):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    is_published = Column(Boolean, default=False, nullable=True)

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title={self.title}, content={self.content}, is_published={self.is_published})>"
```

**Features:**
- Proper table naming (pluralized)
- UUID primary key with indexing
- Automatic `date_created` timestamp
- Soft delete mixin (if enabled)
- Proper field types and constraints

#### 2. Schema File (`app/schemas/post.py`)

```python
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from app.utils.pagination import PaginatedResponse

class PostBase(BaseModel):
    title: str
    content: str
    is_published: bool = False

class PostCreate(PostBase):
    title: str
    content: str
    is_published: bool = False

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    date_created: datetime
    
    class Config:
        from_attributes = True

class PostPaginatedResponse(PaginatedResponse):
    items: list[PostResponse]
```

**Features:**
- Input validation schemas
- Response schemas with proper typing
- Pagination support
- Optional field updates

#### 3. CRUD File (`app/crud/post.py`)

```python
from typing import Any, Dict, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.crud.base import CRUDBase
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate
from app.utils.search_filter import apply_search_filters

class CRUDPost(CRUDBase[Post, PostCreate, PostUpdate]):
    def get_by_title(self, db: Session, *, title: str) -> Optional[Post]:
        return db.query(Post).filter(Post.title == title).first()
    
    def get_published_posts(self, db: Session, *, skip: int = 0, limit: int = 100):
        return db.query(Post).filter(Post.is_published == True).offset(skip).limit(limit).all()

post = CRUDPost(Post)
```

**Features:**
- Base CRUD operations (create, read, update, delete)
- Custom query methods
- Search and filtering support
- Pagination handling

#### 4. API Endpoints (`app/api/api_v1/endpoints/post.py`)

```python
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.utils.pagination import PaginationParams

router = APIRouter()

@router.get("/", response_model=schemas.PostPaginatedResponse)
def read_posts(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search term"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
) -> Any:
    """
    Retrieve posts with pagination and search.
    """
    posts = crud.post.get_multi_with_pagination(
        db, pagination=pagination, search=search, is_published=is_published
    )
    return posts

@router.post("/", response_model=schemas.PostResponse)
def create_post(
    *,
    db: Session = Depends(deps.get_db),
    post_in: schemas.PostCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new post.
    """
    post = crud.post.create(db=db, obj_in=post_in)
    return post

# ... more endpoints for GET /{id}, PUT /{id}, DELETE /{id}
```

**Features:**
- Full CRUD endpoints
- Pagination support
- Search and filtering
- Authentication integration
- Proper error handling

#### 5. Test File (`tests/template_tests/test_post.py`)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.schemas.post import PostCreate

def test_create_post(client: TestClient, db: Session) -> None:
    """Test creating a new post."""
    post_data = {
        "title": "Test Post",
        "content": "This is a test post",
        "is_published": True
    }
    
    response = client.post("/api/v1/posts/", json=post_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == post_data["title"]
    assert data["content"] == post_data["content"]
    assert data["is_published"] == post_data["is_published"]

# ... more tests
```

**Features:**
- Unit tests for all endpoints
- Integration tests
- Edge case testing
- Proper test isolation

### Available Options

| Option | Description |
|--------|-------------|
| `--soft-delete` | Include soft delete functionality with restoration |
| `--searchable` | Add search and filtering capabilities |
| `--admin` | Include admin panel integration |
| `--slug` | Auto-generate slug field from title |

### Next Steps After Generation

1. **Review the generated files** in `app/models/`, `app/schemas/`, `app/crud/`, and `app/api/`
2. **Run database migrations**:
   ```bash
   alembic revision --autogenerate -m "Add Post model"
   alembic upgrade head
   ```
3. **Test the endpoints**:
   ```bash
   pytest tests/template_tests/test_post.py
   ```
4. **Customize as needed** - Add relationships, validation, or business logic

---

## Database Operations

### Basic CRUD Operations

#### Create
```python
from app.crud import user as crud_user
from app.schemas.user import UserCreate

# Create a new user
user_data = UserCreate(
    email="user@example.com",
    username="newuser",
    password="securepassword123"
)
user = crud_user.create(db, obj_in=user_data)
```

#### Read
```python
# Get user by ID
user = crud_user.get(db, id=user_id)

# Get user by email
user = crud_user.get_by_email(db, email="user@example.com")

# Get multiple users with pagination
users = crud_user.get_multi(db, skip=0, limit=100)
```

#### Update
```python
from app.schemas.user import UserUpdate

# Update user
update_data = UserUpdate(username="newusername")
user = crud_user.update(db, db_obj=user, obj_in=update_data)
```

#### Delete
```python
# Soft delete (recommended)
crud_user.remove(db, id=user_id)

# Hard delete (permanent)
crud_user.delete(db, id=user_id)
```

### Advanced Queries

#### Search and Filtering
```python
# Search users by name or email
users = crud_user.search(db, search_term="john")

# This searches in: username, email, first_name, last_name
```

#### Pagination
```python
from app.utils.pagination import PaginationParams

# Get paginated results
pagination = PaginationParams(page=1, size=20)
users = crud_user.get_multi_with_pagination(
    db, 
    pagination=pagination,
    search="john"
)
```

#### Relationships
```python
# Get user with related data
user = crud_user.get_with_relationships(
    db, 
    id=user_id,
    relationships=["api_keys", "audit_logs"]
)
```

---

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user bio field"

# Create empty migration for manual changes
alembic revision -m "Custom data migration"
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback to previous migration
alembic downgrade -1
```

### Migration Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations on development data** first
3. **Backup your database** before applying migrations
4. **Use descriptive migration messages**
5. **Include both upgrade and downgrade logic**

### Example Migration

```python
"""Add user bio field

Revision ID: 123456789abc
Revises: previous_revision
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add bio column to users table
    op.add_column('users', sa.Column('bio', sa.String(), nullable=True))

def downgrade() -> None:
    # Remove bio column from users table
    op.drop_column('users', 'bio')
```

---

## Search and Filtering

The template includes a powerful search and filtering system.

### Basic Search

```python
# Search across multiple fields
users = crud_user.search(db, search_term="john")

# This searches in: username, email, first_name, last_name
```

### Advanced Filtering

```python
# Filter by multiple criteria
filters = {
    "is_active": True,
    "is_verified": True,
    "date_created__gte": "2024-01-01"
}

users = crud_user.get_multi_with_filters(db, filters=filters)
```

### Search Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `__exact` | Exact match | `{"username__exact": "john"}` |
| `__contains` | Contains text | `{"email__contains": "gmail"}` |
| `__startswith` | Starts with | `{"username__startswith": "j"}` |
| `__endswith` | Ends with | `{"email__endswith": ".com"}` |
| `__gte` | Greater than or equal | `{"date_created__gte": "2024-01-01"}` |
| `__lte` | Less than or equal | `{"date_created__lte": "2024-12-31"}` |
| `__in` | In list | `{"status__in": ["active", "pending"]}` |
| `__isnull` | Is null | `{"deleted_at__isnull": True}` |

### Full-Text Search

```python
# PostgreSQL full-text search
users = crud_user.full_text_search(db, query="john doe")
```

---

## Soft Delete

The template includes soft delete functionality to prevent data loss.

### Using Soft Delete

```python
# Soft delete a user (marks as deleted but keeps data)
crud_user.soft_delete(db, id=user_id, deleted_by=admin_id, reason="User request")

# Get only active users
active_users = crud_user.get_active(db)

# Get only deleted users
deleted_users = crud_user.get_deleted(db)

# Get all users (active and deleted)
all_users = crud_user.get_all(db)

# Restore a soft-deleted user
crud_user.restore(db, id=user_id)
```

### Soft Delete in Queries

```python
# By default, queries exclude soft-deleted records
users = crud_user.get_multi(db)  # Only active users

# Include soft-deleted records
users = crud_user.get_multi_including_deleted(db)

# Only soft-deleted records
users = crud_user.get_multi_deleted_only(db)
```

---

## Audit Logging

The template automatically logs database changes for audit purposes.

### Automatic Logging

```python
# These operations are automatically logged
user = crud_user.create(db, obj_in=user_data)  # CREATE
user = crud_user.update(db, db_obj=user, obj_in=update_data)  # UPDATE
crud_user.remove(db, id=user_id)  # DELETE
```

### Manual Logging

```python
from app.services.audit import log_audit_event

# Log custom events
log_audit_event(
    db=db,
    user_id=current_user.id,
    event_type="password_changed",
    success=True,
    context={"ip_address": "192.168.1.1"}
)
```

### Querying Audit Logs

```python
from app.crud import audit_log as crud_audit

# Get audit logs for a user
logs = crud_audit.get_by_user_id(db, user_id=user_id)

# Get audit logs by event type
logs = crud_audit.get_by_event_type(db, event_type="login")

# Get recent audit logs
logs = crud_audit.get_recent(db, hours=24)
```

---

## Performance Optimization

### Connection Pooling

The template uses SQLAlchemy connection pooling for better performance:

```python
# Configuration in app/core/config.py
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 30
DB_POOL_RECYCLE = 3600
DB_POOL_TIMEOUT = 30
DB_POOL_PRE_PING = True
```

### Query Optimization

```python
# Use select() for better performance
from sqlalchemy import select

# Instead of: db.query(User).filter(User.is_active == True).all()
stmt = select(User).where(User.is_active == True)
users = db.execute(stmt).scalars().all()

# Use joins to avoid N+1 queries
stmt = select(User).options(joinedload(User.api_keys))
users = db.execute(stmt).scalars().all()
```

### Indexing

```python
# Add indexes for frequently queried fields
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    email = Column(String, unique=True, index=True)  # Indexed for lookups
    username = Column(String, unique=True, index=True)  # Indexed for lookups
    is_active = Column(Boolean, default=True, index=True)  # Indexed for filtering
```

---

## Troubleshooting

### Common Issues

#### Migration Conflicts
```bash
# If migrations conflict, stamp the head
alembic stamp head

# Then create a new migration
alembic revision --autogenerate -m "Fix migration conflict"
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check connection
python -c "from app.database.database import engine; print(engine.url)"
```

#### Performance Issues
```bash
# Check slow queries
# Add to your .env file:
SQLALCHEMY_ECHO = true

# Monitor connection pool
python -c "from app.database.database import engine; print(engine.pool.status())"
```

### Debugging Queries

```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or use SQLAlchemy echo
from app.database.database import engine
engine.echo = True
```

---

## Best Practices

### 1. **Always Use Transactions**
```python
from sqlalchemy.orm import Session

def create_user_with_profile(db: Session, user_data, profile_data):
    try:
        # Create user
        user = crud_user.create(db, obj_in=user_data)
        
        # Create profile
        profile_data["user_id"] = user.id
        profile = crud_profile.create(db, obj_in=profile_data)
        
        db.commit()
        return user
    except Exception:
        db.rollback()
        raise
```

### 2. **Use Proper Data Types**
```python
# Good: Use proper UUID type
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# Good: Use proper string lengths
email = Column(String(255), unique=True, index=True)

# Good: Use proper boolean defaults
is_active = Column(Boolean, default=True, nullable=False)
```

### 3. **Validate Data at Multiple Levels**
```python
# Database level (constraints)
email = Column(String(255), unique=True, nullable=False)

# Schema level (Pydantic)
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

# Application level (business logic)
def create_user(db: Session, user_data: UserCreate):
    if crud_user.get_by_email(db, email=user_data.email):
        raise HTTPException(400, "Email already registered")
```

### 4. **Use Soft Delete for Important Data**
```python
# Instead of hard delete
# crud_user.delete(db, id=user_id)

# Use soft delete
crud_user.soft_delete(db, id=user_id, reason="User request")
```

### 5. **Optimize for Common Queries**
```python
# Add indexes for frequently queried fields
class User(Base):
    email = Column(String(255), unique=True, index=True)
    username = Column(String(255), unique=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    date_created = Column(DateTime, default=datetime.utcnow, index=True)
```

---

## Next Steps

Now that you understand database management, you can:

1. **Generate CRUD boilerplate** for your own models
2. **Customize the search and filtering** for your needs
3. **Add relationships** between your models
4. **Implement business logic** in your CRUD operations
5. **Set up monitoring** for database performance
6. **Create data migrations** for production deployments

For more advanced topics, check out:
- [Authentication Tutorial](authentication.md) - User management and security
- [Testing Tutorial](testing-and-development.md) - Testing database operations
- [Deployment Tutorial](deployment-and-production.md) - Production database setup 