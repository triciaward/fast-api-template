# 🚀 FastAPI Template for Solo Developers

**The perfect starter for building your own projects that can scale. Built for vibe-coding with AI.**

[![CI](https://github.com/triciaward/fast-api-template/workflows/CI/badge.svg)](https://github.com/triciaward/fast-api-template/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-green.svg)](https://fastapi.tiangolo.com/)
[![Test Coverage](https://img.shields.io/badge/coverage-98.2%25-brightgreen.svg)](https://github.com/triciaward/fast-api-template)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Check: MyPy](https://img.shields.io/badge/type%20check-mypy-blue.svg)](https://mypy-lang.org/)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-red.svg)](https://github.com/astral-sh/ruff)


**🎯 Perfect for:** Solo developers building their own projects, side hustles, and apps that might grow into something bigger.

**⚡ What makes this special:** Everything you need to build cool stuff, with room to grow. No over-engineering, just solid foundations for your ideas.

**🤖 AI-Optimized:** Built-in `.cursorrules` for efficient AI assistant interactions and beginner-friendly explanations.
**🤖 Agent Setup Guide:** `docs/tutorials/agent_setup.md` ensures AI agents work correctly with your project environment.

## 🚀 Getting Started

**🎯 STREAMLINED SETUP** - One command does everything!

> **⚠️ For Users with AI Assistants**: The setup script must be run by YOU personally, not by your AI assistant. See the setup instructions below for details.

### 📋 Prerequisites

Before you start, make sure you have:

- **Python 3.11+** installed on your system
- **Docker Desktop** installed (the setup script will help you start it if needed)
- **Git** (for cloning the repository)

**💡 Don't have Python?** Download it from [python.org](https://www.python.org/downloads/)

**💡 Don't have Docker?** Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Quick Setup (GitHub Template)

**🎯 RECOMMENDED APPROACH** - Use GitHub's template feature:

```bash
# 1. Click "Use this template" button above to create your repo
# 2. Clone YOUR new repository
git clone https://github.com/yourusername/your-project-name.git
cd your-project-name

# 3. Run the setup script (IMPORTANT: You must do this personally!)
./scripts/setup/setup_project.py
```

> **🚨 IMPORTANT**: You **must run the setup script yourself** in your terminal!
> 
> **❌ Do NOT ask AI assistants** (like Claude, ChatGPT, Cursor AI, etc.) to run this script
> 
> **✅ Instead**: Open your terminal and run `./scripts/setup/setup_project.py` directly
>
> **Why?** The script requires personal input to customize your project details and has built-in protections against automation.

**That's it!** The script will automatically:
- ✅ Customize all files with your project details
- ✅ Set up Python environment and dependencies
- ✅ Start database services
- ✅ Run migrations and create superuser
- ✅ Install git protection hooks
- ✅ Verify everything works

### 🔍 Verify It's Working (v1.1.1)

```bash
# Check the API is running
curl http://localhost:8000/system/health
# Expected: {"status": "healthy", "timestamp": "..."}

# View the interactive API docs
open http://localhost:8000/docs

# Run the test suite
pytest
# Expected: 173 files, 561 passed, 98% coverage
```

> Docs page tip: If `/docs` appears blank, just refresh once after startup. The template ships with a custom docs page and a relaxed CSP for docs only. If your network blocks CDNs, allowlist `unpkg.com` and `cdnjs.cloudflare.com` or serve Swagger UI assets locally.

### What You Get
The setup script creates a **fully working API** with all the features you need to build cool stuff. You'll be coding in minutes, not hours.

**📖 Complete Setup Guide**: For detailed information, see [docs/TEMPLATE_README.md](docs/TEMPLATE_README.md)

**🆘 Need Help?**: If you encounter issues, see the [Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING_README.md)

### 🤖 AI Assistant Users - READ THIS!

If you're using AI assistants (Claude, ChatGPT, Cursor AI, etc.), they might offer to run the setup script for you. **Don't let them!**

**❌ What will happen if AI tries to run it:**
```
❌ This script requires interactive mode.
   You must run this script directly in a terminal.
   Automated/non-interactive execution is not supported.
```

**✅ What you should do instead:**
1. Open your terminal application (Terminal on Mac, Command Prompt on Windows)
2. Navigate to your project folder: `cd your-project-name`
3. Run the script yourself: `./scripts/setup/setup_project.py`
4. Answer the questions personally to customize your project

**💡 Why this matters:** The setup script customizes your project with your personal details (project name, author info, database settings). This requires human input and thoughtful answers!

## 🏆 Why This Template?

### 🚀 **Solid Foundation to Build On**
- **173 test files** with 98.2% coverage - everything works
- **Clean architecture** that grows with your project
- **Async-first design** for good performance
- **Type-safe** with full MyPy integration
- **Code quality** tools (Black, Ruff) keep things clean

### 🔐 **User Authentication & Security**
- **JWT authentication** with refresh tokens
- **OAuth integration** (Google, Apple) ready to configure
- **Rate limiting** to prevent abuse
- **Security headers** automatically applied
- **Password reset** and email verification workflows
- **Soft delete** with audit trails
- **API key management** for your users
  - Sensitive system endpoints protected by scoped API keys (`system:read`, `tasks:read`, `tasks:write`)

### 🗄️ **Database & Data Management**
- **PostgreSQL** with async operations
- **Alembic migrations** for schema changes
- **Connection pooling** for good performance
- **Search and filtering** utilities built-in
- **Audit logging** for tracking changes

### 📊 **Admin & Monitoring**
- **Admin dashboard** for managing users and API keys
- **8 health check endpoints** for monitoring
- **Performance monitoring** with query analysis
- **Error tracking** ready for Sentry integration
- **Bulk operations** for managing lots of data

### ⚡ **Optional Features for Scaling**
- **Redis caching** for faster performance
- **WebSockets** for real-time features
- **Celery background tasks** for heavy processing
- **Email service** for notifications
- **Admin CLI** for terminal management

## 🛠️ What's Included

This FastAPI template gives you everything you need to build cool projects:

### 🔐 Authentication & Security
- **JWT-based authentication** with modular architecture
- **Password hashing** with bcrypt
- **Email verification workflow** with templates
- **OAuth integration** (Google, Apple) ready to configure
- **Password reset functionality** with secure tokens
- **Account deletion** with soft delete and audit trails
- **Rate limiting** to prevent abuse
- **Security headers** automatically applied

### 👥 User Management
- **User registration and login** with validation
- **Email verification** and password reset workflows
- **Account deletion** with audit trails
- **User profiles** and admin management interface
- **Bulk user operations** for managing lots of users

### 🔑 API Keys & Access Control
- **API key generation** and management with scoped permissions
- **Expiration dates** and usage tracking
- **Admin dashboard** for key management
- **Audit logging** for tracking usage
- **Role-based access control** ready to implement

### 📊 Admin Panel & Monitoring
- **Admin dashboard** for user and API key management
- **System statistics** and audit log viewing
- **Bulk operations** for managing lots of data
- **8 health check endpoints** for monitoring
- **Performance monitoring** with query analysis
- **Error tracking** ready for Sentry integration

### 🗄️ Database & Data Management
- **PostgreSQL** with async SQLAlchemy operations
- **Alembic migrations** for schema changes
- **Connection pooling** for good performance
- **Search and filtering** utilities built-in
- **Soft delete support** with audit trails
- **Pagination** and sorting utilities

### 🐳 Docker & Infrastructure
- **Docker Compose** setup for development
- **PostgreSQL container** with persistent data
- **Redis container** for caching (optional)
- **Celery worker** for background tasks (optional)
- **Health checks** for monitoring
- **Environment-based configuration** management

### 🚀 Performance & Scaling
- **Redis caching** for faster performance
- **Celery task queue** for heavy background processing
- **WebSockets** for real-time features
- **Async database operations** for good concurrency
- **Connection pooling** for efficient resource usage
- **Performance monitoring** with query analysis

### 🛠️ Development & Testing
- **173 test files** with 98.2% coverage
- **Pre-commit hooks** for code quality
- **Automated setup scripts** for easy onboarding
- **Fix scripts** for common issues
- **Verification tools** for deployment confidence
- **Type safety** with full MyPy integration
- **AI-optimized development** with `.cursorrules` for efficient AI interactions

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

## 🤖 AI Development Features

### **Optimized for AI Assistants**
- **`.cursorrules` configuration** for efficient token usage
- **Beginner-friendly explanations** with ELI5-style breakdowns
- **FastAPI-specific optimizations** for development workflows
- **Reduced AI costs** while maintaining educational value

### **How It Works**
The template includes pre-configured Cursor rules that:
- **Minimize token usage** by 60%+ compared to default settings
- **Provide educational context** for FastAPI concepts
- **Cache project context** for faster AI responses
- **Use simple analogies** to explain complex topics

## 🧪 Test Coverage

### **Everything is Tested**
- **173 test files** with **98.2% coverage**
- **561 passing tests** covering all core functionality
- **10 optional feature tests** (skipped by default, can be enabled)

### **Optional Features**
The template includes tests for optional features that you can enable when you need them:

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
