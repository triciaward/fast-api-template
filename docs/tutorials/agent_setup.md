# 🤖 AI Agent Setup Guide

**IMPORTANT: Read this before making any changes to the project!**

This guide tells AI agents exactly how to work with this FastAPI template project. Follow these instructions precisely to avoid errors and ensure changes work correctly.

## 🚨 **CRITICAL: Always Start Here**

### **1. Environment Setup (REQUIRED First Step)**
```bash
# ALWAYS activate the virtual environment first
source venv/bin/activate

# Verify you're in the right environment
which python
# Should show: /Users/triciaward/Coding Projects/fast-api-template/venv/bin/python

# Verify you're in the project directory
pwd
# Should show: /Users/triciaward/Coding Projects/fast-api-template
```

### **2. Project Structure Understanding**
```
fast-api-template/
├── venv/                    # Python virtual environment (ALWAYS activate first)
├── app/                     # Main FastAPI application code
├── tests/                   # 173 test files (98.2% coverage)
├── scripts/                 # Setup and utility scripts
├── docker-compose.yml       # Database and services
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── .cursorrules            # AI optimization rules (already configured)
```

## 🐍 **Python Environment Rules**

### **❌ NEVER DO THIS:**
- Don't run `python` without activating venv
- Don't use system Python
- Don't install packages globally

### **✅ ALWAYS DO THIS:**
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Verify activation
which python
pip list | grep fastapi

# 3. Now run your commands
python -m pytest
python scripts/setup/setup_project.py
```

## 🐳 **Docker Services Rules**

### **Database and Services:**
```bash
# Start database and services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### **❌ NEVER DO THIS:**
- Don't try to install PostgreSQL locally
- Don't modify database connection strings manually
- Don't start services without Docker

## 🧪 **Testing Rules**

### **Running Tests:**
```bash
# Activate venv first
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/api/auth/test_login.py

# Run with coverage
pytest --cov=app

# Run optional feature tests
ENABLE_WEBSOCKETS=true pytest tests/api/integrations/
```

### **❌ NEVER DO THIS:**
- Don't run tests without activating venv
- Don't modify test files without understanding the 173-file structure
- Don't skip the conftest.py configuration

## 🔧 **Development Workflow Rules**

### **Code Quality:**
```bash
# Activate venv first
source venv/bin/activate

# Format code
black .

# Lint code
ruff check .

# Type checking
mypy app/

# Run all quality checks
./scripts/development/validate_ci.sh
```

### **Git Operations:**
```bash
# Check status
git status

# Add changes
git add .

# Commit with descriptive message
git commit -m "Descriptive message about changes"

# Push to remote
git push origin main
```

## 📁 **File Modification Rules**

### **Adding New Features:**
1. **Follow the 6-step pattern** from `docs/tutorials/building-a-feature.md`
2. **Use existing patterns** - Copy from similar features
3. **Maintain test coverage** - Add tests for new functionality
4. **Update documentation** - Keep tutorials current

### **Modifying Existing Code:**
1. **Understand the current structure** before making changes
2. **Follow naming conventions** - Keep consistency
3. **Update tests** if you change behavior
4. **Check for breaking changes** in dependent code

## 🚀 **Common Agent Mistakes to Avoid**

### **1. Environment Issues:**
- ❌ Running `python` without venv activation
- ❌ Using wrong Python interpreter
- ❌ Installing packages globally

### **2. Project Structure Issues:**
- ❌ Creating files in wrong locations
- ❌ Ignoring existing patterns
- ❌ Breaking the 173-test-file organization

### **3. Service Issues:**
- ❌ Trying to start services without Docker
- ❌ Modifying database configuration manually
- ❌ Ignoring docker-compose.yml setup

### **4. Testing Issues:**
- ❌ Running tests without venv
- ❌ Modifying test structure without understanding
- ❌ Breaking existing test coverage

## 💡 **Best Practices for AI Agents**

### **1. Always Start with Environment:**
```bash
source venv/bin/activate
which python
pwd
```

### **2. Understand Before Changing:**
- Read existing code patterns
- Check similar implementations
- Understand the 6-step feature building process

### **3. Test Your Changes:**
- Run relevant tests
- Check for errors
- Verify functionality works

### **4. Follow Project Patterns:**
- Use existing naming conventions
- Follow the established architecture
- Maintain test coverage

## 🎯 **Quick Reference Commands**

```bash
# Environment
source venv/bin/activate

# Services
docker-compose up -d

# Testing
pytest

# Quality
black . && ruff check . && mypy app/

# Git
git add . && git commit -m "Message" && git push origin main
```

## 🚨 **Emergency Stop**

**If something goes wrong:**
1. **Stop current operations** - Ctrl+C
2. **Check environment** - `which python`, `pwd`
3. **Verify services** - `docker-compose ps`
4. **Read this guide again** - Make sure you followed all rules

---

**Remember: This project has 173 test files and 98.2% coverage. If you break something, the tests will tell you!** 🧪✅

**Follow these rules and you'll work efficiently with this FastAPI template!** 🚀
