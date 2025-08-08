# Setup Issues Troubleshooting Guide

This guide documents common issues encountered during project setup and their solutions.

## 🚨 Common Setup Issues & Solutions

### 1. **Wrong Python Version in Virtual Environment** ⚠️ HIGH PRIORITY

**Problem**: Setup script creates venv with system Python (e.g., 3.9) instead of required Python 3.11+, causing import errors:
```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

**Root Cause**: The script used `sys.executable` (current Python) instead of finding Python 3.11+.

**Solution**: 
- Fixed in template: Setup script now automatically detects and uses Python 3.11+ 
- Validates Python version before creating virtual environment
- Provides clear error messages if Python 3.11+ is not available

**Manual Fix**:
```bash
# Remove old venv and recreate with correct Python version
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Prevention**: The setup script now includes Python version validation:
- Searches for python3.11, python3.12, python3.13 first
- Falls back to python3.10 (minimum supported)
- Exits with clear error if no suitable Python version found

### 2. **Missing `alembic.ini` Configuration File**

**Problem**: Setup script fails with "No config file 'alembic.ini' found"
```
FAILED: No config file 'alembic.ini' found, or file has no '[alembic]' section
```

**Root Cause**: The `alembic.ini` file wasn't properly customized during the template customization process.

**Solution**: 
- The template now includes proper `alembic.ini` customization in the `customize_template.py` script
- The file is automatically updated with the correct database name during customization

**Manual Fix** (if needed):
```bash
# Check if alembic.ini exists
ls -la alembic.ini

# If missing, copy from template or create with proper configuration
cp /path/to/original/alembic.ini .
# Then update the database URL in the file
```

### 3. **Alembic Configuration Interpolation Error**

**Problem**: The `version_num_format = %04d` causes a configparser error:
```
configparser.InterpolationSyntaxError: '%' must be followed by '%' or '(', found: '%04d'
```

**Root Cause**: Incorrect escaping in the version number format string.

**Solution**: 
- Fixed in template: `version_num_format = %%04d`
- The double `%%` properly escapes the percent sign for configparser
- The setup script now generates the correct format automatically

**Manual Fix**:
```ini
# In alembic.ini, change:
# version_num_format = %04d
# To:
version_num_format = %%04d
```

### 4. **Database Tables Already Existed**

**Problem**: Migration failed because tables already existed:
```
psycopg2.errors.DuplicateTable: relation "users" already exists
```

**Root Cause**: Database already had tables but no migration history.

**Solution**: 
- The setup script now detects this condition and uses `alembic stamp head` to mark migrations as applied
- This preserves existing data while establishing proper migration history

**Manual Fix**:
```bash
# If you encounter this error, run:
alembic stamp head
# This marks all existing migrations as applied without running them
```

### 4. **Setup Script Directory Check Logic Error**

**Problem**: The setup script had incorrect logic checking for the wrong directory name.

**Root Cause**: Outdated directory checking logic in setup scripts.

**Solution**: 
- Fixed in template: Scripts now check for the correct template name
- Proper error messages guide users to run scripts in the correct order

**Manual Fix**:
```bash
# Ensure you're in the renamed project directory (not fast-api-template)
# The directory should end with _backend
pwd
# Should show: /path/to/yourproject_backend
```

### 5. **Superuser Creation Issues**

#### 5a. **Module Import Error**

**Problem**: Bootstrap script fails with import error:
```
ModuleNotFoundError: No module named 'app'
```

**Root Cause**: Python path not set correctly.

**Solution**: 
- Fixed in template: `PYTHONPATH=.` is now set automatically
- The setup script ensures proper environment variables

**Manual Fix**:
```bash
# Set PYTHONPATH before running the script
export PYTHONPATH=.
python app/bootstrap_superuser.py
```

#### 5b. **Username Validation Error**

**Problem**: Superuser creation failed because "admin" is a reserved username:
```
Value error, Username is reserved and cannot be used [type=value_error, input_value='admin']
```

**Root Cause**: The username "admin" is in the reserved words list.

**Solution**: 
- Fixed in template: Improved username generation logic
- Creates usernames like `admin_domain` instead of just `admin`
- Validates and fixes usernames automatically

**Manual Fix**:
```bash
# Use a different email that generates a non-reserved username
export FIRST_SUPERUSER="admin@yourproject.com"
export FIRST_SUPERUSER_PASSWORD="Admin123!"
python app/bootstrap_superuser.py
```

#### 5c. **Password Validation Error**

**Problem**: Password didn't meet complexity requirements:
```
Value error, Password must contain at least one uppercase letter
```

**Root Cause**: Password didn't meet the strong password requirements.

**Solution**: 
- Fixed in template: Uses `Admin123!` as default password
- Meets all requirements: uppercase, lowercase, number, special character
- Validates and fixes passwords automatically

**Manual Fix**:
```bash
# Use a strong password that meets requirements
export FIRST_SUPERUSER_PASSWORD="Admin123!"
python app/bootstrap_superuser.py
```

### 6. **Bcrypt Warning (Non-Critical)**

**Problem**: Warning about bcrypt version reading:
```
WARNING:passlib.handlers.bcrypt:(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**Root Cause**: Version compatibility issue between passlib and bcrypt.

**Solution**: 
- This is a non-critical warning that doesn't affect functionality
- The superuser is still created successfully despite this warning
- Can be ignored or fixed by updating dependencies

**Manual Fix** (optional):
```bash
# Update bcrypt to latest version
pip install --upgrade bcrypt
```

## 🔧 **Prevention Measures**

The template now includes these improvements to prevent issues:

1. **Python version validation** - Automatically detects and uses Python 3.11+ for virtual environment
2. **Proper alembic.ini customization** - Fixed percent sign escaping (%%04d format)
3. **Smart database state detection** - Handles existing tables gracefully
4. **Improved error handling** - Better status reporting for migrations and superuser creation
5. **Enhanced validation checks** - Verifies Python version, imports, and configuration
6. **Clear status reporting** - Accurate completion messages showing what succeeded/failed

## 🚀 **Quick Setup Checklist**

To ensure a smooth setup experience:

1. ✅ Run `./scripts/rename_template.sh` first
2. ✅ Restart VS Code and open the renamed directory
3. ✅ Run `./scripts/customize_template.sh` 
4. ✅ Run `./scripts/setup_project.sh`
5. ✅ Verify the API is running at http://localhost:8000/health

## 📞 **Getting Help**

If you encounter issues not covered in this guide:

1. Check the main [TROUBLESHOOTING_README.md](../TROUBLESHOOTING_README.md) for setup instructions
2. Review the [tutorials](../tutorials/) for detailed walkthroughs
3. Check the [template customization log](../TEMPLATE_CUSTOMIZATION.md) if it exists
4. Look at the [test files](../../tests/) for examples of proper configuration

## 🔄 **Template Updates**

This template is continuously improved based on user feedback. If you encounter new issues:

1. Document the exact error message and steps to reproduce
2. Check if the issue is already addressed in this guide
3. Consider contributing a fix or reporting the issue

---

*Last updated: Template version with comprehensive setup fixes* 