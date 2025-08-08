# Environment Issues Troubleshooting Guide

This guide helps you resolve common environment variable and configuration issues that can occur when setting up the FastAPI template.

## 🚨 Common Issues

### 1. Hidden .env File Issues

**Problem:** Can't find the `.env` file or it appears to be missing.

**Root Cause:** The `.env` file is a **hidden file** (starts with a dot) and doesn't show up in regular directory listings.

**Solution:**
```bash
# Show hidden files including .env
ls -la | grep -E "\.env"

# View .env file contents
cat .env

# If .env doesn't exist, create it from example
cp .env.example .env
```

**Why is .env hidden?**
- Hidden files (starting with `.`) are a Unix/Linux convention for configuration files
- This prevents accidental deletion or modification
- It keeps sensitive information out of regular file listings

### 2. Environment Variables Not Loading

**Problem:** Docker Compose shows warnings like:
```
WARN[0000] The "POSTGRES_DB" variable is not set. Defaulting to a blank string.
WARN[0000] The "POSTGRES_USER" variable is not set. Defaulting to a blank string.
WARN[0000] The "POSTGRES_PASSWORD" variable is not set. Defaulting to a blank string.
```

**Root Cause:** The `.env` file is missing required environment variables or Docker Compose can't read it.

**Solution:**
```bash
# Run the environment fix script (recommended)
./scripts/fix_env_issues.sh

# Or manually check and fix
ls -la | grep -E "\.env"
cat .env

# If variables are missing, add them:
echo "POSTGRES_DB=fastapi_template" >> .env
echo "POSTGRES_USER=postgres" >> .env
echo "POSTGRES_PASSWORD=dev_password_123" >> .env
echo "DATABASE_URL=postgresql://postgres:dev_password_123@localhost:5432/fastapi_template" >> .env
echo "SECRET_KEY=dev_secret_key_change_in_production" >> .env
```

### 3. Database Connection Issues

**Problem:** Database connection fails with errors like:
```
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

**Root Cause:** PostgreSQL container is not running or not ready.

**Solution:**
```bash
# Check if containers are running
docker-compose ps

# Start services if not running
docker-compose up -d

# Wait for services to be ready
sleep 10

# Test database connection
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"
```

### 4. Alembic Configuration Errors

**Problem:** Alembic fails with errors like:
```
configparser.InterpolationSyntaxError: '%' must be followed by '%' or '(', found: '%04d'
```

**Root Cause:** Malformed configuration in `alembic.ini` or incorrect database URL.

**Solution:**
```bash
# Run the environment fix script (handles this automatically)
./scripts/fix_env_issues.sh

# Or manually fix alembic.ini
# Check the database URL in alembic.ini:
grep "sqlalchemy.url" alembic.ini

# It should look like:
# sqlalchemy.url = postgresql://postgres:dev_password_123@localhost:5432/fastapi_template
```

### 5. Test Suite Database Issues

**Problem:** Tests fail with database connection errors during `pytest`.

**Root Cause:** Docker services stopped or database not ready for intensive testing.

**Solution:**
```bash
# Ensure services are running
docker-compose up -d

# Wait for services to be ready
sleep 10

# Activate virtual environment
source venv/bin/activate

# Run tests
pytest
```

### 6. Virtual Environment Issues

**Problem:** Commands like `alembic` or `pytest` return "command not found".

**Root Cause:** Virtual environment not activated or dependencies not installed.

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
alembic --version
pytest --version
```

## 🛠️ Diagnostic Commands

### Quick Environment Check
```bash
# Check if .env file exists and has required variables
ls -la | grep -E "\.env"
grep -E "^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|DATABASE_URL|SECRET_KEY)=" .env
```

### Docker Services Check
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs api
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"
```

### API Health Check
```bash
# Test API health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "checks": {
#     "database": "healthy",
#     "application": "healthy"
#   }
# }
```

### Configuration Validation
```bash
# Test Docker Compose configuration
docker-compose config

# Test Alembic configuration
alembic current

# Run comprehensive verification
python scripts/verify_setup.py
```

## 🚀 Automated Solutions

### Environment Fix Script
The template includes a comprehensive fix script that handles most common issues:

```bash
./scripts/fix_env_issues.sh
```

This script automatically:
- ✅ Detects and reads existing `.env` files (including hidden ones)
- ✅ Adds missing required environment variables
- ✅ Fixes database configuration issues
- ✅ Validates Docker Compose configuration
- ✅ Tests database connectivity
- ✅ Verifies Alembic configuration
- ✅ Provides detailed feedback and next steps

### Comprehensive Setup Script
For a complete setup from scratch:

```bash
./scripts/setup_comprehensive.sh
```

This script:
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Sets up environment variables
- ✅ Starts Docker services
- ✅ Runs database migrations
- ✅ Verifies everything works

## 🔧 Manual Configuration

### Required Environment Variables
Your `.env` file should contain these variables:

```env
# Database Configuration
POSTGRES_DB=fastapi_template
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev_password_123
DATABASE_URL=postgresql://postgres:dev_password_123@localhost:5432/fastapi_template

# Security
SECRET_KEY=dev_secret_key_change_in_production
ALGORITHM=HS256

# Optional Features
ENABLE_REDIS=false
ENABLE_WEBSOCKETS=false
ENABLE_CELERY=false
ENABLE_RATE_LIMITING=true
ENABLE_SENTRY=false

# Project Configuration
COMPOSE_PROJECT_NAME=fast-api-template
```

### Docker Compose Configuration
The `docker-compose.yml` file should reference these environment variables:

```yaml
services:
  postgres:
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

## 🆘 Still Having Issues?

If you're still experiencing problems after trying these solutions:

1. **Check the logs**: `docker-compose logs`
2. **Verify file permissions**: `ls -la`
3. **Test individual components**: Use the diagnostic commands above
4. **Check for port conflicts**: `lsof -i :8000` and `lsof -i :5432`
5. **Restart Docker**: Sometimes Docker needs a fresh start
6. **Check system resources**: Ensure you have enough memory and disk space

## 📞 Getting Help

If none of these solutions work:
1. Check the [main troubleshooting guide](../TROUBLESHOOTING_README.md#troubleshooting)
2. Review the [getting started guide](../tutorials/getting-started.md)
3. Check the [template documentation](../TEMPLATE_README.md)
4. Open an issue in the repository with:
   - Your operating system
   - Docker version
   - Python version
   - Complete error messages
   - Output from diagnostic commands 