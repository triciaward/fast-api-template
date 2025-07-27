# Your Project Name

Welcome to your new FastAPI project! 🎉

This is your project's main README file - feel free to customize it to describe what your application does, how to use it, and any specific features you've built.

## 🤖 AI ASSISTANT WORKFLOW INSTRUCTIONS

**⚠️ CRITICAL:** When helping users create projects from this template, follow this EXACT workflow:

1. **Run rename script:** `./scripts/rename_template.sh`
2. **STOP and provide clear instructions:** Tell user to restart VS Code and open renamed directory
3. **Provide the exact message:** Give user the exact message to copy/paste after restart
4. **Wait for confirmation:** Only continue after user confirms VS Code is restarted
5. **Continue with customization:** `./scripts/customize_template.sh`

**DO NOT automatically continue to step 3 without waiting for VS Code restart!**

**📋 EXACT MESSAGE TO GIVE USER AFTER RENAME:**
```
✅ Directory renamed successfully!

🚨 CRITICAL: You must restart VS Code now!

Next steps:
1. Close VS Code completely
2. Open VS Code again  
3. Open the folder: [PROJECT_NAME]_backend
4. Copy and paste this message to your AI assistant:

"I've restarted VS Code and opened the renamed directory: [PROJECT_NAME]_backend

Please help me continue with the template customization process. I need to:
1. Run the customization script
2. Set up my project environment  
3. Get my FastAPI application running

The directory has been renamed from "fast-api-template" to "[PROJECT_NAME]_backend" and I'm now in the renamed directory."
```

## 🎯 Creating Your Own Project from This Template

**This is a FastAPI template!** If you want to create your own project (let's say "My Awesome Project"), here's exactly how to do it:

### 🚀 Quick Start (3 Simple Steps)

**Step 1: Rename the Template**
```bash
# Run the rename script
./scripts/rename_template.sh

# Enter your project name when prompted:
# Project name: My Awesome Project
# 
# The script will:
# ✅ Rename: fast-api-template → myawesomeproject_backend
# ✅ Give you clear next steps
# 
# 💡 Note: The folder will ALWAYS end with "_backend" 
#    (e.g., "My Awesome Project" becomes "myawesomeproject_backend")
```

**🚨 CRITICAL: Step 2 - Restart VS Code (MANDATORY)**
```bash
# CLOSE VS CODE COMPLETELY (quit the entire application)
# Open VS Code again
# Use File → Open Folder and navigate to: myawesomeproject_backend
```

**⚠️ IMPORTANT:** You MUST restart VS Code after renaming. Do NOT continue with the next steps until you have restarted VS Code and opened the renamed directory.

**🤖 AI ASSISTANT INSTRUCTIONS:**
After restarting VS Code and opening the renamed directory, copy and paste this message to your AI assistant:

```
I've restarted VS Code and opened the renamed directory: [YOUR_PROJECT_NAME]_backend

Please help me continue with the template customization process. I need to:
1. Run the customization script
2. Set up my project environment
3. Get my FastAPI application running

The directory has been renamed from "fast-api-template" to "[YOUR_PROJECT_NAME]_backend" and I'm now in the renamed directory.
```

**💡 What your AI assistant will do:**
When you send this message, your AI assistant will:
1. Verify you're in the renamed directory
2. Run the customization script: `./scripts/customize_template.sh`
3. Help you set up your project: `./scripts/setup_project.sh`
4. Get your FastAPI application running

**Step 3: Customize the Template**
```bash
# Run the customization script
./scripts/customize_template.sh

# Enter your project details when prompted:
# Project name: My Awesome Project
# Project slug: myawesomeproject_backend
# Database name: myawesomeproject_backend
# Docker name: myawesomeproject_backend
# Description: A FastAPI backend for my awesome project
# Author: Your Name
# Email: your.email@example.com
```

**Step 2: Rename the Template Directory**
```bash
# Run the rename script
./scripts/rename_template.sh

# This will:
# ✅ Rename the directory to your project name
# ✅ Set up the foundation for customization
# ✅ Give you next steps
```

**Step 3: Restart VS Code**
- Close VS Code completely
- Open VS Code again
- Open the renamed folder

**Step 4: Customize the Template**
```bash
# Run the customization script
./scripts/customize_template.sh

# This will:
# ✅ Replace all template references with your project details
# ✅ Update database names and connection strings
# ✅ Update documentation and configuration files
```

**Step 5: Set Up Your Project**
```bash
# Run the setup script
./scripts/setup_project.sh

# This will:
# ✅ Create Python virtual environment
# ✅ Install all dependencies
# ✅ Start PostgreSQL and FastAPI
# ✅ Run database migrations
# ✅ Set up everything you need
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

### 📋 Complete Setup Process

The template setup involves **5 steps** that must be done in order:

#### Step 1: Clone and Navigate
```bash
# Clone the template
git clone <your-repo-url>
cd fast-api-template
```

#### Step 2: Rename the Template Directory

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

#### Step 3: Restart VS Code

**Why this is important:**
- VS Code needs to recognize the new directory name
- Prevents path conflicts and configuration issues
- Ensures all tools work correctly

**How to do it:**
1. **Close VS Code completely** (not just the window)
2. **Open VS Code again**
3. **Open the renamed folder**: `myawesomeproject_backend`



#### Step 4: Customize the Template

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
2. Update your git remote: git remote set-url origin <your-repo-url>
3. Run the setup script: ./scripts/setup_project.sh
4. Start developing your application!

✨ Happy coding!
```

#### Step 5: Set Up Your Project

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

---

## 🚀 Quick Start Guide

### Test Your Setup

After completing the setup, verify everything is working:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Verify your setup
python3 scripts/verify_setup.py

# 3. Test the API health endpoint
curl http://localhost:8000/api/v1/health

# 4. Run tests
pytest

# 5. Check services
docker-compose ps
```

### Common Issues & Solutions

**Virtual Environment Not Activated:**
```bash
# If verification script fails with "No module named 'fastapi'"
source venv/bin/activate && python3 scripts/verify_setup.py
```

**Health Endpoint Path:**
- ✅ **Correct**: `http://localhost:8000/api/v1/health`
- ❌ **Wrong**: `http://localhost:8000/health`

**Environment Variables:**
- Some variables are set in Docker containers, not in your local `.env` file
- This is normal - the API runs in Docker with its own configuration

### First Steps

1. **View API Docs**: http://localhost:8000/docs
2. **Create Superuser**: `python3 app/bootstrap_superuser.py`
3. **Check Admin Panel**: http://localhost:8000/admin
4. **Start Developing**: Add your own endpoints and features

✨ Happy coding!
```

### 🎯 Start Your Project

After completing all steps, start your project:

```bash
# Start all services
docker-compose up -d

# View API documentation
open http://localhost:8000/docs

# Run tests
pytest

# View logs
docker-compose logs -f
```

Your API will be available at `http://localhost:8000`

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
- Start all services in Docker (FastAPI, PostgreSQL)
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

## 🚀 CI Validation Workflow

**Prevent CI failures before they happen!** This template includes a comprehensive validation system that catches issues locally before they reach CI.

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
5. **Read the Next Steps Guide** - [Next Steps & Development Tips](docs/tutorials/next-steps-and-tips.md)

## 🆕 Recent Improvements

**Latest Updates (July 2025):**
- ✅ **Simplified Template Customization** - Now uses 3 separate scripts for clarity
- ✅ **Step-by-Step Process** - Clear, easy-to-follow instructions
- ✅ **No Complex State Management** - Each script runs independently
- ✅ **Better User Experience** - Natural workflow that matches how users work
- ✅ **Enhanced Documentation** - Crystal clear instructions with examples
- ✅ **Comprehensive Test Coverage** - 416 passing tests with 0 failures
- ✅ **Stable Docker Infrastructure** - Improved container stability and connection handling

**Key Features:**
- **Separated Scripts** - Rename, customize, and setup are now separate steps
- **Clear Instructions** - Each step has detailed, easy-to-follow directions
- **Error Prevention** - Scripts check prerequisites and provide helpful error messages
- **Comprehensive Testing** - Full test suite covering all functionality

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
- [Customization Improvements](tests/template_tests/customization_improvements.md)

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

*This project was created using a FastAPI template. For template-specific information, see the `docs/` folder.* # Test comment for CI validation workflow
