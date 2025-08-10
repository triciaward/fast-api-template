# Environment & Setup Issues

This folder contains troubleshooting guides for environment configuration and project setup issues.

## 📁 Available Guides

### **[Environment Issues](./environment-issues.md)**
- Hidden `.env` file issues
- Environment variables not loading
- Database connection problems
- Alembic configuration errors
- Test suite database issues
- Virtual environment problems

### **[Setup Issues](./setup-issues.md)**
- Missing alembic.ini configuration
- Database migration conflicts
- Superuser creation issues
- Username and password validation errors
- Module import problems

### **[Customization Improvements](./customization_improvements.md)**
- Template customization workflow
- Three-script approach (rename → customize → setup)
- Preventing configuration conflicts
- Clear user instructions and error prevention

## 🚀 Quick Solutions

### Most Common Environment Issues:
```bash
# Fix environment variables
./scripts/fix_env_issues.sh

# Check .env file
ls -la | grep -E "\.env"
cat .env

# Test database connection
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"
```

### Most Common Setup Issues:
```bash
# Run comprehensive setup
./scripts/setup_comprehensive.sh

# Verify setup
python scripts/verify_setup.py

# Check database migrations
alembic current
```

### Docker not running / Docker Desktop closed

If the setup script reports Docker is not running, it now offers options to:
- Attempt to start Docker Desktop automatically (macOS/Windows) or the Docker service (Linux)
- Retry detection
- Continue without Docker (skips containers) and shows follow-up commands

You can always start Docker later and run:
```bash
docker-compose up -d postgres
alembic upgrade head
docker-compose up -d api
```

## 📞 Getting Help

If you encounter issues not covered in these guides:
1. Check the main [troubleshooting index](../TROUBLESHOOTING_README.md)
2. Review the [getting started guide](../../tutorials/getting-started.md)
3. Run diagnostic scripts: `./scripts/fix_env_issues.sh`
4. Open an issue with complete error messages and environment details
