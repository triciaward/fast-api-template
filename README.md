# FastAPI Project Template

![Tests](https://img.shields.io/badge/tests-83%20passing-brightgreen)
![CI](https://github.com/triciaward/fast-api-template/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-78%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

A production-ready FastAPI backend template with built-in authentication, CI/CD, testing, type checking, and Docker support.

## Overview

A robust FastAPI project template with **hybrid async/sync architecture** optimized for both development and production. Features comprehensive testing (83 passing tests), secure authentication, PostgreSQL integration, and a fully working CI/CD pipeline.

## Features

- 🚀 FastAPI Backend with Hybrid Async/Sync Architecture
- 🔒 Secure Authentication System (JWT + bcrypt)
- 👑 Superuser Bootstrap for Easy Setup
- 📦 PostgreSQL Database Integration
- 🌐 CORS Support
- 🐳 Docker Support
- 🧪 Comprehensive Testing (83 passing tests)
- 📝 Alembic Migrations
- 🔍 Linting and Code Quality (ruff)
- ✅ Type Safety (mypy)
- 🎯 Modern Dependencies (SQLAlchemy 2.0, Pydantic V2)
- ✅ Zero Deprecation Warnings
- 🏥 Health Check Endpoints for Monitoring
- 🚀 CI/CD Pipeline (GitHub Actions)

## Project Structure

```
fast-api-template/
├── alembic/                # Database migration scripts
├── app/
│   ├── api/                # API route definitions
│   │   └── api_v1/
│   │       └── endpoints/  # Specific endpoint implementations (auth, users, health)
│   ├── core/               # Core configuration and security
│   ├── crud/               # Database CRUD operations
│   ├── database/           # Database connection and session management
│   ├── models/             # SQLAlchemy database models
│   ├── schemas/            # Pydantic validation schemas
│   └── main.py             # Application entry point
├── tests/                  # Comprehensive test suite (83 tests)
├── docker-compose.yml      # Docker composition file
├── Dockerfile              # Docker image configuration
└── requirements.txt        # Python dependencies
```

## Prerequisites

- Python 3.9+
- Docker (optional, but recommended)
- PostgreSQL

## Quick Start

1. **Clone and setup**
```bash
git clone <your-repo-url>
cd fast-api-template
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database connection, secret keys, and CORS settings
```

3. **Setup database**
```bash
# Create test database
docker exec -it fast-api-template-postgres-1 createdb -U postgres fastapi_template_test

# Run migrations
alembic upgrade head
```

4. **Bootstrap superuser (optional)**
```bash
# Set environment variables in .env file:
# FIRST_SUPERUSER=admin@example.com
# FIRST_SUPERUSER_PASSWORD=change_this_in_prod

# Or run manually:
./bootstrap_superuser.sh --email admin@example.com --password secret123
```

5. **Run the application**
```bash
uvicorn app.main:app --reload
```

## 🛠️ Recent Improvements (July 2025)

### ✅ CI/CD Pipeline Implementation
- **GitHub Actions Workflow**: Complete CI pipeline with tests, linting, and type checking
- **Automated Testing**: 83 tests run on every push/PR with PostgreSQL integration
- **Code Quality**: Automated ruff linting and mypy type checking
- **Environment Consistency**: Proper database credentials and environment variables
- **Fast Execution**: Complete pipeline runs in under 2 minutes

### ✅ Deprecation Warning Fixes
- **SQLAlchemy 2.0 Migration**: Updated `declarative_base()` import to use `sqlalchemy.orm.declarative_base()`
- **Pydantic V2 Migration**: Replaced class-based `Config` with `ConfigDict` for future compatibility
- **Zero Warnings**: All deprecation warnings eliminated, future-proof codebase

### ✅ Type Safety Enhancements
- **Full mypy compliance**: Zero type checking errors
- **Clean linting**: Zero ruff linting issues
- **Import optimization**: Properly sorted and formatted imports

### ✅ Health Check Endpoints
- **Comprehensive monitoring**: 4 health check endpoints for different use cases
- **Database connectivity**: Real-time database connection verification
- **Kubernetes ready**: Proper readiness/liveness probe endpoints
- **Production monitoring**: Ready for load balancers and uptime services

## Hybrid Async/Sync Architecture

This template separates async and sync usage to avoid conflicts during testing while preserving full async performance in production.

### Architecture Overview
- **Production:** Async SQLAlchemy with asyncpg for maximum concurrency
- **TestClient Tests:** Sync SQLAlchemy sessions to avoid event loop issues
- **Direct Async Tests:** Use true async sessions for realism
- **Isolation:** Separate engines prevent connection collisions

### Key Benefits
- **No Connection Conflicts:** Eliminated asyncpg "another operation is in progress" errors
- **Test Reliability:** 100% test success rate with proper isolation
- **Production Ready:** Full async performance for high-load scenarios
- **Development Friendly:** Fast, reliable testing with sync operations

## Testing

### Run Tests
```bash
# All tests (83 tests)
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Specific categories
pytest tests/test_api_*.py -v  # API tests
pytest tests/test_cors.py -v   # CORS tests
```

### Test Coverage Includes
- Authentication (JWT, registration, login)
- CRUD operations and models
- CORS handling
- Health check endpoints (comprehensive, simple, readiness, liveness)
- Security features and edge cases
- Full async DB operations

### Code Quality Checks
```bash
# Type checking with mypy
mypy .

# Linting with ruff
ruff check .

# Run both checks
mypy . && ruff check .
```

## CI/CD Pipeline

The project includes a comprehensive GitHub Actions CI/CD pipeline that runs on every push and pull request:

### Pipeline Jobs
- **🧪 Run Tests**: Executes all 83 tests with PostgreSQL integration
- **🔍 Lint (ruff)**: Performs code linting and format checking
- **🧠 Type Check (mypy)**: Validates type safety across the codebase

### Features
- **Automated Testing**: Full test suite with database integration
- **Code Quality**: Automated linting and type checking
- **Fast Execution**: Complete pipeline completes in under 2 minutes
- **Environment Isolation**: Proper test database setup and cleanup
- **Coverage Reporting**: Test coverage tracking and reporting

### Local Development
The CI pipeline mirrors your local development environment:
- Uses the same database credentials and configuration
- Runs the same linting and type checking tools
- Ensures consistent code quality across environments

> **Note**: CI does **not** use a `.env` file — all environment variables are passed explicitly in the workflow for full control and transparency.

## Docker Deployment

### Local Development
```bash
# Create .env.docker file with your settings
cp .env.example .env.docker

# Build and run
docker-compose --env-file .env.docker build
docker-compose --env-file .env.docker up -d
```

### Production
```bash
docker-compose --env-file .env.prod up -d --build
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## Health Check Endpoints

The application provides comprehensive health monitoring endpoints for container orchestration and uptime monitoring:

### `/api/v1/health`
**Comprehensive Health Check** - Returns detailed health status including database connectivity, application status, version, and environment information.

```json
{
  "status": "healthy",
  "timestamp": "2025-07-19T17:41:11.635810",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": "healthy",
    "application": "healthy"
  }
}
```

### `/api/v1/health/simple`
**Simple Health Check** - Lightweight endpoint for basic uptime monitoring.

```json
{
  "status": "healthy",
  "timestamp": "2025-07-19T17:41:14.030146"
}
```

### `/api/v1/health/ready`
**Readiness Probe** - Kubernetes readiness probe endpoint. Returns 503 if any component is not ready.

```json
{
  "ready": true,
  "timestamp": "2025-07-19T17:41:16.150454",
  "components": {
    "database": {
      "ready": true,
      "message": "Database connection successful"
    },
    "application": {
      "ready": true,
      "message": "Application is running"
    }
  }
}
```

### `/api/v1/health/live`
**Liveness Probe** - Kubernetes liveness probe endpoint.

```json
{
  "alive": true,
  "timestamp": "2025-07-19T17:41:18.964195"
}
```

### Use Cases
- **Container Orchestration**: Use readiness/liveness probes for Kubernetes deployments
- **Load Balancer Health Checks**: Use simple health check for load balancer monitoring
- **Monitoring Systems**: Use comprehensive health check for detailed system monitoring
- **Uptime Monitoring**: Use any endpoint for external uptime monitoring services

## CORS Configuration

Configure via `BACKEND_CORS_ORIGINS` environment variable:

```bash
# Comma-separated format (recommended)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:4200

# Production domains
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Authentication

Secure authentication system with:
- User registration and login
- JWT token-based authentication
- Password hashing with bcrypt
- Superuser bootstrap functionality

### Superuser Bootstrap

The application includes an optional superuser bootstrap feature for easy initial setup:

#### Environment Variables
Set these in your `.env` file to automatically create a superuser on startup:
```bash
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=change_this_in_prod
```

#### Manual Bootstrap
Create a superuser manually using the CLI script:
```bash
# Using the wrapper script (recommended)
./bootstrap_superuser.sh --help

# Using environment variables
./bootstrap_superuser.sh

# Using command line arguments
./bootstrap_superuser.sh --email admin@example.com --password secret123

# With custom username
./bootstrap_superuser.sh --email admin@example.com --password secret123 --username admin

# Force creation (overwrites existing user)
./bootstrap_superuser.sh --email admin@example.com --password secret123 --force

# Alternative: Using PYTHONPATH directly
PYTHONPATH=. python scripts/bootstrap_superuser.py --email admin@example.com --password secret123
```

#### Features
- **Automatic startup**: Superuser is created automatically when the app starts (if env vars are set)
- **Safety checks**: Won't create duplicate superusers
- **Flexible**: Works with environment variables or CLI arguments
- **Development friendly**: Perfect for local dev, testing, and staging environments

## Code Quality and Coverage

### Current Status
- **83 tests passing, 0 failures**
- **78% code coverage** (+9% improvement)
- **100% test success rate**
- **Zero deprecation warnings**
- **Full type safety with mypy**
- **Clean code with ruff linting**
- **Working CI/CD pipeline**

### 🛠️ Why main.py Was Previously 0% Covered

`main.py` is the FastAPI entry point, but our test suite used to create a separate test app instance. This meant the startup logic and routing in `main.py` wasn't being tested — leading to 0% coverage.

We fixed this by:
- **Importing the actual app from `main.py` in `conftest.py`**
- **Updating tests to reflect the real app's routes** (e.g., `/api/v1/health` instead of `/health`)
- **Preventing `main.py` from running async DB setup during tests**, avoiding sync/async conflicts
- **Switching to the sync SQLAlchemy engine for initial table creation** (only in dev)

Now, `main.py` shows **88% coverage**, with the remaining 12% being startup logic that intentionally doesn't run in test mode.

### Coverage Report
```
Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
app/api/api_v1/api.py                      6      0   100%
app/api/api_v1/endpoints/auth.py          27      0   100%
app/api/api_v1/endpoints/health.py        43      6    86%   34-35, 79-81, 102
app/api/api_v1/endpoints/users.py         29      2    93%   30, 36
app/bootstrap_superuser.py                53     39    26%   40-64, 72-111, 116-118, 122
app/core/config.py                        28      4    86%   45, 48-50
app/core/cors.py                          10      1    90%   23
app/core/security.py                      17      0   100%
app/crud/user.py                          87     22    75%   19, 24-28, 44-51, 56-61, 87-88, 124-125
app/database/database.py                  25      9    64%   24, 41-45, 50-54
app/main.py                               26      3    88%   24-28
app/models/models.py                      15      0   100%
app/schemas/user.py                       23      0   100%
--------------------------------------------------------------------
TOTAL                                    389     86    78%
```

### Code Quality Features
- **Type Safety**: Full mypy type checking with zero errors
- **Linting**: Ruff linting with zero issues
- **Modern Dependencies**: Updated to SQLAlchemy 2.0 and Pydantic V2 standards
- **Future-Proof**: No deprecation warnings, ready for future library updates
- **CI/CD Integration**: Automated quality checks on every commit

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Tricia Ward - badish@gmail.com

Project Link: [https://github.com/triciaward/fast-api-template](https://github.com/triciaward/fast-api-template) 