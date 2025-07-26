#!/usr/bin/env python3
"""
CRUD Scaffolding CLI

Generates complete CRUD boilerplate for FastAPI resources including:
- Model definition
- Pydantic schemas
- CRUD operations
- API endpoints
- Basic tests
- Auto-registration in router

Usage:
    python3 scripts/generate_crud.py Post title:str content:str is_published:bool
    python3 scripts/generate_crud.py Product name:str price:float description:str --soft-delete --searchable
    python3 scripts/generate_crud.py Category name:str slug:str --admin
"""

import argparse
import re
import sys
from pathlib import Path

# Add the project root to the path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after adding to path


class CRUDGenerator:
    """Generates CRUD boilerplate for FastAPI resources."""

    def __init__(
        self, model_name: str, fields: list[tuple[str, str]], options: dict[str, bool]
    ):
        self.model_name = model_name
        self.model_name_lower = model_name.lower()
        self.model_name_plural = self._pluralize(model_name)
        self.fields = fields
        self.options = options

        # Project paths
        self.app_dir = project_root / "app"
        self.models_dir = self.app_dir / "models"
        self.schemas_dir = self.app_dir / "schemas"
        self.crud_dir = self.app_dir / "crud"
        self.endpoints_dir = self.app_dir / "api" / "api_v1" / "endpoints"
        self.tests_dir = project_root / "tests" / "template_tests"

    def _pluralize(self, word: str) -> str:
        """Simple pluralization logic."""
        # Handle words ending in 'y' (change 'y' to 'ies')
        if word.endswith("y"):
            return word[:-1] + "ies"
        # Handle words ending in 's', 'sh', 'ch', 'x', 'z' (add 'es')
        elif (
            word.endswith("s")
            or word.endswith("sh")
            or word.endswith("ch")
            or word.endswith("x")
            or word.endswith("z")
        ):
            return word + "es"
        # Handle words ending in 'f' or 'fe' (change to 'ves')
        elif word.endswith("f"):
            return word[:-1] + "ves"
        elif word.endswith("fe"):
            return word[:-2] + "ves"
        # Default case (add 's')
        else:
            return word + "s"

    def _pluralize_lower(self, word: str) -> str:
        """Pluralize and convert to lowercase for function names."""
        return self._pluralize(word).lower()

    def _get_sqlalchemy_type(self, field_type: str) -> str:
        """Convert Python type to SQLAlchemy type."""
        type_mapping = {
            "str": "String",
            "int": "Integer",
            "float": "Float",
            "bool": "Boolean",
            "datetime": "DateTime",
            "date": "Date",
            "uuid": "UUID(as_uuid=True)",
            "text": "Text",
            "json": "JSON",
        }
        return type_mapping.get(field_type.lower(), "String")

    def _get_pydantic_type(self, field_type: str) -> str:
        """Convert Python type to Pydantic type."""
        type_mapping = {
            "str": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "datetime": "datetime",
            "date": "date",
            "uuid": "uuid.UUID",
            "text": "str",
            "json": "dict",
        }
        return type_mapping.get(field_type.lower(), "str")

    def _get_default_value(self, field_type: str) -> str:
        """Get default value for field type."""
        defaults = {
            "str": '""',
            "int": "0",
            "float": "0.0",
            "bool": "False",
            "datetime": "datetime.utcnow",
            "date": "date.today",
            "uuid": "uuid.uuid4",
            "text": '""',
            "json": "{}",
        }
        return defaults.get(field_type.lower(), '""')

    def generate_model(self) -> str:
        """Generate SQLAlchemy model."""
        imports = [
            "import uuid",
            "from datetime import datetime",
            "",
            "from sqlalchemy import Boolean, Column, DateTime, String, Text",
            "from sqlalchemy.dialects.postgresql import UUID",
            "",
            "from app.database.database import Base",
        ]

        if any(field_type in ["int", "float"] for _, field_type in self.fields):
            imports.append("from sqlalchemy import Integer, Float")

        if any(field_type == "json" for _, field_type in self.fields):
            imports.append("from sqlalchemy import JSON")

        if self.options.get("soft_delete"):
            imports.append("from app.models import SoftDeleteMixin")

        model_class = f"""class {self.model_name}(Base{", SoftDeleteMixin" if self.options.get('soft_delete') else ""}):
    __tablename__ = "{self.model_name_plural.lower()}"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)"""

        # Add fields
        for field_name, field_type in self.fields:
            sql_type = self._get_sqlalchemy_type(field_type)
            nullable = "False" if field_type != "bool" else "True"
            default = (
                self._get_default_value(field_type) if field_type == "bool" else "None"
            )

            if default != "None":
                model_class += f"\n    {field_name} = Column({sql_type}, default={default}, nullable={nullable})"
            else:
                model_class += (
                    f"\n    {field_name} = Column({sql_type}, nullable={nullable})"
                )

        model_class += f"""

    def __repr__(self) -> str:
        return f"<{self.model_name}(id={{self.id}}, {', '.join(f'{name}={{self.{name}}}' for name, _ in self.fields)})>"
"""

        return "\n".join(imports) + "\n\n" + model_class

    def generate_schemas(self) -> str:
        """Generate Pydantic schemas."""
        imports = [
            "import uuid",
            "from datetime import datetime",
            "from typing import Optional",
            "",
            "from pydantic import BaseModel, ConfigDict",
            "from app.utils.pagination import PaginatedResponse",
        ]

        # Base schema
        base_fields = []
        for field_name, field_type in self.fields:
            pydantic_type = self._get_pydantic_type(field_type)
            if field_type == "bool":
                base_fields.append(f"    {field_name}: {pydantic_type} = False")
            else:
                base_fields.append(f"    {field_name}: {pydantic_type}")

        base_schema = f"""class {self.model_name}Base(BaseModel):
{chr(10).join(base_fields)}"""

        # Create schema
        create_fields = []
        for field_name, field_type in self.fields:
            pydantic_type = self._get_pydantic_type(field_type)
            if field_type == "bool":
                create_fields.append(f"    {field_name}: {pydantic_type} = False")
            else:
                create_fields.append(f"    {field_name}: {pydantic_type}")

        create_schema = f"""class {self.model_name}Create({self.model_name}Base):
{chr(10).join(create_fields)}"""

        # Update schema
        update_fields = []
        for field_name, field_type in self.fields:
            pydantic_type = self._get_pydantic_type(field_type)
            update_fields.append(f"    {field_name}: Optional[{pydantic_type}] = None")

        update_schema = f"""class {self.model_name}Update(BaseModel):
{chr(10).join(update_fields)}"""

        # Response schema
        response_fields = [
            "    id: uuid.UUID",
            "    date_created: datetime",
        ]
        for field_name, field_type in self.fields:
            pydantic_type = self._get_pydantic_type(field_type)
            response_fields.append(f"    {field_name}: {pydantic_type}")

        if self.options.get("soft_delete"):
            response_fields.extend(
                [
                    "    is_deleted: bool = False",
                    "    deleted_at: Optional[datetime] = None",
                    "    deleted_by: Optional[uuid.UUID] = None",
                    "    deletion_reason: Optional[str] = None",
                ]
            )

        response_schema = f"""class {self.model_name}Response({self.model_name}Base):
{chr(10).join(response_fields)}

    model_config = ConfigDict(from_attributes=True)"""

        # List response
        list_schema = f"""class {self.model_name}ListResponse(PaginatedResponse[{self.model_name}Response]):
    pass"""

        return "\n\n".join(
            imports
            + [base_schema, create_schema, update_schema, response_schema, list_schema]
        )

    def generate_crud(self) -> str:
        """Generate CRUD operations."""
        imports = [
            "from typing import List, Optional, Union",
            "",
            "from sqlalchemy import select",
            "from sqlalchemy.ext.asyncio import AsyncSession",
            "from sqlalchemy.orm import Session",
            "",
            f"from app.models.{self.model_name_lower} import {self.model_name}",
            f"from app.schemas.{self.model_name_lower} import {self.model_name}Create, {self.model_name}Update",
        ]

        # Type alias
        type_alias = "# Type alias for both sync and async sessions\nDBSession = Union[AsyncSession, Session]\n"

        # CRUD functions
        crud_functions = []

        # Get by ID
        get_by_id = f"""async def get_{self.model_name_lower}_by_id(db: DBSession, {self.model_name_lower}_id: str) -> Optional[{self.model_name}]:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select({self.model_name}).filter({self.model_name}.id == {self.model_name_lower}_id{f", {self.model_name}.is_deleted.is_(False)" if self.options.get('soft_delete') else ""})
        )
    else:
        result = db.execute(
            select({self.model_name}).filter({self.model_name}.id == {self.model_name_lower}_id{f", {self.model_name}.is_deleted.is_(False)" if self.options.get('soft_delete') else ""})
        )
    return result.scalar_one_or_none()"""
        crud_functions.append(get_by_id)

        # Create
        create = f"""async def create_{self.model_name_lower}(db: DBSession, obj: {self.model_name}Create) -> {self.model_name}:
    db_obj = {self.model_name}(**obj.dict())
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
    return db_obj"""
        crud_functions.append(create)

        # Update
        update = f"""async def update_{self.model_name_lower}(db: DBSession, {self.model_name_lower}_id: str, obj: {self.model_name}Update) -> Optional[{self.model_name}]:
    db_obj = await get_{self.model_name_lower}_by_id(db, {self.model_name_lower}_id)
    if not db_obj:
        return None

    update_data = obj.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

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
    return db_obj"""
        crud_functions.append(update)

        # Delete
        if self.options.get("soft_delete"):
            delete = f"""async def soft_delete_{self.model_name_lower}(db: DBSession, {self.model_name_lower}_id: str, deleted_by: str = None, reason: str = None) -> bool:
    db_obj = await get_{self.model_name_lower}_by_id(db, {self.model_name_lower}_id)
    if not db_obj:
        return False

    db_obj.soft_delete(deleted_by=deleted_by, reason=reason)

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()
    return True"""
        else:
            delete = f"""async def delete_{self.model_name_lower}(db: DBSession, {self.model_name_lower}_id: str) -> bool:
    db_obj = await get_{self.model_name_lower}_by_id(db, {self.model_name_lower}_id)
    if not db_obj:
        return False

    if isinstance(db, AsyncSession):
        await db.delete(db_obj)
        await db.commit()
    else:
        db.delete(db_obj)
        db.commit()
    return True"""
        crud_functions.append(delete)

        # List
        list_func = f"""async def get_{self._pluralize_lower(self.model_name)}(db: DBSession, skip: int = 0, limit: int = 100) -> List[{self.model_name}]:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select({self.model_name})
            .offset(skip)
            .limit(limit)
            {f".filter({self.model_name}.is_deleted.is_(False))" if self.options.get('soft_delete') else ""}
        )
    else:
        result = db.execute(
            select({self.model_name})
            .offset(skip)
            .limit(limit)
            {f".filter({self.model_name}.is_deleted.is_(False))" if self.options.get('soft_delete') else ""}
        )
    return result.scalars().all()"""
        crud_functions.append(list_func)

        # Count
        count_func = f"""async def count_{self._pluralize_lower(self.model_name)}(db: DBSession) -> int:
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select({self.model_name})
            {f".filter({self.model_name}.is_deleted.is_(False))" if self.options.get('soft_delete') else ""}
        )
    else:
        result = db.execute(
            select({self.model_name})
            {f".filter({self.model_name}.is_deleted.is_(False))" if self.options.get('soft_delete') else ""}
        )
    return len(result.scalars().all())"""
        crud_functions.append(count_func)

        return "\n\n".join(imports + [type_alias] + crud_functions)

    def generate_endpoints(self) -> str:
        """Generate API endpoints."""
        imports = [
            "from typing import List",
            "",
            "from fastapi import APIRouter, Depends, HTTPException, status",
            "from sqlalchemy.orm import Session",
            "",
            f"from app.crud import {self.model_name_lower} as crud_{self.model_name_lower}",
            "from app.database.database import get_db",
            f"from app.schemas.{self.model_name_lower} import {self.model_name}Create, {self.model_name}Update, {self.model_name}Response, {self.model_name}ListResponse",
            "from app.utils.pagination import PaginationParams",
        ]

        if self.options.get("searchable"):
            imports.extend(
                [
                    f"from app.utils.search_filter import {self.model_name}SearchParams",
                ]
            )

        router = """router = APIRouter()"""

        # List endpoint
        list_endpoint = f"""@router.get("", response_model={self.model_name}ListResponse)
async def list_{self._pluralize_lower(self.model_name)}(
    pagination: PaginationParams = Depends(),"""

        if self.options.get("searchable"):
            list_endpoint += f"""
    search_params: {self.model_name}SearchParams = Depends(),"""

        list_endpoint += f"""
    db: Session = Depends(get_db),
) -> {self.model_name}ListResponse:
    \"\"\"
    List {self.model_name_plural} with pagination.
    \"\"\"
    {self._pluralize_lower(self.model_name)} = await crud_{self.model_name_lower}.get_{self._pluralize_lower(self.model_name)}(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    total = await crud_{self.model_name_lower}.count_{self._pluralize_lower(self.model_name)}(db=db)

    return {self.model_name}ListResponse(
        items={self._pluralize_lower(self.model_name)},
        total=total,
        page=pagination.page,
        per_page=pagination.limit,
        total_pages=(total + pagination.limit - 1) // pagination.limit,
    )"""

        # Get by ID endpoint
        get_endpoint = f"""@router.get("/{{{self.model_name_lower}_id}}", response_model={self.model_name}Response)
async def get_{self.model_name_lower}(
    {self.model_name_lower}_id: str,
    db: Session = Depends(get_db),
) -> {self.model_name}Response:
    \"\"\"
    Get a {self.model_name_lower} by ID.
    \"\"\"
    {self.model_name_lower} = await crud_{self.model_name_lower}.get_{self.model_name_lower}_by_id(db, {self.model_name_lower}_id)
    if not {self.model_name_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{self.model_name} not found"
        )
    return {self.model_name_lower}"""

        # Create endpoint
        create_endpoint = f"""@router.post("", response_model={self.model_name}Response, status_code=status.HTTP_201_CREATED)
async def create_{self.model_name_lower}(
    obj: {self.model_name}Create,
    db: Session = Depends(get_db),
) -> {self.model_name}Response:
    \"\"\"
    Create a new {self.model_name_lower}.
    \"\"\"
    return await crud_{self.model_name_lower}.create_{self.model_name_lower}(db, obj)"""

        # Update endpoint
        update_endpoint = f"""@router.put("/{{{self.model_name_lower}_id}}", response_model={self.model_name}Response)
async def update_{self.model_name_lower}(
    {self.model_name_lower}_id: str,
    obj: {self.model_name}Update,
    db: Session = Depends(get_db),
) -> {self.model_name}Response:
    \"\"\"
    Update a {self.model_name_lower}.
    \"\"\"
    {self.model_name_lower} = await crud_{self.model_name_lower}.update_{self.model_name_lower}(db, {self.model_name_lower}_id, obj)
    if not {self.model_name_lower}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{self.model_name} not found"
        )
    return {self.model_name_lower}"""

        # Delete endpoint
        if self.options.get("soft_delete"):
            delete_endpoint = f"""@router.delete("/{{{self.model_name_lower}_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_{self.model_name_lower}(
    {self.model_name_lower}_id: str,
    db: Session = Depends(get_db),
) -> None:
    \"\"\"
    Soft delete a {self.model_name_lower}.
    \"\"\"
    success = await crud_{self.model_name_lower}.soft_delete_{self.model_name_lower}(db, {self.model_name_lower}_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{self.model_name} not found"
        )"""
        else:
            delete_endpoint = f"""@router.delete("/{{{self.model_name_lower}_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{self.model_name_lower}(
    {self.model_name_lower}_id: str,
    db: Session = Depends(get_db),
) -> None:
    \"\"\"
    Delete a {self.model_name_lower}.
    \"\"\"
    success = await crud_{self.model_name_lower}.delete_{self.model_name_lower}(db, {self.model_name_lower}_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{self.model_name} not found"
        )"""

        return "\n\n".join(
            imports
            + [
                router,
                list_endpoint,
                get_endpoint,
                create_endpoint,
                update_endpoint,
                delete_endpoint,
            ]
        )

    def generate_tests(self) -> str:
        """Generate basic tests."""
        imports = [
            "import uuid",
            "from datetime import datetime",
            "",
            "import pytest",
            "from fastapi.testclient import TestClient",
            "from sqlalchemy.orm import Session",
            "",
            f"from app.models.{self.model_name_lower} import {self.model_name}",
            f"from app.schemas.{self.model_name_lower} import {self.model_name}Create",
        ]

        # Test data
        test_data = f"""# Test data
test_{self.model_name_lower}_data = {{
"""
        for field_name, field_type in self.fields:
            if field_type == "str":
                test_data += f'    "{field_name}": "Test {field_name}",\n'
            elif field_type == "int":
                test_data += f'    "{field_name}": 42,\n'
            elif field_type == "float":
                test_data += f'    "{field_name}": 42.0,\n'
            elif field_type == "bool":
                test_data += f'    "{field_name}": True,\n'
            elif field_type == "datetime":
                test_data += f'    "{field_name}": datetime.utcnow(),\n'
            else:
                test_data += f'    "{field_name}": "test_value",\n'
        test_data += "}"

        # Test functions
        test_functions = []

        # Test create
        test_create = f"""def test_create_{self.model_name_lower}(client: TestClient, db: Session):
    \"\"\"Test creating a {self.model_name_lower}.\"\"\"
    response = client.post(f"/api/v1/{self.model_name_plural}", json=test_{self.model_name_lower}_data)
    assert response.status_code == 201
    data = response.json()
    assert data["{self.fields[0][0]}"] == test_{self.model_name_lower}_data["{self.fields[0][0]}"]
    assert "id" in data"""

        # Test get
        test_get = f"""def test_get_{self.model_name_lower}(client: TestClient, db: Session):
    \"\"\"Test getting a {self.model_name_lower} by ID.\"\"\"
    # First create a {self.model_name_lower}
    create_response = client.post(f"/api/v1/{self.model_name_plural}", json=test_{self.model_name_lower}_data)
    assert create_response.status_code == 201
    {self.model_name_lower}_id = create_response.json()["id"]

    # Then get it
    response = client.get(f"/api/v1/{self.model_name_plural}/{{{self.model_name_lower}_id}}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == {self.model_name_lower}_id"""

        # Test list
        test_list = f"""def test_list_{self._pluralize_lower(self.model_name)}(client: TestClient, db: Session):
    \"\"\"Test listing {self.model_name_plural}.\"\"\"
    # Create a {self.model_name_lower}
    client.post(f"/api/v1/{self.model_name_plural}", json=test_{self.model_name_lower}_data)

    # List {self.model_name_plural}
    response = client.get(f"/api/v1/{self.model_name_plural}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data"""

        # Test update
        test_update = f"""def test_update_{self.model_name_lower}(client: TestClient, db: Session):
    \"\"\"Test updating a {self.model_name_lower}.\"\"\"
    # First create a {self.model_name_lower}
    create_response = client.post(f"/api/v1/{self.model_name_plural}", json=test_{self.model_name_lower}_data)
    assert create_response.status_code == 201
    {self.model_name_lower}_id = create_response.json()["id"]

    # Update it
    update_data = {{**test_{self.model_name_lower}_data, "{self.fields[0][0]}": "Updated {self.fields[0][0]}"}}
    response = client.put(f"/api/v1/{self.model_name_plural}/{{{self.model_name_lower}_id}}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["{self.fields[0][0]}"] == "Updated {self.fields[0][0]}" """

        # Test delete
        if self.options.get("soft_delete"):
            test_delete = f"""def test_soft_delete_{self.model_name_lower}(client: TestClient, db: Session):
    \"\"\"Test soft deleting a {self.model_name_lower}.\"\"\"
    # First create a {self.model_name_lower}
    create_response = client.post(f"/api/v1/{self.model_name_plural}", json=test_{self.model_name_lower}_data)
    assert create_response.status_code == 201
    {self.model_name_lower}_id = create_response.json()["id"]

    # Soft delete it
    response = client.delete(f"/api/v1/{self.model_name_plural}/{{{self.model_name_lower}_id}}")
    assert response.status_code == 204"""
        else:
            test_delete = f"""def test_delete_{self.model_name_lower}(client: TestClient, db: Session):
    \"\"\"Test deleting a {self.model_name_lower}.\"\"\"
    # First create a {self.model_name_lower}
    create_response = client.post(f"/api/v1/{self.model_name_plural}", json=test_{self.model_name_lower}_data)
    assert create_response.status_code == 201
    {self.model_name_lower}_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/v1/{self.model_name_plural}/{{{self.model_name_lower}_id}}")
    assert response.status_code == 204"""

        test_functions.extend(
            [test_create, test_get, test_list, test_update, test_delete]
        )

        return "\n\n".join(imports + [test_data] + test_functions)

    def update_api_router(self):
        """Update the API router to include the new endpoints."""
        api_file = self.app_dir / "api" / "api_v1" / "api.py"

        if not api_file.exists():
            print(f"Warning: API router file not found at {api_file}")
            return

        with open(api_file) as f:
            content = f.read()

        # Add import
        import_pattern = r"from app\.api\.api_v1\.endpoints import (.+)"
        match = re.search(import_pattern, content)
        if match:
            current_imports = match.group(1)
            if self.model_name_lower not in current_imports:
                new_imports = current_imports + f", {self.model_name_lower}"
                content = re.sub(
                    import_pattern,
                    f"from app.api.api_v1.endpoints import {new_imports}",
                    content,
                )

        # Add router include
        include_pattern = r"api_router\.include_router\((.+)\.router, prefix=\"/(.+)\", tags=\[\"(.+)\"\]\)"
        match = re.search(include_pattern, content)
        if match:
            # Add after the last include_router call
            new_include = f'    api_router.include_router({self.model_name_lower}.router, prefix="/{self.model_name_plural}", tags=["{self.model_name_lower}"])'
            content = content.replace(
                match.group(0), match.group(0) + "\n" + new_include
            )

        with open(api_file, "w") as f:
            f.write(content)

    def create_files(self):
        """Create all the generated files."""
        # Create model file
        model_file = self.models_dir / f"{self.model_name_lower}.py"
        with open(model_file, "w") as f:
            f.write(self.generate_model())
        print(f"✅ Created model: {model_file}")

        # Create schema file
        schema_file = self.schemas_dir / f"{self.model_name_lower}.py"
        with open(schema_file, "w") as f:
            f.write(self.generate_schemas())
        print(f"✅ Created schemas: {schema_file}")

        # Create CRUD file
        crud_file = self.crud_dir / f"{self.model_name_lower}.py"
        with open(crud_file, "w") as f:
            f.write(self.generate_crud())
        print(f"✅ Created CRUD: {crud_file}")

        # Create endpoints file
        endpoint_file = self.endpoints_dir / f"{self.model_name_lower}.py"
        with open(endpoint_file, "w") as f:
            f.write(self.generate_endpoints())
        print(f"✅ Created endpoints: {endpoint_file}")

        # Create test file
        test_file = self.tests_dir / f"test_{self.model_name_lower}.py"
        with open(test_file, "w") as f:
            f.write(self.generate_tests())
        print(f"✅ Created tests: {test_file}")

        # Update API router
        self.update_api_router()
        print("✅ Updated API router")

        # Update models __init__.py
        self._update_models_init()

    def _update_models_init(self):
        """Update models __init__.py to import the new model."""
        init_file = self.models_dir / "__init__.py"

        if not init_file.exists():
            with open(init_file, "w") as f:
                f.write(f"from .{self.model_name_lower} import {self.model_name}\n")
        else:
            with open(init_file) as f:
                content = f.read()

            if f"from .{self.model_name_lower} import {self.model_name}" not in content:
                with open(init_file, "a") as f:
                    f.write(
                        f"\nfrom .{self.model_name_lower} import {self.model_name}\n"
                    )

        print("✅ Updated models __init__.py")


def parse_field_spec(field_spec: str) -> tuple[str, str]:
    """Parse field specification like 'name:str' into (name, type)."""
    if ":" not in field_spec:
        raise ValueError(
            f"Invalid field specification: {field_spec}. Use format 'name:type'"
        )

    name, field_type = field_spec.split(":", 1)
    name = name.strip()
    field_type = field_type.strip()

    # Validate that both name and type are not empty
    if not name or not field_type:
        raise ValueError(
            f"Invalid field specification: {field_spec}. Both name and type must be provided"
        )

    return name, field_type


def main():
    parser = argparse.ArgumentParser(
        description="Generate CRUD boilerplate for FastAPI resources"
    )
    parser.add_argument("model_name", help="Name of the model (e.g., Post, Product)")
    parser.add_argument(
        "fields",
        nargs="+",
        help="Field specifications (e.g., title:str content:str is_published:bool)",
    )
    parser.add_argument(
        "--soft-delete", action="store_true", help="Include soft delete functionality"
    )
    parser.add_argument(
        "--searchable", action="store_true", help="Include search functionality"
    )
    parser.add_argument(
        "--admin", action="store_true", help="Include admin functionality"
    )
    parser.add_argument("--slug", action="store_true", help="Include slug field")

    args = parser.parse_args()

    # Parse fields
    try:
        fields = [parse_field_spec(field) for field in args.fields]
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Add slug field if requested
    if args.slug:
        fields.append(("slug", "str"))

    # Create options dict
    options = {
        "soft_delete": args.soft_delete,
        "searchable": args.searchable,
        "admin": args.admin,
    }

    # Generate CRUD
    generator = CRUDGenerator(args.model_name, fields, options)

    print(f"🚀 Generating CRUD for {args.model_name}...")
    print(f"📝 Fields: {', '.join(f'{name}:{type}' for name, type in fields)}")
    print(f"⚙️  Options: {', '.join(k for k, v in options.items() if v)}")
    print()

    try:
        generator.create_files()
        print()
        print("🎉 CRUD generation complete!")
        print()
        print("📋 Next steps:")
        print(
            f"1. Review the generated files in app/models/{args.model_name.lower()}.py"
        )
        print(
            f"2. Run database migrations: alembic revision --autogenerate -m 'Add {args.model_name} model'"
        )
        print("3. Apply migrations: alembic upgrade head")
        print(
            f"4. Test the endpoints: pytest tests/template_tests/test_{args.model_name.lower()}.py"
        )
        print()
        print("🔗 API endpoints available at:")
        print(f"   GET    /api/v1/{generator.model_name_plural}")
        print(f"   POST   /api/v1/{generator.model_name_plural}")
        print(f"   GET    /api/v1/{generator.model_name_plural}/{{id}}")
        print(f"   PUT    /api/v1/{generator.model_name_plural}/{{id}}")
        print(f"   DELETE /api/v1/{generator.model_name_plural}/{{id}}")

    except Exception as e:
        print(f"❌ Error generating CRUD: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
