#!/usr/bin/env python3
"""
Demo script showing how the template customization works.

This script demonstrates the template customization process
without actually modifying any files.
"""

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the TemplateCustomizer class
spec = importlib.util.spec_from_file_location(
    "customize_template",
    project_root / "scripts" / "customize_template.py",
)
if spec is not None:
    customize_module = importlib.util.module_from_spec(spec)
    if spec.loader is not None:
        spec.loader.exec_module(customize_module)
else:
    raise ImportError("Could not load customize_template module")  # noqa: TRY003
TemplateCustomizer = customize_module.TemplateCustomizer


def create_demo_files(project_dir: Path) -> None:
    """Create demo files with template references."""
    demo_files = {
        "README.md": """# Your Project Name

A FastAPI application built with the [FastAPI Template](docs/TEMPLATE_README.md).

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

## 🐳 Docker

```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📚 Documentation

- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs
- **[Template Documentation](docs/TEMPLATE_README.md)** - Complete template guide
- **[Getting Started](docs/tutorials/getting-started.md)** - Setup and configuration
- **[Tutorials](docs/tutorials/TUTORIALS.md)** - Feature guides and examples

## 🏗️ Features

This application includes:

- **Authentication** - User registration, login, and JWT tokens
- **Database** - PostgreSQL with migrations and CRUD operations
- **Admin Panel** - Built-in admin interface
- **API Keys** - Secure API key management
- **Audit Logging** - Track all important actions
- **Testing** - Comprehensive test suite
- **Docker** - Containerized deployment

---

**Built with ❤️ using the [FastAPI Template](docs/TEMPLATE_README.md)**
""",
        "app/core/config.py": '''"""Configuration settings for the FastAPI Template application."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Template"
    DESCRIPTION: str = "FastAPI Template with Authentication"
    FROM_NAME: str = "FastAPI Template"

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:dev_password_123@localhost:5432/fastapi_template"

    class Config:
        env_file = ".env"
''',
        "docker-compose.yml": """version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fastapi_template
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: dev_password_123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:dev_password_123@postgres:5432/fastapi_template
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
""",
        "scripts/setup.sh": """#!/bin/bash

echo "🚀 Setting up FastAPI Template Development Environment"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o 'Python [0-9]\\.[0-9]' | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo "✅ FastAPI Template setup complete!"
""",
        "docs/tutorials/getting-started.md": """# Getting Started with FastAPI Template

Welcome! This guide will walk you through creating a new application based on this FastAPI template.

## What is FastAPI Template?

This FastAPI template is like a pre-built foundation for web applications. Think of it as a house that's already built with electricity, plumbing, and basic furniture - you just need to add your personal touches.

## Features Included

- **Authentication System**: User registration, login, password reset
- **Admin Panel**: Built-in admin interface for managing data
- **API Key Management**: Secure API key generation and management
- **Audit Logging**: Track all important actions
- **Database Management**: PostgreSQL with migrations
- **Testing Framework**: Comprehensive test suite
- **Docker Support**: Easy deployment with Docker
- **Production Ready**: Security, logging, error handling

## Quick Start

1. Clone the template
2. Run the setup script
3. Start developing!

For detailed instructions, see the main README.md file.
""",
        "app/main.py": '''"""Main FastAPI application."""

from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version="1.0.0",
)

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Template"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FastAPI Template"}
''',
    }

    for file_path, content in demo_files.items():
        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)


def show_before_after_demo() -> None:
    """Show a before/after demo of the customization process."""

    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    project_dir = Path(temp_dir) / "fast-api-template"
    project_dir.mkdir()

    try:
        # Create demo files
        create_demo_files(project_dir)

        # Show before state
        (project_dir / "README.md").read_text()

        config_before = (project_dir / "app/core/config.py").read_text()
        for line in config_before.split("\n"):
            if "FastAPI Template" in line or "fastapi_template" in line:
                pass

        # Create customizer with demo replacements
        customizer = TemplateCustomizer()
        customizer.project_root = project_dir
        customizer.replacements = {
            "fast-api-template": "myawesomeproject_backend",
            "fastapi_template": "myawesomeproject_backend",
            "FastAPI Template": "My Awesome Project",
            "FastAPI Template with Authentication": "Backend API for My Awesome Project",
            "Your Name": "John Doe",
            "your.email@example.com": "john@example.com",
            "fast-api-template-postgres-1": "myawesomeproject_backend-postgres-1",
            "fast-api-template-postgres": "myawesomeproject_backend-postgres",
        }

        # Process files
        files_to_process = customizer.get_files_to_process()
        processed_count = 0

        for file_path in files_to_process:
            if customizer.process_file(file_path):
                processed_count += 1

        # Show after state
        (project_dir / "README.md").read_text()

        # Show template README info

        config_after = (project_dir / "app/core/config.py").read_text()
        for line in config_after.split("\n"):
            if "My Awesome Project" in line or "myawesomeproject_backend" in line:
                pass

        # Show summary

        for _old_text, _new_text in customizer.replacements.items():
            pass

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    show_before_after_demo()
