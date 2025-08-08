# FastAPI Template - Complete Setup Guide

A comprehensive, production-ready FastAPI template with authentication, admin panel, API keys, audit logging, and more.

[![CI](https://github.com/triciaward/fast-api-template/workflows/CI/badge.svg)](https://github.com/triciaward/fast-api-template/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Test Coverage](https://img.shields.io/badge/coverage-98.2%25-brightgreen.svg)](https://github.com/triciaward/fast-api-template)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Check: MyPy](https://img.shields.io/badge/type%20check-mypy-blue.svg)](https://mypy-lang.org/)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-red.svg)](https://github.com/astral-sh/ruff)
[![Template Grade: A+](https://img.shields.io/badge/template%20grade-A%2B-brightgreen.svg)](https://github.com/triciaward/fast-api-template)
[![Test Files: 173](https://img.shields.io/badge/test%20files-173-blue.svg)](https://github.com/triciaward/fast-api-template)
[![Execution Time: 8.86s](https://img.shields.io/badge/execution%20time-8.86s-green.svg)](https://github.com/triciaward/fast-api-template)

## 🚀 Getting Started

### 🤖 For AI Assistants

If you're helping a user set up this project:
1. **Use the streamlined setup process below** - one command does everything
2. **No manual steps required** - the script handles all customization automatically
3. **GitHub template approach recommended** - click "Use this template" for best experience

### Quick Start (GitHub Template)

**🎯 ONE COMMAND SETUP** - Use GitHub's template feature:

```bash
# 1. Click "Use this template" button above to create your repo
# 2. Clone YOUR new repository
git clone https://github.com/yourusername/your-project-name.git
cd your-project-name

# 3. Run the setup script
./scripts/setup/setup_project.py
```

**That's it!** The script will:
- ✅ Customize all files with your project details
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Start PostgreSQL database
- ✅ Run database migrations
- ✅ Create superuser account
- ✅ Install git protection hooks
- ✅ Verify everything works

### What the Setup Script Does

The `setup_project.py` script is an intelligent, all-in-one solution:

1. **Interactive Setup**: Prompts for your project details
2. **File Customization**: Replaces all template placeholders with your details
3. **Environment Setup**: Creates virtual environment and installs dependencies
4. **Service Management**: Starts Docker services and waits for readiness
5. **Database Setup**: Runs migrations and creates superuser
6. **Git Protection**: Installs hooks to prevent pushing to template repository
7. **Validation**: Tests that everything is working correctly

### Example Setup Flow

```bash
$ ./scripts/setup/setup_project.py
🚀 FastAPI Project Setup
==========================

Setting up your FastAPI project...

Project name [My Awesome API]: Todo App Backend
Author name: John Doe
Author email: john@example.com
Database name [todo_app_backend]: 
Project description [A FastAPI backend for Todo App Backend]: 

📋 Setup Summary:
=============================
  Project Name: Todo App Backend
  Project Folder: todo_app_backend
  Database Name: todo_app_backend
  Description: A FastAPI backend for Todo App Backend
  Author: John Doe <john@example.com>
  Action: Customize files in current directory

Proceed with setup? (y/N): y

🔄 Customizing project files...
   ✅ Updated: README.md
   ✅ Updated: docker-compose.yml
   ✅ Updated: app/main.py
   (... more files ...)
✅ Customization complete: 42/45 files updated

🔧 Setting up development environment...
   Creating .env file...
   ✅ .env file created
   Creating Python virtual environment...
   ✅ Virtual environment created
   Installing Python dependencies...
   ✅ Dependencies installed

🐳 Checking Docker...
✅ Docker is running

🗄️  Starting database services...
✅ Database service started
⏳ Waiting for PostgreSQL to be ready...
✅ PostgreSQL is ready

🔄 Running database migrations...
✅ Database migrations completed

👤 Creating superuser account...
   Email: admin@todoapp.com
   Password: Admin123!
✅ Superuser created successfully

🔍 Running final checks...
   ✅ API imports successfully
   ✅ Configuration loads successfully

🎉 PROJECT SETUP COMPLETE!
==========================

🚀 Your FastAPI project is ready!

📋 What's been set up:
  ✅ Project files customized
  ✅ Python virtual environment created
  ✅ Dependencies installed
  ✅ PostgreSQL database running
  ✅ Database migrations applied
  ✅ Superuser account created

🎯 Next Steps:
1. Start the API server:
   docker-compose up -d api

2. View API documentation:
   http://localhost:8000/docs

3. Update your git remote (if needed):
   git remote set-url origin https://github.com/yourusername/todo_app_backend.git

4. Start developing your application!

💡 Useful Commands:
  docker-compose up -d          # Start all services
  docker-compose logs -f api    # View API logs
  docker-compose down           # Stop services
  source venv/bin/activate      # Activate virtual environment
  pytest                        # Run tests

✨ Happy coding! 🚀
```



## 🎯 Quick Commands (After Setup)

Once your project is set up, you can use these commands:

```bash
# Start the application
docker-compose up -d

# View API documentation
open http://localhost:8000/docs

# Check code quality
./scripts/development/validate_ci.sh

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## 🛠️ What's Included

This FastAPI template provides a comprehensive foundation for building production-ready APIs:

### 🔐 Authentication & Security
- JWT-based authentication with modular architecture
- Password hashing with bcrypt
- Email verification workflow
- OAuth integration (Google, Apple)
- Password reset functionality
- Account deletion with soft delete
- Rate limiting and CORS configuration
- Enhanced security headers with request validation

### 👥 User Management
- User registration and login
- Email verification and password reset
- Account deletion with audit trails
- User profiles and admin management

### 🔑 API Keys
- API key generation and management
- Scoped permissions and expiration dates
- Admin dashboard for key management
- Audit logging for key usage

### 📊 Admin Panel
- User management interface
- API key management
- System statistics and audit log viewing
- Bulk operations

### 🗄️ Database
- PostgreSQL with SQLAlchemy async operations
- Alembic migrations
- Connection pooling and optimized queries
- Soft delete support

### 🚀 Performance & Monitoring
- Redis caching (optional)
- Celery task queue (optional)
- Comprehensive health check endpoints
- Performance monitoring utilities
- Error tracking with Sentry (optional)

### 🛠️ Development Tools
- Pre-commit hooks for code quality
- Code generation and CRUD scaffolding
- Automated setup scripts
- Fix scripts for common issues
- Verification tools

## 📁 Project Structure

Your project is organized using a **domain-based architecture** for better maintainability:

```
app/
├── api/                    # API endpoints (domain-based)
│   ├── auth/              # Authentication endpoints
│   ├── users/             # User management endpoints
│   ├── admin/             # Admin panel endpoints
│   ├── system/            # System endpoints (health, etc.)
│   └── integrations/      # External integrations (WebSockets)
├── crud/                  # Database operations (domain-based)
│   ├── auth/              # Authentication CRUD operations
│   └── system/            # System CRUD operations
├── models/                # Database models (domain-based)
│   ├── auth/              # Authentication models
│   ├── core/              # Base models
│   └── system/            # System models
├── schemas/               # Pydantic schemas (domain-based)
│   ├── auth/              # Authentication schemas
│   ├── admin/             # Admin schemas
│   └── core/              # Core schemas
├── services/              # Business logic services
│   ├── auth/              # Authentication services
│   ├── background/        # Background tasks (Celery)
│   ├── external/          # External services (Email, Redis)
│   ├── middleware/        # Request middleware
│   └── monitoring/        # Monitoring and audit
├── core/                  # Core application configuration
│   ├── config/            # Settings and configuration
│   ├── security/          # Security utilities
│   ├── error_handling/    # Error handling
│   └── admin/             # Admin utilities
├── utils/                 # Utility functions
└── database/              # Database configuration
```

## 🔧 Key Features

### **Async-First Architecture**
The entire application uses **async/await patterns** for optimal performance:

```python
# Database operations are async
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).filter(User.email == email)
    )
    return result.scalar_one_or_none()

# API endpoints are async
@router.get("/users/me")
async def get_current_user(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    return current_user
```

### **Domain-Based Organization**
Code is organized by **business domains** rather than technical layers:

- **Authentication Domain**: `app/api/auth/`, `app/crud/auth/`, `app/models/auth/`
- **User Management Domain**: `app/api/users/`, `app/crud/auth/user.py`
- **System Domain**: `app/api/system/`, `app/crud/system/`

### **Type Safety**
Full type annotations throughout the codebase:

```python
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(
    db: AsyncSession, 
    user_data: UserCreate
) -> User:
    # Type-safe database operations
    pass
```

## 🚀 Development Workflow

### **Local Development**
```bash
# Start services
docker-compose up -d

# Run development tools
ruff format .
ruff check .

# View logs
docker-compose logs -f api
```

> Note: The backend (`api`) and database (`postgres`) run inside Docker. Use the Python virtual environment only for developer tooling (formatting, linting, Alembic command generation), not for running the server.

### **Database Migrations**
```bash
# Create new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### **Code Quality**
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy app/

# Run all quality checks
./scripts/development/validate_ci.sh
```

## 🧪 Testing

- Run tests: `pytest -q`
- With coverage: `pytest --cov=app --cov-report=term-missing -q`
- Skipped, feature-flagged tests and how to enable them are documented in [`docs/testing/skipped-tests.md`](docs/testing/skipped-tests.md).

## 📊 Monitoring and Health

### **Health Check Endpoints**
Comprehensive health monitoring:

```bash
# Basic health
curl http://localhost:8000/system/health

# Simple health (load balancer)
curl http://localhost:8000/system/health/simple

# Detailed health with database
curl http://localhost:8000/system/health/detailed

# Database-specific health
curl http://localhost:8000/system/health/database

# Application metrics
curl http://localhost:8000/system/health/metrics

# Readiness probe (Kubernetes)
curl http://localhost:8000/system/health/ready

# Liveness probe (Kubernetes)
curl http://localhost:8000/system/health/live
```

### **Performance Monitoring**
Built-in performance utilities:

```python
from app.utils.performance import monitor_request_performance

@monitor_request_performance()
async def expensive_operation():
    # Your code here
    pass
```

## 🔧 Configuration

### **Environment Variables**
Key configuration in `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/your_project

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Optional Services
ENABLE_REDIS=false
ENABLE_CELERY=false
ENABLE_WEBSOCKETS=false
```

### **Settings Management**
Centralized configuration in `app/core/config/config.py`:

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "Your Project"
    DATABASE_URL: str
    SECRET_KEY: str
    # ... other settings
```

## 🎯 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Read the template assessment**: Check out the [architecture evaluation](tutorials/template-audit.md)
3. **Add your features**: Start building in the domain-based structure
4. **Read the tutorials**: Check out the other guides in `docs/tutorials/`
5. **Customize the project**: Update README and project details

## 🆘 Need Help?

- **Template Assessment**: See [tutorials/template-audit.md](tutorials/template-audit.md) for architecture evaluation
- **Troubleshooting**: Check `docs/troubleshooting/` for common issues
- **Tutorials**: See `docs/tutorials/` for detailed guides
- **API Documentation**: Visit http://localhost:8000/docs for interactive docs

---

**Happy coding! 🚀**