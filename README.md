# 🚀 Production-Ready FastAPI Template

**The ultimate FastAPI starter that gets you from zero to production in minutes, not hours.**

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

**🎯 Perfect for:** Solo developers, startups, and teams building production APIs with authentication, admin panels, and enterprise features.

**⚡ What makes this special:** Built by a developer who actually ships production apps. Every feature is battle-tested, well-documented, and ready for real-world use.

## 🚀 Getting Started

**🎯 STREAMLINED SETUP** - One command does everything!

### Quick Setup (GitHub Template)

**🎯 RECOMMENDED APPROACH** - Use GitHub's template feature:

```bash
# 1. Click "Use this template" button above to create your repo
# 2. Clone YOUR new repository
git clone https://github.com/yourusername/your-project-name.git
cd your-project-name

# 3. Run the setup script
./scripts/setup/setup_project.py
```

**That's it!** The script will automatically:
- ✅ Customize all files with your project details
- ✅ Set up Python environment and dependencies
- ✅ Start database services
- ✅ Run migrations and create superuser
- ✅ Install git protection hooks
- ✅ Verify everything works

### What You Get
The setup script creates a **fully working production API** with enterprise-grade features. You'll be coding in minutes, not hours.

**📖 Complete Setup Guide**: For detailed information, see [docs/TEMPLATE_README.md](docs/TEMPLATE_README.md)

**🆘 Need Help?**: If you encounter issues, see the [Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING_README.md)

## 🏆 Why This Template?

### 🚀 **Production-Ready Out of the Box**
- **173 test files** with 98.2% coverage - everything is tested
- **Domain-based architecture** that scales with your business
- **Async-first design** for high performance
- **Type-safe** with full MyPy integration
- **Code quality** enforced with Black, Ruff, and pre-commit hooks

### 🔐 **Enterprise Security Features**
- **JWT authentication** with refresh tokens
- **OAuth integration** (Google, Apple) ready to configure
- **Rate limiting** to prevent abuse
- **Security headers** (CORS, CSP, HSTS) automatically applied
- **Password reset** and email verification workflows
- **Soft delete** with audit trails
- **API key management** with scoped permissions

### 🗄️ **Database Excellence**
- **PostgreSQL** with async SQLAlchemy operations
- **Alembic migrations** for schema management
- **Connection pooling** for optimal performance
- **Search and filtering** utilities built-in
- **Audit logging** for compliance requirements

### 📊 **Admin & Monitoring**
- **Admin dashboard** for user and API key management
- **8 health check endpoints** for load balancers and Kubernetes
- **Performance monitoring** with query analysis
- **Error tracking** ready for Sentry integration
- **Bulk operations** for efficient management

### ⚡ **Optional Enterprise Features**
- **Redis caching** for blazing-fast performance
- **WebSockets** for real-time features
- **Celery background tasks** for heavy processing
- **Email service** for automated notifications
- **Admin CLI** for terminal-based management

## 🛠️ What's Included

This FastAPI template provides a **comprehensive foundation** for building production-ready APIs:

### 🔐 Authentication & Security
- **JWT-based authentication** with modular architecture
- **Password hashing** with bcrypt (industry standard)
- **Email verification workflow** with templates
- **OAuth integration** (Google, Apple) ready to configure
- **Password reset functionality** with secure tokens
- **Account deletion** with soft delete and audit trails
- **Rate limiting** to prevent abuse and DDoS attacks
- **Enhanced security headers** (CORS, CSP, HSTS) automatically applied

### 👥 User Management
- **User registration and login** with validation
- **Email verification** and password reset workflows
- **Account deletion** with audit trails for compliance
- **User profiles** and admin management interface
- **Bulk user operations** for efficient management

### 🔑 API Keys & Access Control
- **API key generation** and management with scoped permissions
- **Expiration dates** and usage tracking
- **Admin dashboard** for key management
- **Audit logging** for compliance and security monitoring
- **Role-based access control** ready to implement

### 📊 Admin Panel & Monitoring
- **Admin dashboard** for user and API key management
- **System statistics** and audit log viewing
- **Bulk operations** for efficient management
- **8 health check endpoints** for load balancers and Kubernetes
- **Performance monitoring** with query analysis
- **Error tracking** ready for Sentry integration

### 🗄️ Database & Data Management
- **PostgreSQL** with async SQLAlchemy operations
- **Alembic migrations** for schema management
- **Connection pooling** for optimal performance
- **Search and filtering** utilities built-in
- **Soft delete support** with audit trails
- **Pagination** and sorting utilities

### 🐳 Docker & Infrastructure
- **Docker Compose** setup for development and production
- **PostgreSQL container** with persistent data
- **Redis container** for caching (optional)
- **Celery worker** for background tasks (optional)
- **Health checks** for container orchestration
- **Environment-based configuration** management

### 🚀 Performance & Scalability
- **Redis caching** for blazing-fast performance
- **Celery task queue** for heavy background processing
- **WebSockets** for real-time features
- **Async database operations** for high concurrency
- **Connection pooling** for optimal resource usage
- **Performance monitoring** with query analysis

### 🛠️ Development & Testing
- **173 test files** with 98.2% coverage
- **Pre-commit hooks** for code quality
- **Automated setup scripts** for easy onboarding
- **Fix scripts** for common issues
- **Verification tools** for deployment confidence
- **Type safety** with full MyPy integration

## 📚 Documentation

### 🚀 Getting Started
- **[Complete Setup Guide](docs/TEMPLATE_README.md)** - Detailed setup instructions and project overview
- **[Next Steps & Development Tips](docs/tutorials/next-steps-and-tips.md)** - What to build first

### 🛠️ Development Guides
- **[Authentication Guide](docs/tutorials/authentication.md)** - User auth and security
- **[Database Management](docs/tutorials/database-management.md)** - Database operations
- **[Deployment Guide](docs/tutorials/deployment-and-production.md)** - Production deployment
- **[Cost Optimization](docs/tutorials/cost-optimization.md)** - Deploy on a budget ($10-15/month)

### ⚡ Optional Features
- **[Optional Features Guide](docs/tutorials/optional-features.md)** - Redis, WebSockets, Celery, Email
- **[Health Monitoring](docs/tutorials/health-monitoring.md)** - 8 health check endpoints
- **[Performance Optimization](docs/tutorials/performance-optimization.md)** - Monitoring and optimization

### 🔧 Troubleshooting
- **[Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING_README.md)** - Common issues and solutions
- **[Environment & Setup Issues](docs/troubleshooting/environment-setup/ENVIRONMENT_SETUP_README.md)** - Setup problems
- **[Development Workflow Issues](docs/troubleshooting/development-workflow/DEVELOPMENT_WORKFLOW_README.md)** - Workflow problems
- **[Code Quality Issues](docs/troubleshooting/code-quality/CODE_QUALITY_README.md)** - Code quality problems

### 📖 All Documentation
- **[Tutorials Index](docs/tutorials/TUTORIALS.md)** - All tutorials in one place
- **[Template Assessment](docs/tutorials/template-audit.md)** - Architecture evaluation and production readiness

## 🧪 Test Coverage

### **Comprehensive Testing**
- **173 test files** with **98.2% coverage**
- **561 passing tests** covering all core functionality
- **10 optional feature tests** (skipped by default, can be enabled)

### **Optional Feature Tests**
The template includes tests for optional features that can be enabled when you need them:

| Feature | Tests | Enable With | Use Case |
|---------|-------|-------------|----------|
| **Rate Limiting** | 4 tests | `ENABLE_RATE_LIMITING=true` | Prevent API abuse |
| **WebSockets** | 4 tests | `ENABLE_WEBSOCKETS=true` | Real-time features |
| **Celery** | 1 test | `ENABLE_CELERY=true` | Background tasks |
| **Sentry** | 1 test | `ENABLE_SENTRY=true` | Error tracking |

**To run all tests including optional features:**
```bash
# Enable all optional features
ENABLE_RATE_LIMITING=true ENABLE_WEBSOCKETS=true ENABLE_CELERY=true ENABLE_SENTRY=true pytest

# Or run specific feature tests
ENABLE_WEBSOCKETS=true pytest tests/api/integrations/test_websockets.py
```

## 🎯 Quick Commands

```bash
# Start the application
docker-compose up -d

# View API documentation
open http://localhost:8000/docs

# Run tests
pytest

# Check code quality
./scripts/development/validate_ci.sh

# Start with optional features
docker-compose up -d redis  # Add Redis for caching
ENABLE_WEBSOCKETS=true docker-compose up -d  # Enable WebSockets

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

## 🤝 Contributing

This is your project! Feel free to:
- Add new features
- Modify existing code
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Happy coding! 🚀**

*This project was created using a FastAPI template. For template-specific information, see the `docs/` folder.*
