# Getting Started with FastAPI Template

Welcome! This guide will walk you through creating a new application based on this FastAPI template. Whether you're a seasoned developer or just starting out, we'll make this process as smooth as possible.

---

> **🧪 Do I Need to Do Local Setup if I'm Using Coolify?**
>
> Yes — you should absolutely do the local setup first.
>
> Even if you plan to host the app on your server using Coolify, it's best to:
> - Build the app on your computer first
> - Test everything locally
> - Only push it to Coolify once it's working
>
> ⚠️ Don't skip local development — it's where you'll catch most bugs early and build faster.
>
> _Think of Coolify like a delivery system. It takes your app and sets it up on a live server. But if something's broken, it's much harder to debug on the server._
>
> _It's like baking a cake at home (local dev), tasting it, and then letting Coolify deliver it. You wouldn't want to deliver uncooked batter and hope it turns into cake on the way!_

---

## 🚀 Quick Setup Flow

```mermaid
flowchart TD
    A[Download Template] --> B[Run Setup Script]
    B --> C[Verify Setup]
    C --> D[Start Application]
    D --> E[Test Everything]
    E --> F[Explore Tutorials]
```

---

## What is this template?

This FastAPI template is like a pre-built foundation for web applications. Think of it as a house that's already built with electricity, plumbing, and basic furniture - you just need to add your personal touches!

### 🎯 What's included:
- **🔐 User authentication** (login, signup, password reset, OAuth)
- **🗄️ Database setup** with PostgreSQL and migrations
- **📧 Email functionality** for notifications and verification
- **👑 Admin panel** for managing users and data
- **🛡️ Security features** (rate limiting, CORS, JWT tokens)
- **🧪 Testing framework** ready to go
- **🐳 Docker support** for easy deployment
- **⚡ Optional features** (Redis, WebSockets, Celery)
- **🚀 CRUD scaffolding** - Generate complete CRUD boilerplate with one command
- **🛠️ Development tools** - Setup scripts, pre-commit hooks, verification tools

---

## 📋 Prerequisites

Before you start, make sure you have these tools installed on your computer:

### 🔧 Required Tools:
1. **Python 3.11+** - The programming language we'll use
2. **Git** - For version control (downloading and managing code)
3. **Docker** - For running databases and services
4. **A code editor** - Like VS Code, PyCharm, or even Notepad++

### 🔍 How to check if you have them:
Open your terminal/command prompt and type:
```bash
python --version
git --version
docker --version
```

If any of these commands don't work, you'll need to install them first:

### 📥 Installation Links:
- **[Python](https://www.python.org/downloads/)** - Download the latest version
- **[Git](https://git-scm.com/downloads)** - Available for all platforms
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** - For Windows/Mac
- **[VS Code](https://code.visualstudio.com/)** - Recommended code editor

### 🛠️ Recommended Additional Tools:
- **[pgAdmin](https://www.pgadmin.org/)** - PostgreSQL database management
- **[Beekeeper Studio](https://www.beekeeperstudio.io/)** - Modern SQL editor
- **[Postman](https://www.postman.com/)** - API testing and documentation

---

## 📥 Step 1: Download the Template

### Option A: Clone with Git (Recommended)
```bash
git clone https://github.com/your-username/fast-api-template.git my-new-app
cd my-new-app
```

### Option B: Download as ZIP
1. Go to the template repository on GitHub
2. Click the green "Code" button
3. Select "Download ZIP"
4. Extract the ZIP file to your desired location
5. The customization script will provide instructions for renaming the folder to your project name

> **💡 Note**: The template includes a user-friendly README.md that you can customize for your project. The comprehensive template documentation is available in [docs/TEMPLATE_README.md](TEMPLATE_README.md).

---

## 🎯 Step 1.5: Customize the Template (Recommended)

> **💡 Pro Tip:** Before setting up your environment, consider customizing the template to match your project's name and branding. This step is optional but highly recommended for a professional setup.

The template uses a simple 3-step process to transform it into your custom project:

### 🚀 Step 1: Rename the Template Directory
```bash
# Run the rename script
./scripts/rename_template.sh
```

This script will:
- Prompt you for your project name
- Generate a project slug automatically
- Rename the directory from `fast-api-template` to your project name
- Provide clear next steps

### 🔄 Step 2: Restart VS Code
After renaming, you need to restart VS Code to recognize the new directory:
```bash
# Close VS Code completely, then:
code your_project_name
# OR open VS Code and File → Open Folder → your_project_name
```

### ⚙️ Step 3: Customize the Template
```bash
# Run the customization script
./scripts/customize_template.sh
```

The script will prompt you for:
- **Project name** (e.g., "My Awesome Project")
- **Project slug** (e.g., "myawesomeproject_backend") - auto-generated if not provided
- **Database name** (e.g., "myawesomeproject_backend") - defaults to project slug
- **Docker project name** (e.g., "myawesomeproject_backend") - defaults to project slug
- **Description** (e.g., "Backend API for My Awesome Project application")
- **Author information** (name and email)

### Example Workflow:
```bash
# Step 1: Rename
$ ./scripts/rename_template.sh
Project name: My Awesome Project
# Script renames: fast-api-template → myawesomeproject_backend

# Step 2: Restart VS Code
$ code myawesomeproject_backend

# Step 3: Customize
$ ./scripts/customize_template.sh
Project name: My Awesome Project
Project slug: myawesomeproject_backend
# Script updates all files with your project details
```

### What Gets Customized:
- **Project Name**: "FastAPI Template" → "Your Project Name"
- **Project Slug**: "fast-api-template" → "your_project_name"
- **Database Name**: "fastapi_template" → "your_project_name"
- **Docker Containers**: All containers get unique names using `COMPOSE_PROJECT_NAME`
- **Documentation**: All references updated to reflect your project
- **Configuration Files**: Database URLs, container names, etc.
- **Environment Variables**: `COMPOSE_PROJECT_NAME` added to `.env` to prevent container conflicts

### After Customization:
1. Review the changes in `tests/template_tests/customization_improvements.md`
2. **Docker Container Naming**: The customization script adds `COMPOSE_PROJECT_NAME` to your `.env` file, ensuring each project gets unique container names and preventing conflicts when running multiple projects
3. Update your git remote to point to your new repository:
   ```bash
   git remote set-url origin <your-new-repo-url>
   git remote add upstream <template-repo-url>  # Optional: keep template as upstream
   ```
4. Continue with the setup process below

---

## 🔧 Step 2: Rename the Template Directory

**What this does:**
- Renames the template directory to your project name
- Prevents configuration conflicts
- Sets up the foundation for customization

**How to do it:**
```bash
# Run the rename script
./scripts/rename_template.sh
```

**Example:**
```bash
$ ./scripts/rename_template.sh
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

🚨 IMPORTANT: You must restart VS Code now!

Next steps:
1. Close VS Code completely
2. Open VS Code again
3. Open the folder: myawesomeproject_backend
4. Run the next script: ./scripts/customize_template.sh
```

## 🔄 Step 3: Restart VS Code

**Why this is important:**
- VS Code needs to recognize the new directory name
- Prevents path conflicts and configuration issues
- Ensures all tools work correctly

**How to do it:**
1. **Close VS Code completely** (not just the window)
2. **Open VS Code again**
3. **Open the renamed folder**: `myawesomeproject_backend`

**Quick way:**
```bash
code myawesomeproject_backend
```

## 🎨 Step 4: Customize the Template

**What this does:**
- Replaces all template references with your project details
- Updates database names and connection strings
- Changes import statements throughout the code
- Updates documentation and configuration files

**How to do it:**
```bash
# Run the customization script
./scripts/customize_template.sh
```

## 🚀 Step 5: Set Up Your Environment

### 🚀 Automated Setup (Recommended)
The template includes a setup script that handles everything automatically:

```bash
# Run the setup script
./scripts/setup_project.sh
```

This script will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Create a complete `.env` file with all required variables
- ✅ Start PostgreSQL and FastAPI services
- ✅ Run database migrations
- ✅ Verify the setup is working correctly
- ✅ Provide next steps and troubleshooting tips

### Option B: Manual Setup
If you prefer to set up everything manually:

#### Create a Virtual Environment
Think of a virtual environment as a clean workspace for your project. It keeps your project's dependencies separate from other projects on your computer.

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate
```

You'll know it's activated when you see `(venv)` at the beginning of your command line.

#### Install Dependencies
```bash
pip install -r requirements.txt
```

This installs all the packages your project needs. It might take a few minutes the first time.

---

## 🗄️ Step 6: Configure Your Database

> **Note:** If you used the automated setup script, this step is already complete! You can skip to the next section.

### Start PostgreSQL and FastAPI with Docker
```bash
docker-compose up -d postgres api
```

This uses the prebuilt `docker-compose.yml` file in the project, which spins up:
- **PostgreSQL**: Your main database
- **FastAPI**: Your API application

### Set Up Your Environment Variables

**💡 Important:** The `.env` file is a **hidden file** (starts with a dot). This is normal and intentional for security reasons.

Create a file called `.env` in your project root:

```bash
# If you have .env.example (the automated setup creates .env automatically)
cp .env.example .env

# To view hidden files including .env:
ls -la | grep -E "\.env"

# To view .env contents:
cat .env
```

**🆕 Environment Fix Script (Recommended):**
If you encounter any environment variable issues, use our dedicated fix script:
```bash
./scripts/fix_env_issues.sh
```

This script will:
- ✅ Detect and read existing `.env` files (including hidden ones)
- ✅ Add missing required environment variables
- ✅ Fix database configuration issues
- ✅ Validate Docker Compose configuration
- ✅ Test database connectivity
- ✅ Verify Alembic configuration

Then edit the `.env` file with your settings. Here are the most important ones:

> **📋 Environment Variables Reference**
>
> The template uses many environment variables for configuration. Here are the key ones:
>
> **Required:**
> - `DATABASE_URL` - PostgreSQL connection string
> - `SECRET_KEY` - Security key for JWT tokens
> - `ALGORITHM` - JWT algorithm (default: HS256)
>
> **Optional (enable features):**
> - `ENABLE_REDIS=true` - Enable Redis caching
> - `ENABLE_WEBSOCKETS=true` - Enable WebSocket support
> - `ENABLE_CELERY=true` - Enable background tasks
> - `ENABLE_RATE_LIMITING=true` - Enable rate limiting
> - `ENABLE_SENTRY=true` - Enable error monitoring
>
> **Email (for notifications):**
> - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
>
> **OAuth (for social login):**
> - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
> - `APPLE_CLIENT_ID`, `APPLE_CLIENT_SECRET`

```env
# Database settings (change 'password' to a strong password)
DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/fastapi_template

# Security settings (generate these with: openssl rand -hex 32)
SECRET_KEY=2f8e4c7e2b8d4e1a9c3b7f6d5e4c2a1b3d6e7f8c9b0a1e2d3c4b5a6f7e8d9c0
ALGORITHM=HS256

# Email settings (for password reset, etc.)
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Optional features (set to true to enable)
ENABLE_REDIS=true
ENABLE_WEBSOCKETS=true
ENABLE_CELERY=true
```

> **Tip:** You can generate a secure secret key with:
> ```bash
> openssl rand -hex 32
> ```

> **Note:** If you do not set up SMTP credentials, any feature that sends email (registration, password reset, etc.) will fail with an error in development mode. This is expected! You can still test most flows, but email delivery will not work until you provide valid SMTP settings.

### Run Database Migrations
```bash
alembic upgrade head
```

This creates all the necessary database tables.

---

## 👑 Step 4: Create Your First Superuser

A superuser is like an admin account that can access everything in your application.

```bash
python3 scripts/bootstrap_superuser.py
```

Follow the prompts to create your admin account.

---

## 🚀 Step 5: Start Your Application

### Start All Services with Docker
```bash
docker-compose up -d
```

Your application is now running! Open your web browser and go to:
- **Main app**: http://localhost:8000
- **API documentation**: http://localhost:8000/docs
- **Admin panel**: http://localhost:8000/admin

### Development Workflow
For development, you'll use the local Python environment for tools while the app runs in Docker:

```bash
# Development tools (run locally)
ruff format .
ruff check .
pytest

# Application (runs in Docker)
docker-compose up -d
docker-compose logs -f api
```

---

## ✅ Step 6: Verify Your Setup

Before testing, let's make sure everything is configured correctly:

### Run the Verification Script
```bash
# This will check all components and provide detailed feedback
python scripts/verify_setup.py
```

The verification script will test:
- ✅ Environment variables configuration
- ✅ Database connectivity
- ✅ Configuration loading
- ✅ Database migrations
- ✅ Docker services status
- ✅ File structure integrity

If any issues are found, the script will provide specific instructions to fix them.

### Common Issues and Solutions

**If verification fails, try these steps:**

1. **Service issues:**
   ```bash
   docker-compose down
   docker-compose up -d
   docker-compose logs -f
   ```

2. **Environment variable issues:**
   ```bash
   # Re-run the setup script
   ./scripts/setup_comprehensive.sh
   ```

3. **Migration conflicts:**
   ```bash
   alembic stamp head
   ```

## ✅ Step 7: Test Everything Works

1. **Check the health endpoint**: Visit http://localhost:8000/health
2. **Try the API docs**: Visit http://localhost:8000/docs
3. **Test user registration**: Use the `/auth/register` endpoint in the docs

### Available Health Endpoints
The template includes comprehensive health monitoring:

```bash
# Comprehensive health check (includes database, Redis, rate limiting, etc.)
curl http://localhost:8000/health

# Simple health check (basic uptime)
curl http://localhost:8000/health/simple

# Readiness check (for Kubernetes)
curl http://localhost:8000/health/ready

# Liveness check (for Kubernetes)
curl http://localhost:8000/health/live

# Rate limiting status
curl http://localhost:8000/health/rate-limit

# Test Sentry error monitoring
curl http://localhost:8000/health/test-sentry
```

### 🧪 Quick Test Commands
```bash
# Test the health endpoint
curl http://localhost:8000/health

# Run all tests
pytest --cov -v

# Run only template tests
pytest -m "template_only"

# Test specific features
pytest tests/template_tests/test_auth.py -v
```

### Main Application Endpoints
Your application includes these key endpoints:

```bash
# Root endpoint
curl http://localhost:8000/

# Features overview
curl http://localhost:8000/features

# API documentation
open http://localhost:8000/docs

# Alternative API docs
open http://localhost:8000/redoc

# OpenAPI schema
curl http://localhost:8000/api/v1/openapi.json
```

### Available API Routes
The template includes these API endpoints:

**Authentication (`/api/v1/auth/`):**
- `POST /register` - Create new user account
- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `POST /logout` - User logout
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password with token
- `POST /verify-email` - Verify email address
- `GET /me` - Get current user info

**Users (`/api/v1/users/`):**
- `GET /` - List users (with pagination/search)
- `GET /{user_id}` - Get specific user
- `PUT /me` - Update current user
- `DELETE /me` - Delete current user

**Admin (`/api/v1/admin/`):**
- `GET /users` - List all users (admin only)
- `GET /audit-logs` - View audit logs (admin only)
- `PUT /users/{user_id}` - Update user (admin only)
- `DELETE /users/{user_id}` - Delete user (admin only)

**Optional Features:**
- WebSockets (`/api/v1/ws/`) - Real-time communication
- Celery (`/api/v1/celery/`) - Background task management

---

## 🎯 What's Next?

Now that your basic application is running, you can:

1. **📚 Explore the tutorials** in the `docs/tutorials/` folder to learn about specific features
2. **🔐 Learn authentication** - Start with the [Authentication Tutorial](tutorials/authentication.md)
3. **🗄️ Master database management** - Check out the [Database Tutorial](tutorials/database-management.md)
4. **🧪 Set up testing** - Follow the [Testing Tutorial](tutorials/testing-and-development.md)
5. **🌐 Deploy to production** - Read the [Deployment Tutorial](tutorials/deployment-and-production.md)
6. **⚡ Add optional features** - Explore the [Optional Features Tutorial](tutorials/optional-features.md)
7. **🚀 Generate CRUD boilerplate** - Use the CRUD scaffolding tool

### 📁 Understanding Your Project Structure

```
fast-api-template/
├── 📁 app/                    # Main application code
│   ├── 📁 api/               # API endpoints and routes
│   │   └── 📁 api_v1/
│   │       └── 📁 endpoints/ # Route handlers (auth, users, admin, health)
│   ├── 📁 core/              # Configuration and core utilities
│   ├── 📁 crud/              # Database operations
│   ├── 📁 models/            # SQLAlchemy database models (separated by entity)
│   │   ├── base.py           # Base model and mixins
│   │   ├── user.py           # User model
│   │   ├── api_key.py        # API key model
│   │   ├── audit_log.py      # Audit log model
│   │   └── refresh_token.py  # Refresh token model
│   ├── 📁 schemas/           # Pydantic schemas for validation
│   ├── 📁 services/          # Business logic and external services
│   └── 📁 utils/             # Utility functions
├── 📁 alembic/               # Database migrations
├── 📁 docs/                  # Documentation (you're here!)
├── 📁 tests/                 # Test files (360+ tests)
│   └── 📁 template_tests/    # Template-specific tests
├── 📁 scripts/               # Utility scripts
├── 📄 docker-compose.yml     # Docker services
├── 📄 requirements.txt       # Python dependencies
└── 📄 .env                   # Environment variables
```

**Key files to know:**
- `app/main.py` - Application entry point
- `app/core/config.py` - All configuration settings
- `app/models/` - Database models (separated by entity)
- `app/api/api_v1/endpoints/` - API route handlers
- `alembic/versions/` - Database migration files

### 📁 **Full folder layout and feature-by-feature tutorials** are available in `docs/tutorials/`

### 🔗 **Read more about FastAPI itself**: [FastAPI Official Documentation](https://fastapi.tiangolo.com/)

---

## 🚨 Common Issues and Solutions

### ✅ **Automatic Fixes Included**

The template now includes automatic fixes for common setup issues:

- **Python Version Detection**: Automatically detects and uses `python3.11` if available
- **Missing alembic.ini**: Automatically creates `alembic.ini` with proper configuration
- **Database Creation**: Automatically creates main and test databases before migrations
- **Docker Container Conflicts**: Uses `COMPOSE_PROJECT_NAME` to prevent naming conflicts
- **Migration Conflicts**: Automatically handles existing tables with `alembic stamp head`

### Docker Container Naming Conflicts
**Problem**: When creating multiple projects from the template, Docker containers might have the same names, causing conflicts.

**Solution**: The template customization script automatically adds `COMPOSE_PROJECT_NAME` to your `.env` file, ensuring each project gets unique container names. If you encounter container conflicts:

1. **Check your `.env` file** - ensure `COMPOSE_PROJECT_NAME` is set to your project name
2. **Stop existing containers** - `docker-compose down` in other project directories  
3. **Use different project names** - each project should have a unique name during customization

### "Port already in use" error
If you get an error about port 8000 being in use, try:
```bash
# Stop other containers first
docker-compose down

# Start with a different port
docker-compose up -d
# Or if running locally: uvicorn app.main:app --reload --port 8001
```

### Database connection errors
Make sure Docker is running and PostgreSQL is started:
```bash
docker-compose ps
```

### Import errors
Make sure your virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Docker not starting
Make sure Docker Desktop is running and you have sufficient permissions:
```bash
docker --version
docker-compose --version
```

---

## 🧪 Testing Your Application

If you want to run tests to make sure everything is working correctly:

```bash
# Run all tests with coverage report
pytest --cov -v

# Run only template tests
pytest -m "template_only"

# Run specific test files
pytest tests/template_tests/test_auth.py -v

# Run tests for a specific feature
pytest tests/template_tests/test_auth_email_verification.py -v

# Run tests in parallel (faster)
pytest -n auto
```

**Note**: Tests will automatically use the `.env.test` configuration file if it exists, ensuring your test database is separate from your development database.

---

## 🛠️ Development Tools

### Available Scripts
The template includes several utility scripts to help with development:

```bash
# Bootstrap admin user
./scripts/bootstrap_admin.py

# Bootstrap superuser
./scripts/bootstrap_superuser.sh

# Install pre-commit hooks
./scripts/install_precommit.sh

# Run linting
./scripts/lint.sh

# Setup GlitchTip (error monitoring)
./scripts/setup_glitchtip.sh

# Demo error responses
python3 scripts/demo_error_responses.py

# Logging demo
python3 scripts/logging_demo.py

# Fix common issues
./scripts/fix_common_issues.sh
```

### Code Quality Tools
```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/

# Run all quality checks
./scripts/lint.sh
```

### 🛡️ Pre-commit Hooks (Automatic Quality Checks)

This template includes pre-commit hooks that automatically run code quality checks before every commit. This means **mypy and ruff will automatically check your code** when you commit, helping catch errors before they reach GitHub or CI.

**Setup (one-time):**
```bash
# Install pre-commit hooks
./scripts/install_precommit.sh
```

**What happens automatically:**
- **ruff**: Fast Python linting with zero warnings
- **black**: Automatic code formatting
- **mypy**: Static type checking with zero errors

**Manual checks (if needed):**
```bash
# Run all pre-commit hooks manually
pre-commit run --all-files

# Run specific hooks
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

> **💡 Pro Tip**: While pre-commit hooks catch most issues, they may not catch everything. If you see errors in GitHub CI that weren't caught locally, you can run `pre-commit run --all-files` to check all files, not just the ones you're committing.

### 🚀 **CRUD Scaffolding**

Generate complete CRUD boilerplate with one command:

```bash
# Generate a Post model with title, content, and is_published fields
python3 scripts/generate_crud.py Post title:str content:str is_published:bool

# Generate a Product model with soft delete and search capabilities
python3 scripts/generate_crud.py Product name:str price:float description:str --soft-delete --searchable

# Generate an admin-managed Category model
python3 scripts/generate_crud.py Category name:str slug:str --admin
```

This generates:
- SQLAlchemy model with proper relationships
- Pydantic schemas for validation
- CRUD operations with search and filtering
- API endpoints with pagination
- Basic tests
- Auto-registration in the API router

### Database Management
```bash
# View database with pgAdmin (if installed)
# Connect to: localhost:5432, database: fastapi_template

# Or use Beekeeper Studio
# Connection string: postgresql://postgres:password@localhost:5432/fastapi_template
```

---

## 🛠️ Troubleshooting Common Issues

### Environment Variable Problems

**Problem:** "The 'POSTGRES_DB' variable is not set. Defaulting to a blank string."
**Solution:**
```bash
# Run the environment fix script
./scripts/fix_env_issues.sh
```

**Problem:** Can't find the `.env` file
**Solution:**
```bash
# Show hidden files
ls -la | grep -E "\.env"

# If it doesn't exist, create it
cp .env.example .env
```

### Database Connection Issues

**Problem:** "connection to server at localhost failed"
**Solution:**
```bash
# Ensure Docker services are running
docker-compose up -d

# Wait for services to be ready
sleep 10

# Test connection
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"
```

### Alembic Configuration Errors

**Problem:** `configparser.InterpolationSyntaxError`
**Solution:**
```bash
# The fix script handles this automatically
./scripts/fix_env_issues.sh
```

### Test Suite Issues

**Problem:** Tests fail with database connection errors
**Solution:**
```bash
# Ensure services are running
docker-compose up -d

# Activate virtual environment
source venv/bin/activate

# Run tests
pytest
```

### Virtual Environment Issues

**Problem:** "command not found" for Python tools
**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Problem:** Verification script fails with "No module named 'fastapi'"
**Solution:**
```bash
# The verification script needs the virtual environment activated
source venv/bin/activate && python3 scripts/verify_setup.py

# Or run it directly with venv Python
./venv/bin/python scripts/verify_setup.py
```

### VS Code Workspace Issues

**Problem:** Project disappeared from VS Code after customization
**Solution:**
```bash
# The customization script provides instructions to rename the directory
# Follow the instructions provided by the script:
# 1. Close VS Code completely
# 2. Rename the directory using the provided commands
# 3. Reopen the renamed directory in VS Code
# 4. Or use the workspace file: .vscode/project.code-workspace
```

**Problem:** VS Code can't find the Python interpreter
**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# In VS Code:
# 1. Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows/Linux)
# 2. "Python: Select Interpreter"
# 3. Choose: ./venv/bin/python
```

### Quick Diagnostic Commands

```bash
# Check environment
./scripts/fix_env_issues.sh

# Check service status
docker-compose ps

# Check logs
docker-compose logs api

# Test API health (note the correct path)
curl http://localhost:8000/api/v1/health

# Run verification (with virtual environment)
source venv/bin/activate && python3 scripts/verify_setup.py
```

---

## 🎉 You're Ready!

Congratulations! You now have a fully functional FastAPI application running locally. Here's what you can do next:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Check the Admin Panel**: Visit http://localhost:8000/admin
3. **Run Tests**: `pytest` to verify everything works
4. **Read More Tutorials**: Check out the other guides in the `docs/tutorials/` folder
5. **Start Building**: Add your own features and endpoints

---

## 🚀 Quick Start Guide

### Test Your Setup

Here are the exact commands to verify everything is working:

```bash
# 1. Activate virtual environment (if not already activated)
source venv/bin/activate

# 2. Verify your setup
python3 scripts/verify_setup.py

# 3. Test the API health endpoint
curl http://localhost:8000/api/v1/health

# 4. Run the test suite
pytest

# 5. Check that services are running
docker-compose ps
```

### Common First Steps

**View API Documentation:**
- Open http://localhost:8000/docs in your browser
- This shows all available endpoints and lets you test them

**Create Your First User:**
```bash
# Create a superuser account
python3 app/bootstrap_superuser.py
```

**Check the Admin Panel:**
- Visit http://localhost:8000/admin
- Login with your superuser credentials
- Manage users, API keys, and audit logs

**Start Developing:**
```bash
# Your API is running at: http://localhost:8000
# API docs are at: http://localhost:8000/docs
# Admin panel is at: http://localhost:8000/admin
```

### Environment Variables Explained

**Local Development (.env file):**
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Database configuration
- `SECRET_KEY` - Security key for JWT tokens
- `FIRST_SUPERUSER` - Initial admin email (optional)

**Docker Environment (set in docker-compose.yml):**
- `DATABASE_URL` - Full database connection string
- `API_PORT` - Port for the FastAPI application
- `ENABLE_REDIS`, `ENABLE_CELERY` - Feature toggles

**Note:** Some environment variables are set in Docker containers and won't appear in your local `.env` file. This is normal!

### Health Endpoint Path

The API uses versioned endpoints. The health check is available at:
- ✅ **Correct**: `http://localhost:8000/api/v1/health`
- ❌ **Wrong**: `http://localhost:8000/health`

### Virtual Environment Tips

**Always activate before running Python scripts:**
```bash
# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**Or run scripts directly with venv Python:**
```bash
# Mac/Linux
./venv/bin/python scripts/verify_setup.py

# Windows
venv\Scripts\python.exe scripts\verify_setup.py
```

Happy coding! 🚀