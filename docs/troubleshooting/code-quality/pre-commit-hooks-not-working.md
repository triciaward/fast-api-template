# Pre-commit Hooks Not Working

**Status**: ✅ **RESOLVED** - Now works out of the box for new projects!

**Problem**: Your commits go through but code quality checks (Black, Ruff, MyPy) aren't running automatically.

## 🚨 Symptoms

- ✅ **Template protection works** - Prevents accidental commits to template repository
- ❌ **Code quality checks don't run** - No automatic formatting, linting, or type checking
- ❌ **`pre-commit --version` command not found**
- ❌ **Commits succeed without code validation**

## 🔍 Root Cause

The FastAPI template has **two pre-commit systems**:

1. **Template Protection Hook** (`scripts/git-hooks/pre-commit`) - ✅ **Working**
   - Prevents commits to the template repository
   - Installed automatically by setup script
   - Basic bash script that runs before commits

2. **Code Quality Hooks** (`.pre-commit-config.yaml`) - ❌ **Not Working**
   - Runs Black (code formatting)
   - Runs Ruff (linting)
   - Runs MyPy (type checking)
   - Requires the `pre-commit` Python package

**What Happened**: The setup script only installed the template protection hook, but missed installing the `pre-commit` framework that runs the code quality checks.

## 🛠️ Quick Fix

**Option 1: Use the Fix Script (Recommended)**
```bash
# Run this script to fix everything automatically
./scripts/setup/fix_precommit_setup.sh
```

**Option 2: Manual Fix**
```bash
# 1. Activate your virtual environment
source venv/bin/activate  # or venv\\Scripts\\activate on Windows

# 2. Install pre-commit
pip install pre-commit

# 3. Install the git hooks
pre-commit install

# 4. Run initial check on all files
pre-commit run --all-files
```

## ✅ What You Get After Fix

- **Template Protection**: Prevents accidental commits to template repository
- **Code Formatting**: Black automatically formats your Python code
- **Linting**: Ruff catches code quality issues
- **Type Checking**: MyPy validates type annotations
- **Automatic**: All checks run before every commit

## 🔧 Verification

After fixing, verify it's working:

```bash
# Check pre-commit is installed
pre-commit --version

# Check hooks are installed
ls -la .git/hooks/ | grep pre-commit

# Test a commit (should run all checks)
git add .
git commit -m "test: verify pre-commit hooks working"
```

## 🚀 Why This Happened (Now Fixed!)

**Previous Issue**: The setup script only installed template protection but missed the pre-commit framework.

**Root Causes**:
1. **Template Protection Priority**: The setup script prioritized protecting the template repository
2. **Framework Dependency**: Code quality hooks require the `pre-commit` Python package
3. **Installation Order**: The pre-commit framework installation was happening before the virtual environment was ready
4. **Missing Dependency**: `pre-commit` was only in `requirements-dev.txt`, not in the main `requirements.txt`

**✅ Now Fixed**: The setup script automatically installs both systems in the correct order.

## 🎯 Prevention

For future projects, the updated setup script will:
1. Install template protection hooks first
2. Install the `pre-commit` framework
3. Install code quality hooks
4. Run initial validation

## 📚 Related Documentation

- **[Main README](../../../README.md#-pre-commit-setup-troubleshooting)** - Quick troubleshooting guide
- **[Code Quality Guide](../CODE_QUALITY_README.md)** - General code quality issues
- **[Setup Guide](../../../docs/TEMPLATE_README.md)** - Complete project setup instructions

## 🆘 Still Having Issues?

If the fix script doesn't work:

1. **Check virtual environment**: Make sure you're in the right Python environment
2. **Check permissions**: Ensure the scripts are executable
3. **Check git status**: Make sure you're in a git repository
4. **Check dependencies**: Verify all requirements are installed

```bash
# Debug commands
which python
pip list | grep pre-commit
git status
ls -la scripts/setup/
```
