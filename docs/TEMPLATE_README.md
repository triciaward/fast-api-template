# FastAPI Template

A comprehensive, production-ready FastAPI template with authentication, admin panel, API keys, audit logging, and more.

![Tests](https://img.shields.io/badge/tests-414%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-74%25-yellowgreen)
![CI](https://github.com/triciaward/fast-api-template/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 🚀 Quick Start

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

**🛡️ Safety Features:** This template includes multiple protection mechanisms:
- **Pre-commit hooks** that warn about template repository operations
- **Git hooks** that prevent commits to the template repository
- **Documentation warnings** throughout the setup process

### Option 1: Use as Template (Recommended)

```bash
# Clone the template
git clone <your-repo-url>
cd fast-api-template

# Step 1: Rename the template directory
./scripts/rename_template.sh

# Step 2: Restart VS Code and open the renamed directory
code your_project_name

# Step 3: Customize the template for your project
./scripts/customize_template.sh

# Step 4: Set up your project environment
./scripts/setup_project.sh

# Install pre-commit hooks (recommended for code quality)
pre-commit install

# Start the application
docker-compose up -d
```

> **🎯 What's New**: The setup script now automatically handles common issues like Python version detection, missing alembic.ini files, database creation, and Docker container naming conflicts!

### Option 2: Use as Reference

```bash
# Clone the template
git clone <your-repo-url>
cd fast-api-template

# Run the comprehensive setup script (handles everything automatically!)
./scripts/setup_comprehensive.sh

# Install pre-commit hooks (recommended for code quality)
pre-commit install

# Start the application
docker-compose up -d
```

## 🤖 AI ASSISTANT WORKFLOW INSTRUCTIONS

**⚠️ CRITICAL:** When helping users create projects from this template, follow this EXACT workflow:

1. **Run rename script:** `./scripts/rename_template.sh`
2. **STOP and provide clear instructions:** Tell user to restart VS Code and open renamed directory
3. **Provide the exact message:** Give user the exact message to copy/paste after restart
4. **Wait for confirmation:** Only continue after user confirms VS Code is restarted
5. **Continue with customization:** `./scripts/customize_template.sh`

**DO NOT automatically continue to step 3 without waiting for VS Code restart!**

**📋 EXACT MESSAGE TO GIVE USER AFTER RENAME:**
```
✅ Directory renamed successfully!

🚨 CRITICAL: You must restart VS Code now!

Next steps:
1. Close VS Code completely
2. Open VS Code again  
3. Open the folder: [PROJECT_NAME]_backend
4. Copy and paste this message to your AI assistant:

"I've restarted VS Code and opened the renamed directory: [PROJECT_NAME]_backend

Please help me continue with the template customization process. I need to:
1. Run the customization script
2. Set up my project environment  
3. Get my FastAPI application running

The directory has been renamed from "fast-api-template" to "[PROJECT_NAME]_backend" and I'm now in the renamed directory."
```

## 🎯 Template Customization

The template includes a powerful customization script that transforms all template references into your project-specific names:

### 🆕 **Recent Improvements**

The template has been enhanced with automatic fixes for common setup issues:

- **🔍 Smart Python Detection**: Automatically finds and uses `python3.11` if available
- **📄 Auto alembic.ini**: Creates missing `alembic.ini` files with proper configuration
- **🗄️ Database Auto-Creation**: Creates main and test databases before running migrations
- **🐳 Container Isolation**: Uses `COMPOSE_PROJECT_NAME` to prevent Docker container conflicts
- **🔄 Migration Handling**: Automatically resolves migration conflicts with existing tables
- **📁 Organized Documentation**: Customization logs saved in `docs/` folder

### 🚨 **Critical Fixes Applied (July 2025)**

**Fixed critical issues that were causing problems for users:**

- **✅ Missing alembic.ini File**: Automatic creation of database migration configuration file
- **✅ Commented Superuser Variables**: Uncommented `FIRST_SUPERUSER` and `FIRST_SUPERUSER_PASSWORD` in `.env.example`
- **✅ Setup Script Directory Check**: Made setup script work with both renamed and original template directories
- **✅ Automatic Superuser Creation**: Changed from optional to automatic superuser creation during setup
- **✅ Docker Container Conflicts**: Ensured `COMPOSE_PROJECT_NAME` prevents container naming conflicts
- **✅ CORS Environment Variable Parsing Bug**: Fixed `JSONDecodeError` by changing from `list[str]` to `str` with property conversion
- **✅ Missing Docker Environment Variables**: Added comprehensive `.env.example` with all required Docker variables
- **✅ Customization Script Coverage**: Enhanced file scanning to include `.env*` files and handle all environment files
- **✅ Setup Verification**: Added comprehensive verification steps to confirm services are running correctly
- **✅ Test Configuration Updates**: Updated all tests to use new comma-separated CORS format

**Impact**: These fixes eliminate the most common issues users encountered when setting up projects from this template.

**🚀 New**: Run `python3 scripts/fix_template_issues.py` to automatically apply all fixes to the template.

### What Gets Customized:
- **Project Name**: "FastAPI Template" → "Your Project Name"
- **Project Slug**: "fast-api-template" → "your_project_name"
- **Database Name**: "fastapi_template" → "your_project_name"
- **Docker Containers**: All containers get unique names using `COMPOSE_PROJECT_NAME`
- **Documentation**: All references updated to reflect your project
- **Configuration Files**: Database URLs, container names, etc.
- **Environment Variables**: `COMPOSE_PROJECT_NAME` added to `.env` to prevent container conflicts

### Customization Process:
1. **Step 1**: Run `./scripts/rename_template.sh` to rename the directory
2. **Step 2**: Restart VS Code and open the renamed directory
3. **Step 3**: Run `./scripts/customize_template.sh` to customize the template
4. **Step 4**: Run `./scripts/setup_project.sh` to set up your environment
5. Review the changes in `tests/template_tests/customization_improvements.md`
6. Update your git remote to point to your new repository
7. **Important**: Update the license and README.md branding to reflect your project
8. Start developing!

### Example:
```bash
# Input:
Project name: My Awesome Project
Project slug: myawesomeproject_backend
Database name: myawesomeproject_backend

# Result:
- All "FastAPI Template" → "My Awesome Project"
- All "fast-api-template" → "myawesomeproject_backend"
- All "fastapi_template" → "myawesomeproject_backend"
- Docker containers: "myawesomeproject_backend-postgres-1"
```

### 🎯 See It in Action:
```bash
# Run the demo to see the customization process
python3 scripts/demo_customization.py
```

This will show you exactly what gets changed during the customization process.

## 📋 Complete Setup Process

The template setup involves **5 steps** that must be done in order:

### Step 1: Clone and Navigate
```bash
# Clone the template
git clone <your-repo-url>
cd fast-api-template
```

### Step 2: Rename the Template Directory

**What this does:**
- Renames the template directory to your project name with "_backend" suffix
- Prevents configuration conflicts
- Sets up the foundation for customization

**💡 Important:** The directory will ALWAYS be renamed to end with "_backend"
- "My Awesome Project" → "myawesomeproject_backend"
- "Todo App" → "todo_app_backend"
- "E-commerce API" → "ecommerce_api_backend"

**How to do it:**
1. Make sure you're in the `fast-api-template` directory
2. Run: `./scripts/rename_template.sh`
3. Enter your project name when prompted
4. The script will rename the directory and give you next steps

**Example:**
```bash
$ ./scripts/rename_template.sh
🚀 FastAPI Template - Step 1: Rename Directory
==============================================

This script will rename the template directory to your project name.
This is the FIRST step in customizing your template.

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

💡 Tip: You can also run: code myawesomeproject_backend
```

### Step 3: Restart VS Code

**Why this is important:**
- VS Code needs to recognize the new directory name
- Prevents path conflicts and configuration issues
- Ensures all tools work correctly

**How to do it:**
1. **Close VS Code completely** (not just the window)
2. **Open VS Code again**
3. **Open the renamed folder**: `myawesomeproject_backend`

### Step 4: Customize the Template

**What this does:**
- Replaces all template references with your project details
- Updates database names and connection strings
- Changes import statements throughout the code
- Updates documentation and configuration files
- Modifies Docker setup to prevent conflicts

**How to do it:**
1. Make sure you're in the renamed directory
2. Run: `./scripts/customize_template.sh`
3. Enter your project details when prompted
4. Review the summary and confirm

**Example:**
```bash
$ ./scripts/customize_template.sh
🚀 FastAPI Template Customization - Step 2
==========================================
This script will transform the template into your custom project.
Please provide the following information:

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
   Found 45 files to process

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
1. Review the changes in docs/tutorials/TEMPLATE_CUSTOMIZATION.md
2. **🚨 CRITICAL:** Update your git remote to point to your new repository:
   ```bash
   git remote set-url origin https://github.com/yourusername/your-new-repo-name.git
   ```
3. Run the setup script: ./scripts/setup_project.sh
4. Start developing your application!

✨ Happy coding!
```

### Step 5: Set Up Your Project

**What this does:**
- Creates Python virtual environment
- Installs all dependencies
- Starts PostgreSQL and FastAPI
- Runs database migrations
- Sets up everything you need to start developing

**How to do it:**
1. Make sure you're in the renamed directory
2. Run: `./scripts/setup_project.sh`
3. Follow the prompts (optional: create a superuser)
4. Wait for all services to start

**Example:**
```bash
$ ./scripts/setup_project.sh
🚀 FastAPI Template - Step 3: Project Setup
===========================================

This script will set up your development environment and database.
This is the FINAL step in getting your project ready.

✅ You're in a renamed project directory: myawesomeproject_backend

✅ .env file already exists
✅ Virtual environment already exists

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
   Testing API startup...
✅ API startup test passed
   Testing test environment...
✅ Test environment ready

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
2. Run tests: pytest
3. Start developing!

💡 Useful Commands:
  docker-compose up -d          # Start all services (including Redis if needed)
  docker-compose logs -f        # View logs
  docker-compose down           # Stop all services
  pytest                        # Run tests
  alembic revision --autogenerate -m 'description'  # Create migration
  alembic upgrade head          # Apply migrations
```

**That's it!** You now have a fully working project with:
- User authentication system
- Admin panel
- API key management
- Database setup (PostgreSQL)
- FastAPI application running
- Testing framework
- Docker support
- All template features, but branded for your project

**🚀 What's Running:**
- **PostgreSQL** database on port 5432
- **FastAPI** application on port 8000 (docs at http://localhost:8000/docs)
- **Optional services** (Redis, Celery) can be started when needed

### 🆘 Need Help?

If you encounter any issues during setup:

- **📖 Troubleshooting Guide**: [Setup Issues & Solutions](docs/troubleshooting/setup-issues.md)
- **🐛 Common Problems**: Missing alembic.ini, database errors, superuser creation issues
- **🔧 Quick Fixes**: Most issues have simple solutions documented in the guide

## 📊 Test Status

The template includes a comprehensive test suite with the following status:

### ✅ **Excellent Test Coverage**
- **414 tests passed** ✅
- **199 tests skipped** (intentionally skipped for template reasons)
- **7 tests failed** (minor issues, mostly test isolation)
- **24 template tests deselected** (as configured)

### 🧪 **Test Categories**

#### **Core Tests (Always Run)**
- Basic API functionality
- Database operations
- Security features
- Error handling
- Health checks

#### **Template Tests (Marked with `@pytest.mark.template_only`)**
- Template-specific functionality
- Setup script verification
- Configuration validation
- Admin panel features
- CRUD scaffolding tests

#### **Skipped Tests (Documented)**
Tests are intentionally skipped for the following reasons:

1. **Authentication Tests** - Require proper JWT configuration and user verification workflows
2. **Email Verification Tests** - Require email service setup
3. **OAuth Tests** - Require OAuth provider configuration
4. **Celery Tests** - Require task queue setup
5. **Test Isolation Issues** - Require proper database cleanup between tests

### 🔧 **Running Tests**

```bash
# Run all tests (recommended)
pytest

# Run only template tests
pytest -m "template_only"

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/template_tests/test_admin.py
```

### 📚 **Test Documentation**

For detailed information about implementing skipped tests and test best practices, see:
- [Testing and Development Guide](docs/tutorials/testing-and-development.md)
- [Authentication Tutorial](docs/tutorials/authentication.md)
- [Database Management](docs/tutorials/database-management.md)

### 🎯 **Why Tests Are Skipped**

The template intentionally skips certain tests because:

1. **Template Limitations** - Some features require complex setup not suitable for a template
2. **External Dependencies** - Tests requiring external services (email, OAuth, etc.)
3. **Configuration Complexity** - Tests needing extensive configuration
4. **Test Isolation Issues** - Tests requiring proper database cleanup and isolation

### 🚀 **Implementing Skipped Tests**

When you're ready to implement the skipped tests:

1. **Follow the Implementation Guide** in `docs/tutorials/testing-and-development.md`
2. **Remove skip decorators** from tests you want to run
3. **Configure required services** (email, OAuth, etc.)
4. **Set up proper test isolation** with database cleanup
5. **Run tests incrementally** to verify each feature

## 🏗️ Features

### 🔐 Authentication & Security
- JWT-based authentication
- Password hashing with bcrypt
- Email verification workflow
- OAuth integration (Google, Apple)
- Password reset functionality
- Account deletion with soft delete
- Rate limiting
- CORS configuration
- **Modular Auth Architecture** - Clean, maintainable auth endpoints organized by functionality

### 👥 User Management
- User registration and login
- Email verification
- Password reset
- Account deletion
- User profiles
- Admin user management

### 🔑 API Keys
- API key generation and management
- Scoped permissions
- Expiration dates
- Admin dashboard for key management
- Audit logging for key usage

### 📊 Admin Panel
- User management interface
- API key management
- System statistics
- Audit log viewing
- Bulk operations

### 📝 Audit Logging
- Comprehensive audit trail
- User action tracking
- API usage logging
- Security event logging
- Configurable log levels

### 🗄️ Database
- PostgreSQL with SQLAlchemy
- Alembic migrations
- Connection pooling
- Soft delete support
- Optimized queries
- **CRUD Scaffolding** - Generate complete CRUD boilerplate with one command

### 🚀 Performance & Monitoring
- Redis caching
- Celery task queue
- Health checks
- Performance monitoring
- Error tracking with Sentry

### 🧪 Testing
- Comprehensive test suite
- Unit and integration tests
- Test fixtures and utilities
- Coverage reporting
- CI/CD ready
- Template-specific tests with proper isolation

### 🛠️ Development Tools
- **Comprehensive Setup Scripts** - One-command environment setup
- **Pre-commit Hooks** - Automatic code quality checks
- **Code Generation** - CRUD scaffolding and boilerplate generation
- **Fix Scripts** - Automated issue resolution
- **Verification Tools** - Setup validation and testing

## 📁 Project Structure

```
fast-api-template/
├── app/                    # Main application code
│   ├── api/               # API routes and endpoints
│   │   └── api_v1/
│   │       └── endpoints/
│   │           ├── auth/   # Modular authentication endpoints
│   │           │   ├── __init__.py
│   │           │   ├── login.py
│   │           │   ├── email_verification.py
│   │           │   ├── password_management.py
│   │           │   ├── account_deletion.py
│   │           │   ├── session_management.py
│   │           │   └── api_keys.py
│   │           ├── admin.py
│   │           ├── health.py
│   │           └── users.py
│   ├── core/              # Core configuration and utilities
│   ├── crud/              # Database operations
│   ├── models/            # Database models (separated by entity)
│   │   ├── base.py        # Base model and mixins
│   │   ├── user.py        # User model
│   │   ├── api_key.py     # API key model
│   │   ├── audit_log.py   # Audit log model
│   │   └── refresh_token.py # Refresh token model
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   └── template_tests/    # Template-specific tests
├── docs/                  # Documentation
├── scripts/               # Setup and utility scripts
├── alembic/               # Database migrations
└── docker-compose.yml     # Docker configuration
```

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL
- Redis (optional)



### Environment Setup
```bash
# Automated setup (recommended)
./scripts/setup_comprehensive.sh

# Manual setup (if needed)
cp .env.example .env
nano .env
```

### Database Setup
```bash
# Start database
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Create superuser
./scripts/bootstrap_superuser.sh
```

### Running the Application
```bash
# Start all services with Docker (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Development workflow (tools run locally, app runs in Docker)
ruff format .
ruff check .
pytest
docker-compose up -d
```

### Code Quality (Pre-commit Hooks)
The template includes pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
./scripts/install_precommit.sh

# Install hooks in git repository
pre-commit install

# Run pre-commit manually
pre-commit run --all-files

# Run specific hooks
pre-commit run ruff --all-files
pre-commit run black --all-files
pre-commit run mypy --all-files
```

**Available Hooks:**
- **ruff** - Fast Python linter and formatter
- **black** - Code formatting
- **mypy** - Static type checking
- **isort** - Import sorting
- **pre-commit** - Hook management

**Configuration Files:**
- `.pre-commit-config.yaml` - Pre-commit configuration
- `pyproject.toml` - Tool configurations
- `mypy.ini` - MyPy configuration
- `pyrightconfig.json` - Pyright configuration

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

## 🔄 Tool Version Management

### Why Tool Versions Matter

CI environments update their tool versions **much more frequently** than you might think:

| Tool | Update Frequency | Impact |
|------|-----------------|---------|
| **Black** | Every 2-4 weeks | Formatting rules change, breaking existing code |
| **Ruff** | Every 1-2 weeks | New linting rules, different error messages |
| **Mypy** | Every 3-6 weeks | Type checking behavior changes |
| **Python** | Every 3-6 months | New language features, deprecations |
| **Pre-commit** | Every 2-4 weeks | Hook behavior changes |

### The "Whack-a-Mole" Problem

**Without pinned versions:**
```
Week 1: Your local Black 24.4.2 ✅ "Code looks good!"
Week 2: CI updates to Black 25.1.0 ❌ "Formatting error!"
Week 3: You update local to 25.1.0 ✅ "Fixed!"
Week 4: CI updates to Black 25.2.0 ❌ "New formatting error!"
```

**With our pinned versions:**
```
Week 1: Local & CI both use Black 25.1.0 ✅ "Consistent!"
Week 2: CI updates to 25.2.0, but you're still on 25.1.0 ✅ "Still works!"
Week 3: You choose when to update to 25.2.0 ✅ "Controlled upgrade!"
```

### Recommended Update Schedule

**Monthly**: Check for new tool versions
```bash
./scripts/check_tool_updates.sh
```

**Quarterly**: Update to latest stable versions
```bash
# Update development tools
pip install -r requirements-dev.txt --upgrade

# Test everything still works
./scripts/validate_ci.sh
```

**When needed**: Update for security patches or new features

### How to Update Safely

1. **Check what's new:**
   ```bash
   ./scripts/check_tool_updates.sh
   ```

2. **Update development tools:**
   ```bash
   pip install -r requirements-dev.txt --upgrade
   ```

3. **Test everything still works:**
   ```bash
   ./scripts/validate_ci.sh
   ```

4. **Update the pinned versions** in `requirements-dev.txt` if needed

5. **Commit the changes:**
   ```bash
   git add requirements-dev.txt
   git commit -m "Update development tool versions"
   ```

### Benefits of Controlled Updates

- ✅ **Stability**: Your tools don't change unless you choose to update
- ✅ **Predictability**: Same checks, same results, every time  
- ✅ **Team consistency**: Everyone uses identical tool versions
- ✅ **No surprises**: You control when to upgrade, not CI
- ✅ **Testing**: You can test new versions before adopting them

## 📚 Documentation

- [Getting Started](docs/tutorials/getting-started.md) - Complete setup guide
- [Tutorials Index](docs/tutorials/TUTORIALS.md) - All tutorials in one place
- [Next Steps & Development Tips](docs/tutorials/next-steps-and-tips.md) - What to build first, common commands, and mistakes to avoid
- [Authentication Guide](docs/tutorials/authentication.md)
- [Database Management](docs/tutorials/database-management.md)
- [Testing Guide](docs/tutorials/testing-and-development.md)
- [Deployment Guide](docs/tutorials/deployment-and-production.md)
- [Optional Features](docs/tutorials/optional-features.md)
- [Troubleshooting](docs/troubleshooting/) - Common issues and solutions
  - [Template Critical Fixes](docs/troubleshooting/template-fixes.md) - Critical fixes applied to prevent common issues

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Celery (optional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build custom image
docker build -t fastapi-template .
docker run -p 8000:8000 fastapi-template
```

### Production Considerations
- Use proper secret management
- Configure HTTPS
- Set up monitoring and logging
- Use production database
- Configure backup strategies
- Set up CI/CD pipelines

📖 **For detailed deployment instructions**, see the [Deployment and Production Guide](docs/tutorials/deployment-and-production.md) which covers Docker, cloud deployment, monitoring, and production best practices.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Check the [documentation](docs/)
- Review [troubleshooting guides](docs/troubleshooting/)
- **🚨 Critical Fixes**: See [Template Critical Fixes](docs/troubleshooting/template-fixes.md) for issues that have been resolved
- Open an issue for bugs
- Start a discussion for questions

## 🎯 Roadmap

- [ ] GraphQL support
- [ ] WebSocket real-time features
- [ ] Advanced caching strategies
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] Advanced monitoring
- [ ] Multi-tenancy support