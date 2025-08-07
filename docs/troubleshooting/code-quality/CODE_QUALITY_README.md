# Code Quality Issues

This folder contains troubleshooting guides for code quality, formatting, and dependency issues.

## 📁 Available Guides

### **[Bcrypt Warning Explanation](./bcrypt-warning-explanation.md)**
- Understanding the bcrypt/passlib compatibility warning
- Why this warning is safe to ignore
- Security verification and functionality confirmation
- Warning management and suppression
- Technical details of the compatibility issue

### **[Black vs Mypy Type Ignore Conflict](./black-mypy-type-ignore-conflict.md)**
- SQLAlchemy + Pydantic type conflicts
- Black formatter vs mypy type checker issues
- IDE auto-formatting problems
- Type ignore comment placement issues
- Proper type conversion solutions

## 🚀 Quick Solutions

### Handle Bcrypt Warning:
```bash
# The warning is safe to ignore - password hashing works correctly

```

### Fix Black/Mypy Conflicts:
```python
# Instead of type ignores, use proper type conversion:
# BEFORE (problematic):
result = SomeResponse(field=sqlalchemy_column)  # type: ignore[arg-type]

# AFTER (proper):
converted_value = None
if sqlalchemy_column is not None:
    converted_value = proper_conversion(sqlalchemy_column)
result = SomeResponse(field=converted_value)
```

### Code Quality Checks:
```bash
# Check formatting
python -m black --check .

# Check linting
python -m ruff check .

# Check types
python -m mypy app/ scripts/

# Fix formatting
python -m black .

# Fix linting
python -m ruff check . --fix
```

## 🔧 Known Issues

### Bcrypt Warning
- **Status**: Known compatibility issue between passlib and bcrypt
- **Impact**: None - password hashing works correctly
- **Solution**: Warning is suppressed in test configuration
- **Security**: No security impact - bcrypt still functions properly

### Black/Mypy Conflicts
- **Status**: Ongoing issue with SQLAlchemy + Pydantic type compatibility
- **Impact**: Type checking conflicts with code formatting
- **Solution**: Use proper type conversion instead of type ignores
- **Best Practice**: Convert types explicitly rather than ignoring

## 📞 Getting Help

If you encounter code quality issues not covered in these guides:
1. Check the main [troubleshooting index](../TROUBLESHOOTING_README.md)
2. Review the [code quality tools](../../tutorials/testing-and-development.md)
3. Run validation script: `./scripts/development/validate_ci.sh`
4. Check tool documentation for latest best practices
