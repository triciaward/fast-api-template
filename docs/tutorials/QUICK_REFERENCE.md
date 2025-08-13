# 🚀 FastAPI Template Quick Reference

**AI Agent: Use this file for quick access to common patterns, file locations, and project conventions.**

## 📁 **Project Structure Quick Reference**

```
fast-api-template/
├── app/                          # Main application code
│   ├── main.py                   # FastAPI app entry point
│   ├── api/                      # API routes and endpoints
│   │   ├── auth/                 # Authentication endpoints
│   │   ├── users/                # User management endpoints
│   │   ├── admin/                # Admin panel endpoints
│   │   ├── system/               # System endpoints (health, etc.)
│   │   └── integrations/         # WebSockets, external services
│   ├── core/                     # Core configuration and utilities
│   │   ├── config/               # Settings and environment config
│   │   ├── security/             # Security utilities and middleware
│   │   ├── error_handling/       # Error handlers and exceptions
│   │   └── admin/                # Admin system configuration
│   ├── models/                   # Database models
│   │   ├── auth/                 # User, API key, refresh token models
│   │   ├── core/                 # Base models and mixins
│   │   └── system/               # Audit log and admin models
│   ├── schemas/                  # Pydantic schemas for API
│   ├── crud/                     # Database operations
│   ├── services/                 # Business logic and external services
│   └── utils/                    # Utility functions and helpers
├── tests/                        # 173 test files (98.2% coverage)
│   ├── api/                      # API endpoint tests
│   ├── app/                      # Application lifecycle tests
│   ├── core/                     # Core functionality tests
│   ├── crud/                     # Database operation tests
│   ├── models/                   # Model tests
│   ├── schemas/                  # Schema validation tests
│   ├── services/                 # Service layer tests
│   └── utils/                    # Utility function tests
├── scripts/                      # Setup and utility scripts
├── docs/                         # Documentation and tutorials
└── docker-compose.yml            # Database and service containers
```

## 🔐 **Authentication Patterns**

### **User Authentication Flow:**
1. **Registration**: `POST /api/auth/register` → Creates user, sends verification email
2. **Login**: `POST /api/auth/login` → Returns JWT access + refresh tokens
3. **Refresh**: `POST /api/auth/refresh` → Gets new access token using refresh token
4. **Logout**: `POST /api/auth/logout` → Invalidates refresh token

### **Protected Endpoints:**
```python
from app.api.users.auth import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user: UserResponse = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}"}
```

### **API Key Authentication:**
- **System endpoints**: Require API keys with specific scopes
- **User endpoints**: Require JWT authentication
- **Admin endpoints**: Require admin privileges

## 🗄️ **Database Patterns**

### **Model Structure:**
```python
from app.models.core.base import Base, TimestampMixin, SoftDeleteMixin

class YourModel(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "your_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Always include user_id for user-owned resources
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
```

### **CRUD Operations:**
```python
# Create
async def create_item(db: AsyncSession, user_id: str, data: ItemCreate) -> Item:
    item = Item(user_id=user_id, **data.dict())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

# Read (with user isolation)
async def list_user_items(db: AsyncSession, user_id: str) -> list[Item]:
    result = await db.execute(
        select(Item).filter(Item.user_id == user_id, Item.is_deleted.is_(False))
    )
    return result.scalars().all()
```

### **Migrations:**
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## 🧪 **Testing Patterns**

### **Test File Structure:**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.unit  # Mark as unit test

client = TestClient(app)

def test_endpoint_behavior():
    # Test implementation
    pass
```

### **Test Categories:**
- **Unit tests**: Test individual functions/components
- **Integration tests**: Test API endpoints with database
- **Edge case tests**: Test error conditions and boundaries
- **Security tests**: Test authentication and authorization

### **Running Tests:**
```bash
# All tests
pytest

# Specific test file
pytest tests/api/auth/test_login.py

# With coverage
pytest --cov=app

# Optional features
ENABLE_WEBSOCKETS=true pytest tests/api/integrations/
```

## 🔧 **Development Workflow**

### **Code Quality:**
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy app/

# All quality checks
./scripts/development/validate_ci.sh
```

### **Git Workflow:**
```bash
# Check status
git status

# Add changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description of what was added"

# Push to remote
git push origin main
```

## 🚀 **Feature Building Pattern (6 Steps)**

### **1. Create Model** (`app/models/core/your_model.py`)
- Extend `Base`, `TimestampMixin`, `SoftDeleteMixin`
- Include `user_id` foreign key
- Add appropriate indexes

### **2. Create Schemas** (`app/schemas/your_model.py`)
- `YourModelCreate` - Input validation
- `YourModelResponse` - Output formatting
- Use Pydantic validation rules

### **3. Create CRUD** (`app/crud/core/your_model.py`)
- `create_your_model()` - Create new items
- `list_your_models_for_user()` - User-specific queries
- Always filter by `user_id` and `is_deleted`

### **4. Create API Routes** (`app/api/your_models/routes.py`)
- Use `get_current_user` dependency
- Return schema objects, not ORM models
- Follow REST conventions

### **5. Create Migration**
- `alembic revision --autogenerate -m "add your_models table"`
- `alembic upgrade head`

### **6. Create Tests** (`tests/api/your_models/test_your_models.py`)
- Test unauthorized access (should return 401)
- Test authorized operations
- Test edge cases and validation

## 🎯 **Common Conventions**

### **Naming:**
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

### **File Organization:**
- **Models**: `app/models/core/` for user-owned resources
- **Schemas**: `app/schemas/` matching model structure
- **CRUD**: `app/crud/core/` for core business logic
- **API**: `app/api/` organized by domain
- **Tests**: `tests/` mirroring app structure

### **Security:**
- **Always validate input** with Pydantic schemas
- **Always filter by user_id** for user-owned resources
- **Use soft delete** instead of hard delete
- **Log important actions** in audit log
- **Rate limit** public endpoints

## 🔍 **Quick Commands**

```bash
# Environment
source venv/bin/activate

# Services
docker-compose up -d

# Development
black . && ruff check . && mypy app/

# Testing
pytest

# Database
alembic upgrade head

# Git
git add . && git commit -m "Message" && git push origin main
```

---

**AI Agent: Use this reference to work efficiently with this project. Follow the established patterns and conventions for consistent, high-quality code.** 🚀
