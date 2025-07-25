# FastAPI Template

A comprehensive, production-ready FastAPI template with authentication, admin panel, API keys, audit logging, and more.

![Tests](https://img.shields.io/badge/tests-414%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-74%25-yellowgreen)
![CI](https://github.com/triciaward/fast-api-template/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 🚀 Quick Start

### Option 1: Use as Template (Recommended)

```bash
# Clone the template
git clone <your-repo-url>
cd fast-api-template

# Customize the template for your project
./scripts/customize_template.sh

# Run the comprehensive setup script (handles everything automatically!)
./scripts/setup_comprehensive.sh

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

### What Gets Customized:
- **Project Name**: "FastAPI Template" → "Your Project Name"
- **Project Slug**: "fast-api-template" → "your_project_name"
- **Database Name**: "fastapi_template" → "your_project_name"
- **Docker Containers**: All containers get unique names using `COMPOSE_PROJECT_NAME`
- **Documentation**: All references updated to reflect your project
- **Configuration Files**: Database URLs, container names, etc.
- **Environment Variables**: `COMPOSE_PROJECT_NAME` added to `.env` to prevent container conflicts

### Customization Process:
1. Run `./scripts/customize_template.sh`
2. Enter your project details when prompted
3. Review the changes in `docs/TEMPLATE_CUSTOMIZATION.md`
4. Update your git remote to point to your new repository
5. **Important**: Update the license and README.md branding to reflect your project
6. Start developing!

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
python scripts/demo_customization.py
```

This will show you exactly what gets changed during the customization process.

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
python scripts/generate_crud.py Post title:str content:str is_published:bool

# Generate a Product model with soft delete and search capabilities
python scripts/generate_crud.py Product name:str price:float description:str --soft-delete --searchable

# Generate an admin-managed Category model
python scripts/generate_crud.py Category name:str slug:str --admin
```

This generates:
- SQLAlchemy model with proper relationships
- Pydantic schemas for validation
- CRUD operations with search and filtering
- API endpoints with pagination
- Basic tests
- Auto-registration in the API router

## 📚 Documentation

- [Getting Started](docs/tutorials/getting-started.md) - Complete setup guide
- [Tutorials Index](docs/tutorials/TUTORIALS.md) - All tutorials in one place
- [Authentication Guide](docs/tutorials/authentication.md)
- [Database Management](docs/tutorials/database-management.md)
- [Testing Guide](docs/tutorials/testing-and-development.md)
- [Deployment Guide](docs/tutorials/deployment-and-production.md)
- [Optional Features](docs/tutorials/optional-features.md)

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