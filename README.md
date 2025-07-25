# Your Project Name

Welcome to your new FastAPI project! 🎉

This is your project's main README file - feel free to customize it to describe what your application does, how to use it, and any specific features you've built.

## 🎯 Creating Your Own Project from This Template

**This is a FastAPI template!** If you want to create your own project (let's say "My Awesome Project"), here's exactly how to do it:

### Step 1: Get the Template
First, you need to get this template. You can either:
- Clone the repository: `git clone <template-repo-url>`
- Download it as a ZIP file
- Or use it as a GitHub template

### Step 2: Copy the Template
Copy the entire template folder to your desired location.

### Step 3: Run the Customization Script
This is where the magic happens! Run:
```bash
./scripts/customize_template.sh
```

The script will ask you questions like:
- "What's your project name?" → "My Awesome Project"
- "What should the project slug be?" → "myawesomeproject_backend"
- "What should the database be called?" → "myawesomeproject_backend"

### Step 4: The Magic Happens
The script automatically:
- **Provides instructions** for renaming the project folder to your project slug (e.g., `myawesomeproject_backend`)
- Renames all template references to your project name
- Updates database names and connection strings
- Changes import statements throughout the code
- Updates documentation and README files
- Modifies configuration files
- Updates the Docker setup
- **Creates a VS Code workspace file** to help with the transition

### Step 5: Set Up Your New Project
After customization, follow the instructions to rename the folder, then run:
```bash
cd your_project_name_backend
./scripts/setup_comprehensive.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Set up your `.env` file with the right database name
- Start PostgreSQL and Redis
- Run database migrations
- Verify everything works

### Step 6: Start Building!
Now you have a fully working project with:
- User authentication system
- Admin panel
- API key management
- Database setup
- Testing framework
- Docker support
- All template features, but branded for your project

**That's it!** You've gone from "I want to build My Awesome Project" to "I have a working My Awesome Project API" in just a few commands.

## 🚀 Getting Started

If you're new to this project, here's how to get it running:

### Prerequisites
- Python 3.11 or higher (for development tools)
- Docker and Docker Compose (for running the application)

### Quick Setup

**Option 1: Automated Setup (Recommended)**
```bash
# Run the comprehensive setup script
./scripts/setup_comprehensive.sh
```
This script will automatically:
- Create a virtual environment for development tools
- Install dependencies
- Set up your `.env` file (hidden file starting with a dot)
- Start all services in Docker (FastAPI, PostgreSQL, Redis)
- Run database migrations
- Verify everything is working

**💡 Note:** The `.env` file is a hidden file (starts with `.`). If you can't see it, use `ls -la | grep -E "\.env"` to find it.

**Option 2: Fix Environment Issues (If you encounter problems)**
If you're experiencing environment variable or configuration issues:
```bash
# Run the environment fix script
./scripts/fix_env_issues.sh
```
This script specifically addresses:
- Missing or incorrect environment variables
- Database configuration issues
- Docker Compose environment variable problems
- Alembic configuration errors

**⚠️ Important Note:** The `.env` file is a **hidden file** (starts with a dot). If you can't see it, use:
```bash
# Show hidden files including .env
ls -la | grep -E "\.env"

# Or view the .env file contents
cat .env
```

**Option 2: Manual Docker Setup**
```bash
# Start everything with Docker Compose
docker-compose up -d

# Run database migrations
alembic upgrade head

# Create a superuser (optional)
python app/bootstrap_superuser.py
```

Your API will be available at `http://localhost:8000`

Visit http://localhost:8000/docs to view the interactive API documentation.

## 🐳 Running with Docker

**This is the primary way to run the application!** The template is designed to run everything in Docker containers:

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

## 🛠️ Troubleshooting

### Understanding Hidden Files

**Important:** The `.env` file is a **hidden file** (starts with a dot). This is normal and intentional for security reasons. Hidden files don't show up in regular directory listings.

**To see hidden files:**
```bash
# Show all files including hidden ones
ls -la

# Show only .env files
ls -la | grep -E "\.env"

# View .env file contents
cat .env
```

**Common hidden files in this project:**
- `.env` - Environment variables (this is what you need!)
- `.env.example` - Example environment file
- `.env.test` - Test environment file
- `.gitignore` - Git ignore rules
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

### Common Issues and Solutions

**0. Can't Find the .env File**
If you can't see the `.env` file, it's because it's a **hidden file**:
```bash
# Show hidden files
ls -la | grep -E "\.env"

# View .env contents
cat .env

# If .env doesn't exist, create it from example
cp .env.example .env
```

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

**3. Alembic Configuration Errors**
If you see `configparser.InterpolationSyntaxError` or similar:
```bash
# The fix_env_issues.sh script will automatically fix these
./scripts/fix_env_issues.sh
```

**4. Docker Compose Environment Issues**
If Docker Compose can't read environment variables:
```bash
# Export variables and test configuration
./scripts/fix_env_issues.sh

# Verify configuration
docker-compose config
```

**5. Test Suite Issues**
If tests fail due to database connection problems:
```bash
# Ensure services are running
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run tests
pytest
```

**6. Virtual Environment Issues**
If you get "command not found" errors for Python tools:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Quick Diagnostic Commands

```bash
# Check if .env file exists (it's a hidden file!)
ls -la | grep -E "\.env"

# View .env file contents
cat .env

# Check if .env file has required variables
grep -E "^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD|DATABASE_URL|SECRET_KEY)=" .env

# Test Docker Compose configuration
docker-compose config

# Check service status
docker-compose ps

# View logs for specific service
docker-compose logs api
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U postgres -d fastapi_template -c "SELECT 1;"

# Test Alembic configuration
alembic current
```

## 🧹 Code Quality (Pre-commit Hooks)

This project uses [pre-commit](https://pre-commit.com/) hooks for code quality. To set them up:

```bash
./scripts/install_precommit.sh
```

This script will:
- Install pre-commit
- Install git hooks for code formatting and linting
- Run all hooks on your codebase

You can also manually install the hooks:
```bash
pre-commit install
```

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

If you're using this as a template to create your own project, follow the steps above in the "Creating Your Own Project from This Template" section.

If you're already working with your customized project:

1. **Customize this README** - Update it to describe your specific project
2. **Explore the code** - Check out the `app/` folder to see how everything is organized
3. **Add your features** - Start building your application logic
4. **Check the docs** - See the template documentation for advanced features

## 🆕 Recent Improvements

**Latest Updates (July 2025):**
- ✅ **Enhanced Environment Variable Handling** - Robust detection and validation of hidden `.env` files
- ✅ **Improved Setup Scripts** - Intelligent handling of existing configurations without overwriting
- ✅ **New Environment Fix Script** - Dedicated `fix_env_issues.sh` for quick problem resolution
- ✅ **Comprehensive Test Coverage** - 416 passing tests with 0 failures
- ✅ **Better Documentation** - Clear troubleshooting guides and hidden file explanations
- ✅ **Stable Docker Infrastructure** - Improved container stability and connection handling

**Key Features:**
- **Smart .env Detection** - Scripts now properly find and read hidden environment files
- **Non-Destructive Setup** - Preserves existing configurations while adding missing variables
- **Automated Problem Resolution** - One-command fixes for common environment issues
- **Comprehensive Testing** - Full test suite with 627 selected tests covering all functionality

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

**Note**: This is a default MIT license. You may want to update it to reflect your specific licensing needs for your project.

---

**Happy coding! 🚀**

*This project was created using a FastAPI template. For template-specific information, see the `docs/` folder.* 