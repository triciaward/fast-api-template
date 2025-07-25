# Troubleshooting Guide Index

This directory contains detailed troubleshooting guides for common issues you might encounter when using the FastAPI template.

## 📋 Available Guides

### 🔧 Environment & Configuration Issues
- **[Environment Issues](./environment-issues.md)** - Common environment variable and configuration problems
  - Hidden `.env` file issues
  - Environment variables not loading
  - Database connection problems
  - Alembic configuration errors
  - Test suite database issues
  - Virtual environment problems

### 🧪 Testing & CI Issues
- **[CI Test Hang Resolution](./ci-test-hang-resolution.md)** - CI pipeline and test infrastructure problems
  - Test hangs in CI environment
  - Coverage threshold failures
  - PostgreSQL role errors
  - Async test issues

### 🔐 Authentication & Security Issues
- **[API Keys Dashboard Authentication](./api-keys-dashboard-authentication-issue.md)** - Admin panel authentication problems
  - API keys dashboard access issues
  - Superuser authentication problems
  - Admin panel configuration

## 🚀 Quick Solutions

### Most Common Issues

**Environment Variables Not Loading:**
```bash
./scripts/fix_env_issues.sh
```

**Can't Find .env File:**
```bash
ls -la | grep -E "\.env"
cat .env
```

**Database Connection Issues:**
```bash
docker-compose up -d
sleep 10
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"
```

**Test Suite Problems:**
```bash
docker-compose up -d
source venv/bin/activate
pytest
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