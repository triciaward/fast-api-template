# Your Project Name

Welcome to your new FastAPI project! 🎉

[![CI](https://github.com/triciaward/fast-api-template/workflows/CI/badge.svg)](https://github.com/triciaward/fast-api-template/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Test Coverage](https://img.shields.io/badge/coverage-98.2%25-brightgreen.svg)](https://github.com/triciaward/fast-api-template)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Check: MyPy](https://img.shields.io/badge/type%20check-mypy-blue.svg)](https://mypy-lang.org/)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-red.svg)](https://github.com/astral-sh/ruff)

This is your project's main README file - feel free to customize it to describe what your application does, how to use it, and any specific features you've built.

## 🚨 CRITICAL: Setup Process Must Be Followed In Order

**⚠️ IMPORTANT**: This template requires a specific setup process that MUST be followed in the exact order shown below. Do not skip steps or run commands out of order!

**🤖 For AI Assistants**: If you're helping a user set up this project, please refer to `@README.md` and `@docs/TEMPLATE_README.md` for the complete setup directions. The user MUST complete the customization steps before starting development.

## 🚀 Getting Started

**📖 Complete Setup Guide**: For detailed setup instructions, see [docs/TEMPLATE_README.md](docs/TEMPLATE_README.md)

### Step 1: Clone and Customize (Required - Must Be Done First!)

**🚨 CRITICAL**: You MUST complete these customization steps BEFORE starting development!

```bash
# Clone the template
git clone https://github.com/triciaward/fast-api-template.git
cd fast-api-template

# Step 1: Rename the template directory to your project name
./scripts/setup/rename_template.sh

# Step 2: Customize the template (updates project name, descriptions, etc.)
./scripts/setup/customize_template.sh
```

**Why this is required:**
- The template contains placeholder names and descriptions
- Customization updates all project metadata for your specific project
- This prevents confusion and makes the project truly yours
- **The quick start script will fail if you haven't customized first!**

### Step 2: Set Up Your Development Environment

**ONLY AFTER completing Step 1**, set up your development environment:

```bash
# Run the quick start script (sets up everything automatically)
./scripts/setup/quick_start.sh
```

**That's it!** Your FastAPI application is ready to use.

**🔄 Process Summary**:
1. ✅ Clone template
2. ✅ Rename directory (`./scripts/setup/rename_template.sh`)
3. ✅ Customize project (`./scripts/setup/customize_template.sh`)
4. ✅ Set up environment (`./scripts/setup/quick_start.sh`)
5. ✅ Start building!

**🆘 Need Help?**: If you encounter issues during setup, see the [Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING_README.md)

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
- Redis caching
- Celery task queue
- Comprehensive health check endpoints
- Performance monitoring utilities
- Error tracking with Sentry



### 🛠️ Development Tools
- Pre-commit hooks for code quality
- Code generation and CRUD scaffolding
- Automated setup scripts
- Fix scripts for common issues
- Verification tools

## 📚 Documentation

### 🚀 Getting Started
- **[Complete Setup Guide](docs/TEMPLATE_README.md)** - Detailed setup instructions and project overview
- **[Next Steps & Development Tips](docs/tutorials/next-steps-and-tips.md)** - What to build first

### 🛠️ Development Guides
- **[Authentication Guide](docs/tutorials/authentication.md)** - User auth and security
- **[Database Management](docs/tutorials/database-management.md)** - Database operations

- **[Deployment Guide](docs/tutorials/deployment-and-production.md)** - Production deployment
- **[Cost Optimization](docs/tutorials/cost-optimization.md)** - Deploy on a budget ($10-15/month)

### 🔧 Troubleshooting
- **[Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING_README.md)** - Common issues and solutions
- **[Environment & Setup Issues](docs/troubleshooting/environment-setup/ENVIRONMENT_SETUP_README.md)** - Setup problems

- **[Development Workflow Issues](docs/troubleshooting/development-workflow/DEVELOPMENT_WORKFLOW_README.md)** - Workflow problems
- **[Code Quality Issues](docs/troubleshooting/code-quality/CODE_QUALITY_README.md)** - Code quality problems

### 📖 All Documentation
- **[Tutorials Index](docs/tutorials/TUTORIALS.md)** - All tutorials in one place
- **[Template Assessment](docs/tutorials/template-audit.md)** - Architecture evaluation and production readiness
- **[Optional Features](docs/tutorials/optional-features.md)** - Advanced features

## 🎯 Quick Commands

```bash
# Start the application
docker-compose up -d

# View API documentation
open http://localhost:8000/docs



# Check code quality
./scripts/development/validate_ci.sh
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
