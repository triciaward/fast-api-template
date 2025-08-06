# Your Project Name

Welcome to your new FastAPI project! 🎉

This is your project's main README file - feel free to customize it to describe what your application does, how to use it, and any specific features you've built.

## 🚀 Initial Project Setup

**If you're setting up this project for the first time, follow these steps in order:**

### ⚠️ CRITICAL: Create a New GitHub Repository First!

**🚨 IMPORTANT:** Before starting the setup process, you MUST create a new GitHub repository for your project. If you don't, you risk accidentally overwriting this template repository!

**How to create your new repository:**
1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" button in the top right corner
3. Select "New repository"
4. Name it something like "my-project-backend" or "my-awesome-api"
5. **DO NOT** initialize with README, .gitignore, or license (we'll add these)
6. Click "Create repository"
7. Copy the repository URL (you'll need this later)

**Why this is critical:**
- The setup process will rename and customize the template
- Without a new repo, you might accidentally push changes back to this template
- Your customized project needs its own repository to track changes
- This prevents confusion and protects the original template

**🛡️ Safety Features:** This template includes multiple protection mechanisms:
- **Pre-commit hooks** that warn about template repository operations
- **Git hooks** that prevent commits to the template repository
- **Documentation warnings** throughout the setup process

### Step 1: Clone and Navigate
```bash
# Clone the template
git clone <your-repo-url>
cd fast-api-template
```

### Step 2: Rename the Template Directory

**What this does:**
- Renames the template directory to your project name with "_backend" suffix
- Prevents configuration conflicts
- Sets up the foundation for customization

**💡 Important:** The directory will ALWAYS be renamed to end with "_backend"
- "My Awesome Project" → "myawesomeproject_backend"
- "Todo App" → "todo_app_backend"
- "E-commerce API" → "ecommerce_api_backend"

**How to do it:**
1. Make sure you're in the `fast-api-template` directory
2. Run: `./scripts/rename_template.sh`
3. Enter your project name when prompted
4. The script will rename the directory and give you next steps

**Example:**
```bash
$ ./scripts/rename_template.sh
🚀 FastAPI Template - Step 1: Rename Directory
==============================================

This script will rename the template directory to your project name.
This is the FIRST step in customizing your template.

Please enter your project name:
  Examples: 'My Awesome Project', 'Todo App Backend', 'E-commerce API'

Project name: My Awesome Project

📋 Summary:
  Project Name: My Awesome Project
  Directory Name: myawesomeproject_backend

Continue with renaming? (y/N): y

🔄 Renaming directory...
✅ Directory renamed successfully!

🎉 STEP 1 COMPLETE!
==================

🚨 IMPORTANT: You must restart VS Code now!

Next steps:
1. Close VS Code completely
2. Open VS Code again
3. Open the folder: myawesomeproject_backend
4. Run the next script: ./scripts/customize_template.sh

💡 Tip: You can also run: code myawesomeproject_backend
```

### Step 3: Restart VS Code

**Why this is important:**
- VS Code needs to recognize the new directory name
- Prevents path conflicts and configuration issues
- Ensures all tools work correctly

**How to do it:**
1. **Close VS Code completely** (not just the window)
2. **Open VS Code again**
3. **Open the renamed folder**: `myawesomeproject_backend`

### Step 4: Customize the Template

**What this does:**
- Replaces all template references with your project details
- Updates database names and connection strings
- Changes import statements throughout the code
- Updates documentation and configuration files
- Modifies Docker setup to prevent conflicts

**How to do it:**
1. Make sure you're in the renamed directory
2. Run: `./scripts/customize_template.sh`
3. Enter your project details when prompted
4. Review the summary and confirm

**Example:**
```bash
$ ./scripts/customize_template.sh
🚀 FastAPI Template Customization - Step 2
==========================================
This script will transform the template into your custom project.
Please provide the following information:

Project name (e.g., 'My Awesome Project'): My Awesome Project
Project slug (e.g., 'myawesomeproject_backend'): myawesomeproject_backend
Database name (e.g., 'myawesomeproject_backend', default: myawesomeproject_backend): 
Project description (e.g., 'A FastAPI backend for my awesome project'): A FastAPI backend for my awesome project
Author name (e.g., 'Your Name'): Your Name
Author email (e.g., 'your.email@example.com'): your.email@example.com

📋 Customization Summary:
  Project Name: My Awesome Project
  Project Slug: myawesomeproject_backend
  Database Name: myawesomeproject_backend
  Docker Name: myawesomeproject_backend
  Description: A FastAPI backend for my awesome project
  Author: Your Name <your.email@example.com>

Proceed with customization? (y/N): y

🚀 Starting template customization...

📁 Scanning files for template references...
   Found 45 files to process

🔄 Processing files...
   ✅ Updated: README.md
   ✅ Updated: docker-compose.yml
   ✅ Updated: app/main.py
   ✅ Updated: .env
   ... (more files)

📊 Customization Summary:
   Files processed: 45
   Files updated: 42

🎉 STEP 2 COMPLETE!
==================

📋 Next Steps:
1. Review the changes in docs/troubleshooting/TEMPLATE_CUSTOMIZATION.md
2. **🚨 CRITICAL:** Update your git remote to point to your new repository:
   ```bash
   git remote set-url origin https://github.com/yourusername/your-new-repo-name.git
   ```
3. Run the setup script: ./scripts/setup_project.sh
4. Start developing your application!

✨ Happy coding!
```

### Step 5: Set Up Your Project

**What this does:**
- Creates Python virtual environment
- Installs all dependencies
- Starts PostgreSQL and FastAPI
- Runs database migrations
- Sets up everything you need to start developing

**How to do it:**
1. Make sure you're in the renamed directory
2. Run: `./scripts/setup_project.sh`
3. Follow the prompts (optional: create a superuser)
4. Wait for all services to start

**Example:**
```bash
$ ./scripts/setup_project.sh
🚀 FastAPI Template - Step 3: Project Setup
===========================================

This script will set up your development environment and database.
This is the FINAL step in getting your project ready.

✅ You're in a renamed project directory: myawesomeproject_backend

✅ .env file already exists
✅ Virtual environment already exists

📦 Installing Python dependencies...
✅ Dependencies installed

🐳 Checking Docker...
✅ Docker is running

🗄️  Starting database services...
✅ Database services started

⏳ Waiting for PostgreSQL to be ready...
✅ PostgreSQL is ready

🔄 Running database migrations...
✅ Database migrations completed

👤 Create a superuser account (optional):
Create superuser? (y/N): y

Running superuser creation script...
✅ Superuser creation completed

🔍 Running final checks...
   Testing API startup...
✅ API startup test passed
   Testing test environment...
✅ Test environment ready

🎉 STEP 3 COMPLETE!
==================

🚀 Your project is ready!

📋 What's been set up:
  ✅ Python virtual environment
  ✅ All dependencies installed
  ✅ PostgreSQL database running
  ✅ FastAPI application running
  ✅ Database migrations applied
  ✅ Environment variables configured

🎯 Next Steps:
1. View API docs: http://localhost:8000/docs
2. Run tests: pytest
3. Start developing!

💡 Useful Commands:
  docker-compose up -d          # Start all services (including Redis if needed)
  docker-compose logs -f        # View logs
  docker-compose down           # Stop all services
  pytest                        # Run tests
  alembic revision --autogenerate -m 'description'  # Create migration
  alembic upgrade head          # Apply migrations
```

**That's it!** You now have a fully working project with:
- User authentication system
- Admin panel
- API key management
- Database setup (PostgreSQL)
- FastAPI application running
- Testing framework
- Docker support
- All template features, but branded for your project

**🚀 What's Running:**
- **PostgreSQL** database on port 5432
- **FastAPI** application on port 8000 (docs at http://localhost:8000/docs)
- **Optional services** (Redis, Celery) can be started when needed

### 🆘 Need Help?

If you encounter any issues during setup:

- **📖 Troubleshooting Guide**: [Setup Issues & Solutions](docs/troubleshooting/setup-issues.md)
- **🐛 Common Problems**: Missing alembic.ini, database errors, superuser creation issues
- **🔧 Quick Fixes**: Most issues have simple solutions documented in the guide

## 🚀 Quick Start

**If you've already completed the initial setup above, you can use these quick commands:**

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

This project uses pre-commit hooks to ensure code quality and prevent common mistakes.

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
- **🛡️ Prevent accidental pushes to the template repository**
- Run on every commit to ensure code quality

### 🛡️ Safety Features

**Template Repository Protection:**
- **Git hooks** prevent commits to the template repository
- **Pre-commit hooks** warn about template repository operations
- If detected, they will warn you and ask for confirmation before allowing the operation
- This prevents accidentally overwriting the template and causing problems for others

**To install the protection hooks:**
```bash
# Install git hooks (recommended)
./scripts/install_git_hooks.sh

# Install pre-commit hooks
pre-commit install
```

## 📖 What's Included

This project comes with several features out of the box:

- **Docker-First Architecture** - Everything runs in containers by default
- **User Authentication** - Registration, login, and JWT tokens with modular architecture
- **Database Management** - PostgreSQL with automatic migrations
- **Admin Panel** - Built-in admin interface at `/admin`
- **API Key Management** - Secure API key system
- **Enhanced Security Headers** - Comprehensive HTTP security headers with request validation and content-type checking
- **Audit Logging** - Track important actions
- **Testing Framework** - Comprehensive test suite
- **Development Tools** - Local Python environment for linting, testing, and formatting
- **Type Safety** - Full type annotations with proper error handling

## 🎯 Next Steps

1. **Customize this README** - Update it to describe your specific project
2. **Explore the code** - Check out the `app/` folder to see how everything is organized
3. **Add your features** - Start building your application logic
4. **Check the docs** - See the template documentation for advanced features
5. **Read the Next Steps Guide** - [Next Steps & Development Tips](docs/tutorials/next-steps-and-tips.md)

## 📚 Template Documentation

- [Getting Started](docs/tutorials/getting-started.md) - Complete setup guide
- [Tutorials Index](docs/tutorials/TUTORIALS.md) - All tutorials in one place
- [Next Steps & Development Tips](docs/tutorials/next-steps-and-tips.md) - What to build first, common commands, and mistakes to avoid
- [Authentication Guide](docs/tutorials/authentication.md)
- [Database Management](docs/tutorials/database-management.md)
- [Testing Guide](docs/tutorials/testing-and-development.md)
- [Deployment Guide](docs/tutorials/deployment-and-production.md)
- [Optional Features](docs/tutorials/optional-features.md)
- [Troubleshooting](docs/troubleshooting/) - Common issues and solutions
  - [Template Critical Fixes](docs/troubleshooting/template-fixes.md) - Critical fixes applied to prevent common issues
  - [Recent Improvements](docs/troubleshooting/recent-improvements.md) - Latest security and type safety enhancements

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
