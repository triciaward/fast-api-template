# CRUD Scaffolding CLI Tutorial

**Generate complete CRUD boilerplate in seconds, not minutes!**

This tutorial shows you how to use the built-in CRUD scaffolding tool to rapidly create new resources in your FastAPI application.

## 🎯 What You'll Learn

- How to use the CRUD scaffolding CLI
- What files get generated and why
- How to customize generated code
- Best practices for rapid development

## 🚀 Quick Start

### Basic Usage

```bash
# Generate a simple Post model
python scripts/generate_crud.py Post title:str content:str is_published:bool
```

This single command generates:
- ✅ SQLAlchemy model with proper fields
- ✅ Pydantic schemas (create, update, response)
- ✅ CRUD operations (create, read, update, delete)
- ✅ FastAPI endpoints with full CRUD
- ✅ Basic test coverage
- ✅ Auto-registration in API router

### Advanced Usage

```bash
# Generate with soft delete functionality
python scripts/generate_crud.py Post title:str content:str is_published:bool --soft-delete

# Generate with search capabilities
python scripts/generate_crud.py Product name:str price:float description:str --searchable

# Generate with admin integration
python scripts/generate_crud.py Category name:str slug:str --admin --slug
```

## 📋 Command Reference

### Syntax

```bash
python scripts/generate_crud.py <ModelName> <field1:type1> <field2:type2> [options]
```

### Parameters

- **ModelName**: The name of your model (e.g., `Post`, `Product`, `User`)
- **fields**: Space-separated field specifications in `name:type` format
- **options**: Optional flags to enable additional features

### Field Types

| Type | SQLAlchemy | Pydantic | Description |
|------|------------|----------|-------------|
| `str` | `String` | `str` | Short text fields |
| `int` | `Integer` | `int` | Integer numbers |
| `float` | `Float` | `float` | Decimal numbers |
| `bool` | `Boolean` | `bool` | True/false values |
| `datetime` | `DateTime` | `datetime` | Date and time |
| `date` | `Date` | `date` | Date only |
| `uuid` | `UUID(as_uuid=True)` | `uuid.UUID` | UUID identifiers |
| `text` | `Text` | `str` | Long text content |
| `json` | `JSON` | `dict` | JSON data |

### Options

| Option | Description |
|--------|-------------|
| `--soft-delete` | Include soft delete functionality with restoration |
| `--searchable` | Add search and filtering capabilities |
| `--admin` | Include admin panel integration |
| `--slug` | Auto-generate slug field from title |

## 🔍 What Gets Generated

### 1. Model File (`app/models/post.py`)

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.database.database import Base
from app.models.models import SoftDeleteMixin

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

### 2. Schema File (`app/schemas/post.py`)

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
    id: uuid.UUID
    date_created: datetime
    title: str
    content: str
    is_published: bool
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    deletion_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PostListResponse(PaginatedResponse[PostResponse]):
    pass
```

**Features:**
- Base schema for shared fields
- Create schema for new records
- Update schema with optional fields
- Response schema with all fields
- Paginated response wrapper
- Soft delete fields (if enabled)

### 3. CRUD File (`app/crud/post.py`)

```python
from typing import List, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate

# Type alias for both sync and async sessions
DBSession = Union[AsyncSession, Session]

async def get_post_by_id(db: DBSession, post_id: str) -> Optional[Post]:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(Post).filter(Post.id == post_id, Post.is_deleted.is_(False))
        )
    else:
        result = db.execute(
            select(Post).filter(Post.id == post_id, Post.is_deleted.is_(False))
        )
    return result.scalar_one_or_none()

async def create_post(db: DBSession, obj: PostCreate) -> Post:
    db_obj = Post(**obj.dict())
    db.add(db_obj)
    if isinstance(db, AsyncSession):
        await db.commit()
        try:
            await db.refresh(db_obj)
        except Exception:
            pass
    else:
        db.commit()
        try:
            db.refresh(db_obj)
        except Exception:
            pass
    return db_obj

# ... more CRUD functions
```

**Features:**
- Hybrid async/sync support
- Proper error handling
- Soft delete filtering (if enabled)
- Type-safe operations

### 4. Endpoints File (`app/api/api_v1/endpoints/post.py`)

```python
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import post as crud_post
from app.database.database import get_db
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostListResponse
from app.utils.pagination import PaginationParams

router = APIRouter()

@router.get("", response_model=PostListResponse)
async def list_posts(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> PostListResponse:
    """
    List posts with pagination.
    """
    posts = await crud_post.get_posts(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    total = await crud_post.count_posts(db=db)
    
    return PostListResponse(
        items=posts,
        total=total,
        page=pagination.page,
        per_page=pagination.limit,
        total_pages=(total + pagination.limit - 1) // pagination.limit,
    )

# ... more endpoints
```

**Features:**
- Full CRUD endpoints
- Proper HTTP status codes
- Pagination support
- Error handling
- Auto-generated documentation

### 5. Test File (`tests/template_tests/test_post.py`)

```python
import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.post import Post
from app.schemas.post import PostCreate

# Test data
test_post_data = {
    "title": "Test title",
    "content": "Test content",
    "is_published": True,
}

def test_create_post(client: TestClient, db: Session):
    """Test creating a post."""
    response = client.post("/api/v1/posts", json=test_post_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == test_post_data["title"]
    assert "id" in data

# ... more tests
```

**Features:**
- Basic CRUD test coverage
- Proper test data setup
- Status code validation
- Response structure validation

## 🎯 Real-World Examples

### Example 1: Blog Post System

```bash
python scripts/generate_crud.py Post title:str content:text is_published:bool author_id:uuid --soft-delete
```

**Generated endpoints:**
- `GET /api/v1/posts` - List all posts
- `POST /api/v1/posts` - Create new post
- `GET /api/v1/posts/{id}` - Get specific post
- `PUT /api/v1/posts/{id}` - Update post
- `DELETE /api/v1/posts/{id}` - Soft delete post

### Example 2: E-commerce Product Catalog

```bash
python scripts/generate_crud.py Product name:str price:float description:text category_id:uuid stock:int --searchable --soft-delete
```

**Features added:**
- Search by name and description
- Filter by category and price range
- Sort by price, name, or date
- Stock management

### Example 3: User Management System

```bash
python scripts/generate_crud.py User email:str username:str is_active:bool role:str --admin --soft-delete
```

**Features added:**
- Admin panel integration
- Role-based access control
- User activity tracking
- Bulk operations

## 🔧 Customization Guide

### After Generation

1. **Review the generated files** - Understand the structure
2. **Add business logic** - Customize validation and business rules
3. **Add relationships** - Define foreign keys and relationships
4. **Customize endpoints** - Add specific business logic
5. **Enhance tests** - Add more comprehensive test coverage

### Common Customizations

#### Adding Relationships

```python
# In models/post.py
from app.models.models import User

class Post(Base, SoftDeleteMixin):
    # ... existing fields ...
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author = relationship("User", back_populates="posts")
```

#### Adding Validation

```python
# In schemas/post.py
from pydantic import Field, field_validator

class PostCreate(PostBase):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
```

#### Adding Business Logic

```python
# In crud/post.py
async def create_post(db: DBSession, obj: PostCreate, author_id: str) -> Post:
    db_obj = Post(**obj.dict(), author_id=author_id)
    # Add business logic here
    db.add(db_obj)
    # ... rest of function
```

## 🚀 Next Steps

### 1. Run Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add Post model"

# Apply migration
alembic upgrade head
```

### 2. Test Your Endpoints

```bash
# Run the generated tests
pytest tests/template_tests/test_post.py

# Test manually
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Post", "content": "Hello World!", "is_published": true}'
```

### 3. Customize and Extend

- Add authentication to endpoints
- Implement custom business logic
- Add more validation rules
- Create additional endpoints
- Enhance test coverage

## 🎉 Benefits

### Time Savings
- **Before**: 30-60 minutes of manual setup
- **After**: 30 seconds of automated generation

### Consistency
- All generated code follows established patterns
- Consistent naming conventions
- Standardized error handling
- Uniform API structure

### Quality
- Type-safe operations
- Proper validation
- Error handling
- Test coverage included

### Maintainability
- Clear separation of concerns
- Modular architecture
- Easy to extend and modify
- Well-documented code

## 🔍 Troubleshooting

### Common Issues

**Import errors after generation:**
```bash
# Make sure you're in the project root
cd /path/to/your/project

# Install dependencies if needed
pip install -r requirements.txt
```

**Migration conflicts:**
```bash
# Reset migrations if needed
alembic downgrade base
alembic upgrade head
```

**Test failures:**
```bash
# Check database connection
# Ensure test database is properly configured
# Review generated test data
```

### Getting Help

- Check the generated code for syntax errors
- Review the template's existing patterns
- Consult the FastAPI documentation
- Check the test suite for examples

---

**Ready to boost your development speed?** Start with a simple model and gradually add complexity as you become familiar with the patterns! 