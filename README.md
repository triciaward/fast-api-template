# Your Project Name

Welcome to your new FastAPI project! 🎉

This is your project's main README file - feel free to customize it to describe what your application does, how to use it, and any specific features you've built.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher (for development tools)
- Docker and Docker Compose (for running the application)

### Quick Setup

**Option 1: Automated Setup (Recommended)**
```bash
# Run the comprehensive setup script
./scripts/setup_comprehensive.sh
```

**Option 2: Manual Setup**
```bash
# Start all services
docker-compose up -d

# Run database migrations
alembic upgrade head

# Create a superuser (optional)
python app/bootstrap_superuser.py
```

Your API will be available at `http://localhost:8000`

## 🐳 Running with Docker

**This is the primary way to run the application!** The project is designed to run everything in Docker containers:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

**Available Services:**
- **FastAPI App**: http://localhost:8000
- **PostgreSQL**: Port 5432
- **Redis**: Port 6379 (optional)
- **Celery Worker**: Background tasks (optional)
- **Flower**: Celery monitoring (optional)

## 📚 API Documentation

Once your app is running, you can explore your API:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 🧪 Testing Your Application

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app
```

## 🔧 Development Workflow

For development, you'll use the local Python environment for tools while the app runs in Docker:

```bash
# Development tools (run locally)
ruff format .
ruff check .
pytest

# Application (runs in Docker)
docker-compose up -d
docker-compose logs -f api
```

## 🚀 CI Validation Workflow

**Prevent CI failures before they happen!** This project includes a comprehensive validation system that catches issues locally before they reach CI.

### Quick Validation

**Before pushing code, always run:**
```bash
./scripts/validate_ci.sh
```

This script automatically:
- ✅ Checks Black formatting
- ✅ Checks Ruff linting  
- ✅ Validates pytest fixture discovery
- ✅ Tests critical imports
- ✅ Activates virtual environment automatically

### Setup Automatic Validation

**Install development tools and set up git hooks:**
```bash
# Install development tools with exact versions
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Setup automatic validation before push
./scripts/setup-git-hooks.sh
```

**Now validation runs automatically before every push!**

### If Validation Fails

1. **Black formatting issues**: `python3 -m black .`
2. **Ruff linting issues**: `python3 -m ruff check . --fix`
3. **Pytest issues**: Check `conftest.py` and fixture definitions
4. **Import issues**: Verify module imports and dependencies

### Benefits

- 🎯 **No more CI surprises** - catch issues locally first
- 🔧 **Consistent tooling** - same versions everywhere  
- ⚡ **Faster feedback** - validate in seconds, not minutes
- 👥 **Team consistency** - everyone uses the same validation process

**📖 For detailed information:** See [CI Validation Workflow](docs/troubleshooting/ci-validation-workflow.md)

## 🛠️ Troubleshooting

### Common Issues and Solutions

**1. Environment Variables Not Loading**
If you see warnings like `WARN[0000] The "POSTGRES_DB" variable is not set. Defaulting to a blank string.`:
```bash
# Run the environment fix script
./scripts/fix_env_issues.sh
```

**2. Database Connection Issues**
If migrations fail or database connections don't work:
```bash
# Fix environment and configuration
./scripts/fix_env_issues.sh

# Restart services
docker-compose down
docker-compose up -d

# Run migrations
alembic upgrade head
```

**3. Virtual Environment Issues**
If you get "command not found" errors for Python tools:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Quick Diagnostic Commands

```bash
# Check service status
docker-compose ps

# View logs for specific service
docker-compose logs api
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U postgres -d your_project_name -c "SELECT 1;"

# Test Alembic configuration
alembic current
```

## 🧹 Code Quality (Pre-commit Hooks)

This project uses pre-commit hooks to ensure code quality.

- To install hooks, run:  
  ```bash
  pre-commit install
  ```
- You can also use the helper script:  
  ```bash
  ./scripts/install_precommit.sh
  ```
- Hooks are run automatically on every commit to check formatting and lint your code.

The pre-commit hooks will automatically:
- Format your code with `black`
- Check for linting issues with `ruff`
- Verify type annotations with `mypy`
- Run on every commit to ensure code quality

## 📖 What's Included

This project comes with several features out of the box:

- **Docker-First Architecture** - Everything runs in containers by default
- **User Authentication** - Registration, login, and JWT tokens
- **Database Management** - PostgreSQL with automatic migrations
- **Admin Panel** - Built-in admin interface at `/admin`
- **API Key Management** - Secure API key system
- **Audit Logging** - Track important actions
- **Testing Framework** - Comprehensive test suite
- **Development Tools** - Local Python environment for linting, testing, and formatting

## 🎯 Next Steps

1. **Customize this README** - Update it to describe your specific project
2. **Explore the code** - Check out the `app/` folder to see how everything is organized
3. **Add your features** - Start building your application logic
4. **Check the docs** - See the template documentation for advanced features
5. **Read the Next Steps Guide** - [Next Steps & Development Tips](docs/tutorials/next-steps-and-tips.md)

## 📚 Template Documentation

This project was built using a FastAPI template that provides a solid foundation. For detailed information about:

- Template features and capabilities
- Advanced configuration options
- Deployment guides
- Troubleshooting tips

**Check out the documentation in the `docs/` folder:**
- [Template Overview](docs/TEMPLATE_README.md)
- [Getting Started Guide](docs/tutorials/getting-started.md)
- [Complete Tutorials](docs/tutorials/TUTORIALS.md)

## 🤝 Contributing

This is your project! Feel free to:
- Add new features
- Modify existing code
- Update documentation
- Add tests for your changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Happy coding! 🚀**

*This project was created using a FastAPI template. For template-specific information, see the `docs/` folder.*
