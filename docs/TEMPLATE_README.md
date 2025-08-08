# FastAPI Template - Complete Setup Guide

A comprehensive, production-ready FastAPI template with authentication, admin panel, API keys, audit logging, and more.


![Coverage](https://img.shields.io/badge/coverage-74%25-yellowgreen)
![CI](https://github.com/triciaward/fast-api-template/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 🚀 Getting Started

### ⚠️ CRITICAL: Create a New GitHub Repository First!

**🚨 IMPORTANT:** Before starting the setup process, you MUST create a new GitHub repository for your project. If you don't, you risk accidentally overwriting this template repository!

**How to create your new repository:**
1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" button in the top right corner
3. Select "New repository"
4. Name it something like "my-project-backend" or "my-awesome-api"
5. **DO NOT** initialize with README, .gitignore, or license (we'll add these)
6. Click "Create repository"
7. Copy the repository URL (you'll need this later)

**Why this is critical:**
- The setup process will rename and customize the template
- Without a new repo, you might accidentally push changes back to this template
- Your customized project needs its own repository to track changes
- This prevents confusion and protects the original template

### Step 1: Clone and Rename

```bash
# Clone your new repository
git clone <your-repo-url>
cd your-project-backend

# Rename the template directory to your project name
./scripts/setup/rename_template.sh
```

**What this does:**
- Renames the template directory to your project name with "_backend" suffix
- Prevents configuration conflicts
- Sets up the foundation for customization

**Example:**
```bash
$ ./scripts/setup/rename_template.sh
🚀 FastAPI Template - Step 1: Rename Directory
==============================================

Please enter your project name:
  Examples: 'My Awesome Project', 'Todo App Backend', 'E-commerce API'

Project name: My Awesome Project

📋 Summary:
  Project Name: My Awesome Project
  Directory Name: myawesomeproject_backend

Continue with renaming? (y/N): y

🔄 Renaming directory...
✅ Directory renamed successfully!

🎉 STEP 1 COMPLETE!
==================

🚨 CRITICAL: You must restart VS Code now!

Next steps:
1. Close VS Code completely
2. Open VS Code again
3. Open the folder: myawesomeproject_backend
4. Run the next script: ./scripts/setup/customize_template.sh
```

### Step 2: Restart VS Code

**Why this is important:**
- VS Code needs to recognize the new directory name
- Prevents path conflicts and configuration issues
- Ensures all tools work correctly

**How to do it:**
1. **Close VS Code completely** (not just the window)
2. **Open VS Code again**
3. **Open the renamed folder**: `myawesomeproject_backend`

### Step 3: Customize the Template

```bash
# Customize the template for your project
python scripts/setup/customize_template.py
```

**What this does:**
- Replaces all template references with your project details
- Updates database names and connection strings
- Changes import statements throughout the code
- Updates documentation and configuration files
- Modifies Docker setup to prevent conflicts

**Example:**
```bash
$ python scripts/setup/customize_template.py
🚀 FastAPI Template Customization - Step 2
==========================================
This script will transform the template into your custom project.

Project name (e.g., 'My Awesome Project'): My Awesome Project
Project slug (e.g., 'myawesomeproject_backend'): myawesomeproject_backend
Database name (e.g., 'myawesomeproject_backend', default: myawesomeproject_backend): 
Project description (e.g., 'A FastAPI backend for my awesome project'): A FastAPI backend for my awesome project
Author name (e.g., 'Your Name'): Your Name
Author email (e.g., 'your.email@example.com'): your.email@example.com

📋 Customization Summary:
  Project Name: My Awesome Project
  Project Slug: myawesomeproject_backend
  Database Name: myawesomeproject_backend
  Docker Name: myawesomeproject_backend
  Description: A FastAPI backend for my awesome project
  Author: Your Name <your.email@example.com>

Proceed with customization? (y/N): y

🚀 Starting template customization...
📁 Scanning files for template references...
🔄 Processing files...
   ✅ Updated: README.md
   ✅ Updated: docker-compose.yml
   ✅ Updated: app/main.py
   ✅ Updated: .env
   ... (more files)

📊 Customization Summary:
   Files processed: 45
   Files updated: 42

🎉 STEP 2 COMPLETE!
==================

📋 Next Steps:
1. **🚨 CRITICAL:** Update your git remote to point to your new repository:
   ```bash
   git remote set-url origin https://github.com/yourusername/your-new-repo-name.git
   ```
2. Run the setup script: ./scripts/setup/setup_project.sh
3. Start developing your application!
```

### Step 4: Set Up Your Project

```bash
# Set up your project environment
./scripts/setup/setup_project.sh
```

**What this does:**
- Creates Python virtual environment
- Installs all dependencies
- Starts PostgreSQL and FastAPI
- Runs database migrations
- Sets up everything you need to start developing

**Example:**
```bash
$ ./scripts/setup/setup_project.sh
🚀 FastAPI Template - Step 3: Project Setup
===========================================

✅ You're in a renamed project directory: myawesomeproject_backend

📦 Installing Python dependencies...
✅ Dependencies installed

🐳 Checking Docker...
✅ Docker is running

🗄️  Starting database services...
✅ Database services started

⏳ Waiting for PostgreSQL to be ready...
✅ PostgreSQL is ready

🔄 Running database migrations...
✅ Database migrations completed

👤 Create a superuser account (optional):
Create superuser? (y/N): y

Running superuser creation script...
✅ Superuser creation completed

🔍 Running final checks...
   

🎉 STEP 3 COMPLETE!
==================

🚀 Your project is ready!

📋 What's been set up:
  ✅ Python virtual environment
  ✅ All dependencies installed
  ✅ PostgreSQL database running
  ✅ FastAPI application running
  ✅ Database migrations applied
  ✅ Environment variables configured

🎯 Next Steps:
1. View API docs: http://localhost:8000/docs

3. Start developing!

💡 Useful Commands:
  docker-compose up -d          # Start all services
  docker-compose logs -f        # View logs
  docker-compose down           # Stop all services
  
  alembic revision --autogenerate -m 'description'  # Create migration
  alembic upgrade head          # Apply migrations
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