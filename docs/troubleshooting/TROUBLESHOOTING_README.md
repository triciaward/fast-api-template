# Troubleshooting Guide Index

This directory contains detailed troubleshooting guides for common issues you might encounter when using the FastAPI template.

## 🎯 Current Status

The troubleshooting documentation has been **reorganized and updated** to focus on **current, relevant issues**:

- ✅ **Current Issues**: Only active problems and solutions
- ✅ **Archived History**: Resolved issues moved to archive folders
- ✅ **Updated Information**: Test counts and strategies reflect current state
- ✅ **Clean Structure**: Easy to find relevant troubleshooting guidance

## 📋 Available Guides

### 🔧 Environment & Setup Issues
- **[Environment & Setup](./environment-setup/ENVIRONMENT_SETUP_README.md)** - Environment configuration and project setup
  - Environment variable issues and solutions
  - Database connection problems
  - Template customization workflow
  - Setup script improvements and fixes

### 🧪 Testing & CI Issues  

  - Async test strategies and isolation
  - CI validation workflow and tool versions
  - Test execution and coverage approaches
  - Development environment setup

### 🔄 Development Workflow Issues
- **[Development Workflow](./development-workflow/DEVELOPMENT_WORKFLOW_README.md)** - Development workflow and authentication
  - AI assistant workflow guidance
  - Authentication system modularization
  - API keys dashboard access
  - Template customization procedures

### 🎨 Code Quality Issues
- **[Code Quality](./code-quality/CODE_QUALITY_README.md)** - Code quality, formatting, and dependencies
  - Bcrypt warning explanations
  - Black vs Mypy type conflicts
  - Code formatting and linting issues
  - Dependency compatibility problems



## 🚀 Quick Solutions

### Environment & Setup Issues
```bash
# Fix environment variables
./scripts/fix_env_issues.sh

# Check .env file
ls -la | grep -E "\.env"
cat .env

# Test database connection
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"
```

### Testing & CI Issues
```bash
# Run validation before pushing
./scripts/development/validate_ci.sh

# Run tests locally

```

### Development Workflow Issues
```bash
# Template customization workflow
./scripts/rename_template.sh
# Restart VS Code (CRITICAL!)
./scripts/customize_template.sh
./scripts/setup_project.sh
```

### Code Quality Issues
```bash
# Fix formatting
python -m black .

# Fix linting
python -m ruff check . --fix

# Check types
python -m mypy app/ scripts/
```

## 🛠️ Diagnostic Commands

### Environment Check
```bash
# Check .env file
ls -la | grep -E "\.env"
grep -E "^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|DATABASE_URL|SECRET_KEY)=" .env

# Test Docker Compose
docker-compose config

# Check services
docker-compose ps
```

### API Health Check
```bash
# Test API health
curl http://localhost:8000/api/v1/health

# Check logs
docker-compose logs api
docker-compose logs postgres
```

### Database Check
```bash
# Test database connection
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"

# Check Alembic
alembic current
```

## 📚 Archive

### Historical Documents
- **[Historical Fixes Index](./archive/historical-fixes/historical-fixes-index.md)** - Resolved issues and completed fixes
- **[Completed Improvements Index](./archive/completed-improvements/completed-improvements-index.md)** - Implemented features and enhancements

These archives contain documentation for issues that have been completely resolved and improvements that are now standard features of the template.

## 📞 Getting Help

If you can't find a solution in these guides:

1. **Check the main README** - [Troubleshooting section](../../README.md#troubleshooting)
2. **Review the getting started guide** - [Getting Started](../tutorials/getting-started.md)
3. **Run diagnostic scripts**:
   ```bash
   ./scripts/fix_env_issues.sh
   python scripts/verify_setup.py
   ```
4. **Open an issue** in the repository with:
   - Your operating system
   - Docker version
   - Python version
   - Complete error messages
   - Output from diagnostic commands

## 🔄 Recent Updates

**July 2025:**
- ✅ Added comprehensive environment issues guide
- ✅ Enhanced troubleshooting documentation
- ✅ Added automated fix scripts
- ✅ Improved diagnostic commands
- ✅ Better hidden file explanations
- ✅ **CRITICAL**: Fixed CORS environment variable parsing bugs
- ✅ **CRITICAL**: Added comprehensive Docker environment variables
- ✅ **CRITICAL**: Enhanced customization script coverage
- ✅ **CRITICAL**: Added setup verification steps
- ✅ **CRITICAL**: Updated test configuration for new CORS format

**Current Status:**
- ✅ **CRITICAL**: Phase-based async test execution strategy implemented
- ✅ **CRITICAL**: Individual test isolation prevents connection conflicts
- ✅ **CRITICAL**: Comprehensive CI coverage with strategic batching
- ✅ **CRITICAL**: Database isolation with separate engines
- ✅ **CRITICAL**: Reliable test execution through optimized strategy

**📋 For detailed information about these critical fixes**, see the archived documents in [Historical Fixes](./archive/historical-fixes/historical-fixes-index.md). 