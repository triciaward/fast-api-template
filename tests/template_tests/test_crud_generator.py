"""
Unit tests for the CRUD scaffolding CLI.

Tests the generate_crud.py script to ensure it generates correct boilerplate code
and handles various input scenarios properly.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCRUDGenerator:
    """Test the CRUDGenerator class."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        project_structure = {
            "app": {
                "models": {},
                "schemas": {},
                "crud": {},
                "api": {"api_v1": {"endpoints": {}}},
            },
            "tests": {"template_tests": {}},
        }

        def create_structure(base_path, structure):
            for name, content in structure.items():
                path = Path(base_path) / name
                if isinstance(content, dict):
                    path.mkdir(exist_ok=True)
                    create_structure(path, content)
                else:
                    path.touch()

        create_structure(temp_dir, project_structure)
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_pluralize_logic(self):
        """Test the pluralization logic."""
        # Mock the CRUDGenerator class to test just the pluralize method
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            # Create a minimal generator instance
            fields = [("title", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            # Mock the imports
            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                # Test pluralization
                assert generator._pluralize("Post") == "Posts"
                assert generator._pluralize("Category") == "Categories"
                assert generator._pluralize("User") == "Users"
                assert generator._pluralize("Box") == "Boxes"
                assert generator._pluralize("City") == "Cities"

    def test_type_mapping(self):
        """Test type mapping functions."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                # Test SQLAlchemy type mapping
                assert generator._get_sqlalchemy_type("str") == "String"
                assert generator._get_sqlalchemy_type("int") == "Integer"
                assert generator._get_sqlalchemy_type("float") == "Float"
                assert generator._get_sqlalchemy_type("bool") == "Boolean"
                assert generator._get_sqlalchemy_type("datetime") == "DateTime"
                assert generator._get_sqlalchemy_type("date") == "Date"
                assert generator._get_sqlalchemy_type("uuid") == "UUID(as_uuid=True)"
                assert generator._get_sqlalchemy_type("text") == "Text"
                assert generator._get_sqlalchemy_type("json") == "JSON"
                assert generator._get_sqlalchemy_type("unknown") == "String"  # Default

                # Test Pydantic type mapping
                assert generator._get_pydantic_type("str") == "str"
                assert generator._get_pydantic_type("int") == "int"
                assert generator._get_pydantic_type("float") == "float"
                assert generator._get_pydantic_type("bool") == "bool"
                assert generator._get_pydantic_type("datetime") == "datetime"
                assert generator._get_pydantic_type("date") == "date"
                assert generator._get_pydantic_type("uuid") == "uuid.UUID"
                assert generator._get_pydantic_type("text") == "str"
                assert generator._get_pydantic_type("json") == "dict"
                assert generator._get_pydantic_type("unknown") == "str"  # Default

                # Test default value mapping
                assert generator._get_default_value("str") == '""'
                assert generator._get_default_value("int") == "0"
                assert generator._get_default_value("float") == "0.0"
                assert generator._get_default_value("bool") == "False"
                assert generator._get_default_value("datetime") == "datetime.utcnow"
                assert generator._get_default_value("date") == "date.today"
                assert generator._get_default_value("uuid") == "uuid.uuid4"
                assert generator._get_default_value("text") == '""'
                assert generator._get_default_value("json") == "{}"
                assert generator._get_default_value("unknown") == '""'  # Default

    def test_model_generation(self):
        """Test model generation."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str"), ("is_published", "bool")]
            options = {"soft_delete": True, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                model_code = generator.generate_model()

                # Check imports
                assert "import uuid" in model_code
                assert "from datetime import datetime" in model_code
                assert (
                    "from sqlalchemy import Boolean, Column, DateTime, String"
                    in model_code
                )
                assert "from sqlalchemy.dialects.postgresql import UUID" in model_code
                assert "from app.database.database import Base" in model_code
                assert "from app.models.models import SoftDeleteMixin" in model_code

                # Check class definition
                assert "class Post(Base, SoftDeleteMixin):" in model_code
                assert '__tablename__ = "posts"' in model_code

                # Check fields
                assert (
                    "id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)"
                    in model_code
                )
                assert (
                    "date_created = Column(DateTime, default=datetime.utcnow, nullable=False)"
                    in model_code
                )
                assert "title = Column(String, nullable=False)" in model_code
                assert "content = Column(String, nullable=False)" in model_code
                assert (
                    "is_published = Column(Boolean, default=False, nullable=True)"
                    in model_code
                )

                # Check repr method
                assert "def __repr__(self) -> str:" in model_code
                assert (
                    'return f"<Post(id={self.id}, title={self.title}, content={self.content}, is_published={self.is_published})>"'
                    in model_code
                )

    def test_model_generation_without_soft_delete(self):
        """Test model generation without soft delete."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                model_code = generator.generate_model()

                # Should not include SoftDeleteMixin
                assert "SoftDeleteMixin" not in model_code
                assert "class Post(Base):" in model_code

    def test_schema_generation(self):
        """Test schema generation."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str"), ("is_published", "bool")]
            options = {"soft_delete": True, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                schema_code = generator.generate_schemas()

                # Check imports
                assert "import uuid" in schema_code
                assert "from datetime import datetime" in schema_code
                assert "from typing import Optional" in schema_code
                assert "from pydantic import BaseModel, ConfigDict" in schema_code
                assert (
                    "from app.utils.pagination import PaginatedResponse" in schema_code
                )

                # Check base schema
                assert "class PostBase(BaseModel):" in schema_code
                assert "title: str" in schema_code
                assert "content: str" in schema_code
                assert "is_published: bool = False" in schema_code

                # Check create schema
                assert "class PostCreate(PostBase):" in schema_code

                # Check update schema
                assert "class PostUpdate(BaseModel):" in schema_code
                assert "title: Optional[str] = None" in schema_code
                assert "content: Optional[str] = None" in schema_code
                assert "is_published: Optional[bool] = None" in schema_code

                # Check response schema
                assert "class PostResponse(PostBase):" in schema_code
                assert "id: uuid.UUID" in schema_code
                assert "date_created: datetime" in schema_code
                assert "is_deleted: bool = False" in schema_code
                assert "deleted_at: Optional[datetime] = None" in schema_code
                assert "deleted_by: Optional[uuid.UUID] = None" in schema_code
                assert "deletion_reason: Optional[str] = None" in schema_code
                assert "model_config = ConfigDict(from_attributes=True)" in schema_code

                # Check list response
                assert (
                    "class PostListResponse(PaginatedResponse[PostResponse]):"
                    in schema_code
                )
                assert "pass" in schema_code

    def test_schema_generation_without_soft_delete(self):
        """Test schema generation without soft delete."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                schema_code = generator.generate_schemas()

                # Should not include soft delete fields
                assert "is_deleted" not in schema_code
                assert "deleted_at" not in schema_code
                assert "deleted_by" not in schema_code
                assert "deletion_reason" not in schema_code

    def test_crud_generation(self):
        """Test CRUD generation."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str"), ("is_published", "bool")]
            options = {"soft_delete": True, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                crud_code = generator.generate_crud()

                # Check imports
                assert "from typing import List, Optional, Union" in crud_code
                assert "from sqlalchemy import select" in crud_code
                assert "from sqlalchemy.ext.asyncio import AsyncSession" in crud_code
                assert "from sqlalchemy.orm import Session" in crud_code
                assert "from app.models.post import Post" in crud_code
                assert (
                    "from app.schemas.post import PostCreate, PostUpdate" in crud_code
                )

                # Check type alias
                assert "DBSession = Union[AsyncSession, Session]" in crud_code

                # Check CRUD functions
                assert (
                    "async def get_post_by_id(db: DBSession, post_id: str) -> Optional[Post]:"
                    in crud_code
                )
                assert (
                    "async def create_post(db: DBSession, obj: PostCreate) -> Post:"
                    in crud_code
                )
                assert (
                    "async def update_post(db: DBSession, post_id: str, obj: PostUpdate) -> Optional[Post]:"
                    in crud_code
                )
                assert (
                    "async def soft_delete_post(db: DBSession, post_id: str, deleted_by: str = None, reason: str = None) -> bool:"
                    in crud_code
                )
                assert (
                    "async def get_posts(db: DBSession, skip: int = 0, limit: int = 100) -> List[Post]:"
                    in crud_code
                )
                assert "async def count_posts(db: DBSession) -> int:" in crud_code

                # Check soft delete filtering
                assert "Post.is_deleted.is_(False)" in crud_code

    def test_crud_generation_without_soft_delete(self):
        """Test CRUD generation without soft delete."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                crud_code = generator.generate_crud()

                # Should use hard delete instead of soft delete
                assert (
                    "async def delete_post(db: DBSession, post_id: str) -> bool:"
                    in crud_code
                )
                assert "await db.delete(db_obj)" in crud_code
                assert "db.delete(db_obj)" in crud_code
                assert "Post.is_deleted.is_(False)" not in crud_code

    def test_endpoint_generation(self):
        """Test endpoint generation."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str"), ("is_published", "bool")]
            options = {"soft_delete": True, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                endpoint_code = generator.generate_endpoints()

                # Check imports
                assert "from typing import List" in endpoint_code
                assert (
                    "from fastapi import APIRouter, Depends, HTTPException, status"
                    in endpoint_code
                )
                assert "from sqlalchemy.orm import Session" in endpoint_code
                assert "from app.crud import post as crud_post" in endpoint_code
                assert "from app.database.database import get_db" in endpoint_code
                assert (
                    "from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostListResponse"
                    in endpoint_code
                )
                assert (
                    "from app.utils.pagination import PaginationParams" in endpoint_code
                )

                # Check router
                assert "router = APIRouter()" in endpoint_code

                # Check endpoints
                assert (
                    '@router.get("", response_model=PostListResponse)' in endpoint_code
                )
                assert "async def list_posts(" in endpoint_code
                assert (
                    '@router.get("/{post_id}", response_model=PostResponse)'
                    in endpoint_code
                )
                assert "async def get_post(" in endpoint_code
                assert (
                    '@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)'
                    in endpoint_code
                )
                assert "async def create_post(" in endpoint_code
                assert (
                    '@router.put("/{post_id}", response_model=PostResponse)'
                    in endpoint_code
                )
                assert "async def update_post(" in endpoint_code
                assert (
                    '@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)'
                    in endpoint_code
                )
                assert "async def soft_delete_post(" in endpoint_code

    def test_endpoint_generation_without_soft_delete(self):
        """Test endpoint generation without soft delete."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                endpoint_code = generator.generate_endpoints()

                # Should use hard delete instead of soft delete
                assert "async def delete_post(" in endpoint_code
                assert "soft_delete_post" not in endpoint_code

    def test_test_generation(self):
        """Test test generation."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str"), ("is_published", "bool")]
            options = {"soft_delete": True, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                test_code = generator.generate_tests()

                # Check imports
                assert "import uuid" in test_code
                assert "from datetime import datetime" in test_code
                assert "import pytest" in test_code
                assert "from fastapi.testclient import TestClient" in test_code
                assert "from sqlalchemy.orm import Session" in test_code
                assert "from app.models.post import Post" in test_code
                assert "from app.schemas.post import PostCreate" in test_code

                # Check test data
                assert "test_post_data = {" in test_code
                assert '"title": "Test title"' in test_code
                assert '"content": "Test content"' in test_code
                assert '"is_published": True' in test_code

                # Check test functions
                assert (
                    "def test_create_post(client: TestClient, db: Session):"
                    in test_code
                )
                assert (
                    "def test_get_post(client: TestClient, db: Session):" in test_code
                )
                assert (
                    "def test_list_posts(client: TestClient, db: Session):" in test_code
                )
                assert (
                    "def test_update_post(client: TestClient, db: Session):"
                    in test_code
                )
                assert (
                    "def test_soft_delete_post(client: TestClient, db: Session):"
                    in test_code
                )

    def test_test_generation_without_soft_delete(self):
        """Test test generation without soft delete."""
        with patch("scripts.generate_crud.project_root", Path("/tmp")):
            fields = [("title", "str"), ("content", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                test_code = generator.generate_tests()

                # Should use hard delete instead of soft delete
                assert (
                    "def test_delete_post(client: TestClient, db: Session):"
                    in test_code
                )
                assert "test_soft_delete_post" not in test_code

    def test_file_creation(self, temp_project_dir):
        """Test file creation."""
        with patch("scripts.generate_crud.project_root", Path(temp_project_dir)):
            fields = [("title", "str"), ("content", "str")]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                # Mock the update methods
                with patch.object(
                    generator, "update_api_router"
                ) as mock_update_router, patch.object(
                    generator, "_update_models_init"
                ) as mock_update_init:

                    generator.create_files()

                    # Check that files were created
                    model_file = Path(temp_project_dir) / "app" / "models" / "post.py"
                    schema_file = Path(temp_project_dir) / "app" / "schemas" / "post.py"
                    crud_file = Path(temp_project_dir) / "app" / "crud" / "post.py"
                    endpoint_file = (
                        Path(temp_project_dir)
                        / "app"
                        / "api"
                        / "api_v1"
                        / "endpoints"
                        / "post.py"
                    )
                    test_file = (
                        Path(temp_project_dir)
                        / "tests"
                        / "template_tests"
                        / "test_post.py"
                    )

                    assert model_file.exists()
                    assert schema_file.exists()
                    assert crud_file.exists()
                    assert endpoint_file.exists()
                    assert test_file.exists()

                    # Check that update methods were called
                    mock_update_router.assert_called_once()
                    mock_update_init.assert_called_once()


class TestParseFieldSpec:
    """Test the parse_field_spec function."""

    def test_valid_field_spec(self):
        """Test parsing valid field specifications."""
        with patch.dict(
            "sys.modules",
            {
                "app.core.config": MagicMock(),
                "app.database.database": MagicMock(),
                "app.models.models": MagicMock(),
                "app.utils.pagination": MagicMock(),
            },
        ):
            from scripts.generate_crud import parse_field_spec

            assert parse_field_spec("title:str") == ("title", "str")
            assert parse_field_spec("content:text") == ("content", "text")
            assert parse_field_spec("is_published:bool") == ("is_published", "bool")
            assert parse_field_spec("price:float") == ("price", "float")
            assert parse_field_spec("count:int") == ("count", "int")

    def test_invalid_field_spec(self):
        """Test parsing invalid field specifications."""
        with patch.dict(
            "sys.modules",
            {
                "app.core.config": MagicMock(),
                "app.database.database": MagicMock(),
                "app.models.models": MagicMock(),
                "app.utils.pagination": MagicMock(),
            },
        ):
            from scripts.generate_crud import parse_field_spec

            with pytest.raises(ValueError, match="Invalid field specification"):
                parse_field_spec("title")

            with pytest.raises(ValueError, match="Invalid field specification"):
                parse_field_spec("title:")

            with pytest.raises(ValueError, match="Invalid field specification"):
                parse_field_spec(":str")

    def test_field_spec_with_spaces(self):
        """Test parsing field specifications with spaces."""
        with patch.dict(
            "sys.modules",
            {
                "app.core.config": MagicMock(),
                "app.database.database": MagicMock(),
                "app.models.models": MagicMock(),
                "app.utils.pagination": MagicMock(),
            },
        ):
            from scripts.generate_crud import parse_field_spec

            assert parse_field_spec(" title : str ") == ("title", "str")
            assert parse_field_spec("  content  :  text  ") == ("content", "text")


class TestCRUDGeneratorIntegration:
    """Integration tests for the CRUD generator."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        project_structure = {
            "app": {
                "models": {"__init__.py": ""},
                "schemas": {},
                "crud": {},
                "api": {"api_v1": {"endpoints": {}}},
            },
            "tests": {"template_tests": {}},
        }

        def create_structure(base_path, structure):
            for name, content in structure.items():
                path = Path(base_path) / name
                if isinstance(content, dict):
                    path.mkdir(exist_ok=True)
                    create_structure(path, content)
                else:
                    path.touch()

        create_structure(temp_dir, project_structure)
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_complete_generation_workflow(self, temp_project_dir):
        """Test the complete generation workflow."""
        with patch("scripts.generate_crud.project_root", Path(temp_project_dir)):
            fields = [("title", "str"), ("content", "text"), ("is_published", "bool")]
            options = {"soft_delete": True, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Post", fields, options)

                # Generate all files
                generator.create_files()

                # Verify all files exist and have correct content
                model_file = Path(temp_project_dir) / "app" / "models" / "post.py"
                schema_file = Path(temp_project_dir) / "app" / "schemas" / "post.py"
                crud_file = Path(temp_project_dir) / "app" / "crud" / "post.py"
                endpoint_file = (
                    Path(temp_project_dir)
                    / "app"
                    / "api"
                    / "api_v1"
                    / "endpoints"
                    / "post.py"
                )
                test_file = (
                    Path(temp_project_dir) / "tests" / "template_tests" / "test_post.py"
                )

                assert model_file.exists()
                assert schema_file.exists()
                assert crud_file.exists()
                assert endpoint_file.exists()
                assert test_file.exists()

                # Check model content
                model_content = model_file.read_text()
                assert "class Post(Base, SoftDeleteMixin):" in model_content
                # text type should use Text
                assert "content = Column(Text, nullable=False)" in model_content

                # Check schema content
                schema_content = schema_file.read_text()
                assert "class PostCreate(PostBase):" in schema_content
                assert "class PostResponse(PostBase):" in schema_content

                # Check CRUD content
                crud_content = crud_file.read_text()
                assert "async def create_post(" in crud_content
                assert "async def soft_delete_post(" in crud_content

                # Check endpoint content
                endpoint_content = endpoint_file.read_text()
                assert "async def create_post(" in endpoint_content
                assert "async def soft_delete_post(" in endpoint_content

                # Check test content
                test_content = test_file.read_text()
                assert "def test_create_post(" in test_content
                assert "def test_soft_delete_post(" in test_content

    def test_different_field_types(self, temp_project_dir):
        """Test generation with different field types."""
        with patch("scripts.generate_crud.project_root", Path(temp_project_dir)):
            fields = [
                ("name", "str"),
                ("age", "int"),
                ("height", "float"),
                ("is_active", "bool"),
                ("birth_date", "date"),
                ("created_at", "datetime"),
                ("user_id", "uuid"),
                ("description", "text"),
                ("metadata", "json"),
            ]
            options = {"soft_delete": False, "searchable": False, "admin": False}

            with patch.dict(
                "sys.modules",
                {
                    "app.core.config": MagicMock(),
                    "app.database.database": MagicMock(),
                    "app.models.models": MagicMock(),
                    "app.utils.pagination": MagicMock(),
                },
            ):
                from scripts.generate_crud import CRUDGenerator

                generator = CRUDGenerator("Person", fields, options)

                # Generate model
                model_code = generator.generate_model()

                # Check that all field types are properly mapped
                assert "name = Column(String, nullable=False)" in model_code
                assert "age = Column(Integer, nullable=False)" in model_code
                assert "height = Column(Float, nullable=False)" in model_code
                assert (
                    "is_active = Column(Boolean, default=False, nullable=True)"
                    in model_code
                )
                assert "birth_date = Column(Date, nullable=False)" in model_code
                assert "created_at = Column(DateTime, nullable=False)" in model_code
                assert (
                    "user_id = Column(UUID(as_uuid=True), nullable=False)" in model_code
                )
                assert "description = Column(Text, nullable=False)" in model_code
                assert "metadata = Column(JSON, nullable=False)" in model_code

    def test_model_name_variations(self, temp_project_dir):
        """Test generation with different model name variations."""
        test_cases = [
            ("Post", "posts"),
            ("Category", "categories"),
            ("User", "users"),
            ("Box", "boxes"),
            ("City", "cities"),
            ("Story", "stories"),
            ("Company", "companies"),
        ]

        with patch("scripts.generate_crud.project_root", Path(temp_project_dir)):
            for model_name, expected_plural in test_cases:
                fields = [("name", "str")]
                options = {"soft_delete": False, "searchable": False, "admin": False}

                with patch.dict(
                    "sys.modules",
                    {
                        "app.core.config": MagicMock(),
                        "app.database.database": MagicMock(),
                        "app.models.models": MagicMock(),
                        "app.utils.pagination": MagicMock(),
                    },
                ):
                    from scripts.generate_crud import CRUDGenerator

                    generator = CRUDGenerator(model_name, fields, options)

                    # Check pluralization (should be lowercase for table names)
                    assert generator.model_name_plural.lower() == expected_plural

                    # Check table name in model
                    model_code = generator.generate_model()
                    assert f'__tablename__ = "{expected_plural}"' in model_code
