# Build a Feature (Beginner How-To)

This step-by-step guide shows how to add a new feature to the template: database model → schemas → CRUD → API (with auth) → migrations → basic tests.

We’ll create a simple "Note" feature where authenticated users can create and list their own notes.

## ELI5: How this guide works

Think of adding a feature like adding a new "Notes" room to your house (the app). You do it in small, safe steps:

## 🤖 **AI-Assisted Development: The Most Efficient Way to Build Features**

**Don't know where to start?** Use this prompt with your AI assistant (Cursor AI, Claude, ChatGPT) to get guided, step-by-step help:

---

### **🎯 Copy-Paste This Prompt:**

```
I want to build a [FEATURE_NAME] feature for my FastAPI project, but I'm not sure how to start. 
I'm following the building-a-feature.md tutorial which has 6 steps:
1. Create database model
2. Create schemas  
3. Create CRUD functions
4. Create API routes
5. Create database migration
6. Create basic tests

Can you help me build this feature step by step, following the tutorial pattern? 
Start with step 1 and explain each decision as we go. I want to understand WHY we're doing each step, 
not just copy-paste code.

My feature idea: [DESCRIBE YOUR FEATURE HERE]
```

---

### **🚀 How to Use This Prompt:**

1. **Replace `[FEATURE_NAME]`** with what you want to build (e.g., "Task", "Project", "Comment")
2. **Replace `[DESCRIBE YOUR FEATURE HERE]`** with details about your feature
3. **Copy-paste into your AI assistant** (Cursor AI, Claude, ChatGPT)
4. **Follow along step by step** - don't rush ahead!

### **💡 Pro Tips for Maximum Learning:**

- **Ask for one step at a time** - "Great! Now let's do step 2 - schemas"
- **Test each step** - Make sure it works before moving forward
- **Ask "why" questions** - "Why do we use UUID instead of auto-increment?"
- **Request examples** - "Can you show me how to test this endpoint?"
- **Get explanations** - "What does this security pattern protect against?"

### **🎯 Example Feature Ideas to Try:**

- **Task Management**: Users can create, edit, and complete tasks
- **Project Organization**: Users can group tasks into projects
- **File Uploads**: Users can upload and manage files
- **Comments System**: Users can comment on posts or items
- **Categories/Tags**: Users can organize content with labels

---

**Now let's get building!** 🚀

- **Blueprint (database model)**: the structure of a Note
  - File: `app/models/core/note.py`
  - Fields: `id`, `user_id`, `title`, `body`
  - Uses timestamp/soft-delete mixins and is auto-discovered by the app

- **Shapes (schemas)**: what requests and responses look like
  - File: `app/schemas/note.py`
  - `NoteCreate` = what the user must send
  - `NoteResponse` = what the API returns

- **Store/fetch (CRUD)**: save and list notes
  - File: `app/crud/core/note.py`
  - `create_note` saves a note; `list_notes_for_user` fetches your notes

- **Doors (API routes)**: URLs people use
  - File: `app/api/notes/routes.py`
  - POST `/notes/` creates your note; GET `/notes/` lists your notes
  - Both require login via `get_current_user` and a DB session

- **Hook into the main hallway (router)**: make routes visible
  - File: `app/api/__init__.py`
  - Include the notes router under `settings.API_V1_STR` so endpoints appear at `/api/notes`

- **Update the building plan (migrations) and check the lock (tests)**
  - Run: `alembic revision --autogenerate` then `alembic upgrade head`
  - Minimal test ensures unauthenticated access returns 401 on `/api/notes`

### Quick security notes
- Routes require JWT via `get_current_user`
- Keep endpoints under `/api` to inherit stricter cache-control
- Add API key scopes only for system automation
- Validate inputs with Pydantic and return schema objects, not ORM models

### What you end up with
- A working "Notes" feature: model, schemas, CRUD, secured routes under `/api/notes`, a migration, and a starter test

## 1) Create the model
Create `app/models/core/note.py`:
```python
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.core.base import Base, TimestampMixin, SoftDeleteMixin

class Note(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    body = Column(String(2000), nullable=False)
```

Nothing else to register – models auto-discover via imports already present in `app/models/__init__.py`.

## 2) Create schemas
Create `app/schemas/note.py`:
```python
from pydantic import BaseModel, Field

class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=2000)

class NoteResponse(BaseModel):
    id: str
    title: str
    body: str

    class Config:
        from_attributes = True
```

## 3) CRUD functions
Create `app/crud/core/note.py`:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Note
from app.schemas.note import NoteCreate

async def create_note(db: AsyncSession, user_id: str, data: NoteCreate) -> Note:
    note = Note(user_id=user_id, title=data.title, body=data.body)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

async def list_notes_for_user(db: AsyncSession, user_id: str, skip: int = 0, limit: int = 20) -> list[Note]:
    result = await db.execute(
        select(Note).filter(Note.user_id == user_id, Note.is_deleted.is_(False)).offset(skip).limit(limit)
    )
    return result.scalars().all()
```

## 4) API routes (secured)
Create `app/api/notes/routes.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.auth import get_current_user
from app.database.database import get_db
from app.schemas.auth.user import UserResponse
from app.schemas.note import NoteCreate, NoteResponse
from app.crud.core.note import create_note, list_notes_for_user

router = APIRouter(prefix="/notes", tags=["notes"]) 

@router.post("/", response_model=NoteResponse, status_code=201)
async def create_my_note(
    data: NoteCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteResponse:
    note = await create_note(db, user_id=str(current_user.id), data=data)
    return NoteResponse.model_validate(note)

@router.get("/", response_model=list[NoteResponse])
async def list_my_notes(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NoteResponse]:
    notes = await list_notes_for_user(db, user_id=str(current_user.id))
    return [NoteResponse.model_validate(n) for n in notes]
```

Include the router in `app/api/__init__.py`:
```python
from fastapi import APIRouter
from app.core.config import settings
from . import auth, users, system, admin

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(system.router)

# Add notes
from .notes import routes as notes_routes
api_router.include_router(notes_routes.router, prefix=settings.API_V1_STR)
```

## 5) Create the migration
```bash
alembic revision --autogenerate -m "add notes table"
alembic upgrade head
```

## 6) Minimal tests
Create `tests/api/notes/test_notes.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.unit

client = TestClient(app)

def test_unauthorized_list_notes():
    r = client.get("/api/notes")
    assert r.status_code == 401
```

Later, add tests for authorized create/list using a token.

## Notes on security
- These routes require JWT auth via `get_current_user`.
- Keep endpoints under `/api` to inherit stricter cache-control.
- Add API key scopes only for system automation (see `adding-secure-features.md`).
- Validate inputs with Pydantic and return schema objects, not ORM models.

You now have a full feature from DB to API. Add editing/deleting later following the same patterns.

## 🚀 **What You've Accomplished!**

Congratulations! You've successfully built a complete feature following the FastAPI template's proven patterns. Here's what you now have:

### **✅ Complete Feature Stack:**
- **Database Model** - Structured data storage with proper relationships
- **API Schemas** - Input validation and response formatting
- **CRUD Operations** - Create, read, update, delete functionality
- **Secure Endpoints** - JWT-protected routes with proper validation
- **Database Migration** - Schema changes tracked and versioned
- **Basic Tests** - Verification that your feature works correctly

### **🎓 What You've Learned:**
- **FastAPI patterns** - How to structure features consistently
- **Security practices** - JWT authentication, input validation, proper schemas
- **Database design** - Relationships, indexes, and migrations
- **Testing approach** - How to verify your code works
- **Project organization** - Where to put different types of code

### **🔄 Next Steps:**
1. **Test your feature** - Try the endpoints in the `/docs` interface
2. **Add more functionality** - Edit, delete, search, or pagination
3. **Build another feature** - Use the same 6-step pattern
4. **Customize for your needs** - Modify fields, add business logic
5. **Deploy to production** - Follow the deployment tutorial

### **🤖 Continue with AI Assistance:**
Remember, you can always use the AI prompt from the beginning of this tutorial to:
- **Build additional features** - Follow the same pattern
- **Debug issues** - Get help with errors or problems
- **Add advanced functionality** - Pagination, search, bulk operations
- **Optimize performance** - Database queries, caching, monitoring

---

**You're now a FastAPI feature-building pro!** 🎯✨

Keep building, keep learning, and remember: the template + AI assistance + this tutorial = unstoppable development power! 🚀

