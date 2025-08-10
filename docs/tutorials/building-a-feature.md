# Build a Feature (Beginner How-To)

This step-by-step guide shows how to add a new feature to the template: database model → schemas → CRUD → API (with auth) → migrations → basic tests.

We’ll create a simple "Note" feature where authenticated users can create and list their own notes.

## ELI5: How this guide works

Think of adding a feature like adding a new "Notes" room to your house (the app). You do it in small, safe steps:

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

