# FastAPI Project Template

![Tests](https://img.shields.io/badge/tests-323%20tests%20passing-brightgreen)
![CI](https://github.com/triciaward/fast-api-template/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-70%25-brightgreen)
![Linting](https://img.shields.io/badge/linting-0%20errors-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

A production-ready FastAPI backend template with comprehensive authentication, testing, CI/CD, and enterprise features. **323 tests passing, 156 skipped for complex features.**

## 📋 Table of Contents

- [Overview](#overview)
- [🚀 Quick Start](#-quick-start)
- [🏗️ Architecture](#️-architecture)
- [🔧 Core Features](#-core-features)
- [⚡ Optional Features](#-optional-features)
- [📊 Test Suite](#-test-suite)
- [🚀 Live Examples](#-live-examples)
- [📁 Project Structure](#-project-structure)
- [🔐 Authentication & Security](#-authentication--security)
- [📄 API Documentation](#-api-documentation)
- [🐳 Docker & Deployment](#-docker--deployment)
- [🛠️ Development](#️-development)
- [📈 Monitoring & Logging](#-monitoring--logging)
- [🤝 Contributing](#-contributing)

## Overview

A robust FastAPI project template with **hybrid async/sync architecture** optimized for both development and production. Features comprehensive testing (323 tests passing), secure authentication with email verification, OAuth, and password reset, comprehensive input validation, PostgreSQL integration, and a fully working CI/CD pipeline.

### 🎯 **Core Features**
- **Authentication**: JWT + bcrypt + Email Verification + OAuth + Password Reset
- **Security**: GDPR-compliant account deletion, refresh token management, audit logging
- **Database**: PostgreSQL with Alembic migrations, soft delete, search & filtering
- **Testing**: 323 tests passing, comprehensive coverage, CI/CD pipeline
- **Quality**: Type safety (mypy), linting (ruff), pre-commit hooks
- **Monitoring**: Health checks, structured logging, rate limiting

### 🚀 **Optional Features**
- **Redis**: Caching, sessions, rate limiting backend
- **WebSocket**: Real-time communication with room support
- **Celery**: Background task processing with eager mode testing
- **Advanced Monitoring**: ELK stack ready logging

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Docker (optional)

### Installation
```bash
# Clone the repository
git clone https://github.com/triciaward/fast-api-template.git
cd fast-api-template

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Docker Quick Start
```bash
# Start all services
docker-compose up -d

# Access the API
curl http://localhost:8000/health
```

## 🏗️ Architecture

### Hybrid Async/Sync Design
- **Production**: Fully async for maximum performance
- **Testing**: Sync mode for simpler test writing
- **Database**: SQLAlchemy 2.0 with async support
- **Validation**: Pydantic V2 with comprehensive schemas

### Project Structure
```
app/
├── api/              # API endpoints and routing
├── core/             # Configuration, security, error handling
├── crud/             # Database operations
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business logic and external services
└── utils/            # Utility functions
```

## 🔧 Core Features

### 🔐 Authentication System
- **JWT Tokens**: Secure token-based authentication
- **Email Verification**: Complete email verification workflow
- **OAuth Integration**: Google and Apple OAuth support
- **Password Management**: Reset, change, and strength validation
- **GDPR Compliance**: Account deletion with grace period
- **Session Management**: Refresh tokens with multi-device support

### 🗄️ Database & Data Management
- **PostgreSQL**: Primary database with proper indexing
- **Alembic Migrations**: Version-controlled schema changes
- **Soft Delete**: Comprehensive soft delete with restoration
- **Search & Filter**: Advanced text search and field filtering
- **Pagination**: Type-safe pagination with HATEOAS links
- **Audit Logging**: Complete user activity tracking

### 🛡️ Security & Validation
- **Input Validation**: SQL injection protection, XSS prevention
- **Rate Limiting**: Configurable per-endpoint rate limiting
- **CORS**: Configurable cross-origin resource sharing
- **Error Handling**: Standardized error responses with codes
- **Type Safety**: Complete mypy type checking

## ⚡ Optional Features

### 🎯 Redis Integration
- **Caching**: Response caching for improved performance
- **Sessions**: User session management
- **Rate Limiting**: Redis-backed rate limiting
- **Health Checks**: Redis connection monitoring

### 🌐 WebSocket Support
- **Real-time Communication**: WebSocket endpoints
- **Room Management**: Multi-room chat functionality
- **Connection Handling**: Proper connection lifecycle management
- **Testing**: Comprehensive WebSocket testing

### 🔄 Background Tasks
- **Celery Integration**: Asynchronous task processing
- **Task Management**: Submit, monitor, and cancel tasks
- **Eager Mode**: Synchronous execution during testing
- **Health Integration**: Task status in health checks

## 📊 Test Suite

- **323 Core Tests**: All passing with comprehensive coverage
- **156 Skipped Tests**: Complex features (OAuth, account deletion, etc.)
- **14 Pre-commit Tests**: Configuration and installation validation
- **70% Code Coverage**: Proper async testing with fixtures
- **100% Optional Features**: Complete coverage when enabled

### Test Categories
- **Authentication**: Login, registration, password management
- **API Endpoints**: CRUD operations, validation, error handling
- **Database**: Models, migrations, soft delete operations
- **Security**: Input validation, rate limiting, CORS
- **Services**: Email, Redis, WebSocket, background tasks

## 🚀 Live Examples

This template powers several production applications:

- **[Thirdly](https://github.com/triciaward/thirdly)** - News aggregation and analysis platform
- **[Truth Showdown](https://github.com/triciaward/truth-showdown)** - AI-powered debate game with real-time multiplayer

## 📁 Project Structure

```
fast-api-template/
├── app/                          # Main application code
│   ├── api/                      # API endpoints
│   │   └── api_v1/
│   │       └── endpoints/        # Route handlers
│   ├── core/                     # Core configuration
│   ├── crud/                     # Database operations
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Business logic
│   └── utils/                    # Utility functions
├── alembic/                      # Database migrations
├── tests/                        # Test suite
├── scripts/                      # Utility scripts
├── docker-compose.yml           # Docker services
├── Dockerfile                   # Application container
└── requirements.txt             # Python dependencies
```

## 🔐 Authentication & Security

### Standardized Error Responses
All API endpoints return consistent error formats:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid email format",
    "code": "INVALID_EMAIL",
    "details": {}
  }
}
```

### Security Features
- **JWT Token Management**: Secure token generation and validation
- **Password Security**: bcrypt hashing with strength validation
- **Rate Limiting**: Configurable per-endpoint limits
- **Input Sanitization**: SQL injection and XSS protection
- **Audit Logging**: Complete security event tracking

## 📄 API Documentation

### Interactive Documentation
- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`

### Key Endpoints
- **Health**: `/health`, `/health/simple`, `/health/ready`, `/health/live`
- **Authentication**: `/api/v1/auth/login`, `/api/v1/auth/register`
- **Users**: `/api/v1/users/` (CRUD operations)
- **Admin**: `/api/v1/admin/` (Admin-only operations)

## 🐳 Docker & Deployment

### Docker Services
```yaml
services:
  app:          # FastAPI application
  postgres:     # PostgreSQL database
  redis:        # Redis cache (optional)
  celery:       # Background tasks (optional)
```

### Production Deployment
- **Environment Variables**: Comprehensive configuration
- **Health Checks**: Application and service monitoring
- **Logging**: Structured JSON logging
- **Security**: Proper container security practices

## 🛠️ Development

### Code Quality
- **Pre-commit Hooks**: Automated linting and type checking
- **mypy**: Static type checking with zero errors
- **ruff**: Fast Python linter with zero warnings
- **black**: Code formatting

### Development Workflow
```bash
# Install pre-commit hooks
./scripts/install_precommit.sh

# Run tests
pytest

# Run linting
./scripts/lint.sh

# Format code
black .
```

### Utility Scripts
- **Bootstrap Admin**: `./scripts/bootstrap_admin.py`
- **Logging Demo**: `./scripts/logging_demo.py`
- **Database Setup**: `./scripts/setup.sh`

## 📈 Monitoring & Logging

### Structured Logging
- **JSON Format**: Machine-readable logs
- **Console Output**: Colored human-readable logs
- **File Rotation**: Automatic log file management
- **ELK Ready**: Compatible with ELK stack

### Health Monitoring
- **Application Health**: `/health` - Comprehensive status
- **Simple Health**: `/health/simple` - Basic status
- **Readiness**: `/health/ready` - Service readiness
- **Liveness**: `/health/live` - Application liveness

### Audit Logging
- **User Actions**: Complete activity tracking
- **Security Events**: Authentication and authorization events
- **System Events**: Background tasks and health checks
- **Database Storage**: Persistent audit trail

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type annotations for all functions
- Write comprehensive tests
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- **GitHub**: [@triciaward](https://github.com/triciaward)
- **Issues**: [GitHub Issues](https://github.com/triciaward/fast-api-template/issues)
- **Discussions**: [GitHub Discussions](https://github.com/triciaward/fast-api-template/discussions)