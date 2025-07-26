# Testing and Development

This guide covers testing strategies, development workflows, and how to implement skipped tests in the FastAPI template.

## Test Structure

The template includes comprehensive tests organized into several categories:

- **Core Tests**: Basic functionality tests that should always pass
- **Template Tests**: Tests specifically for template functionality (marked with `@pytest.mark.template_only`)
- **Integration Tests**: Tests that require external services or complex setup
- **Skipped Tests**: Tests that are intentionally skipped due to template limitations

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run only template tests
pytest -m "template_only"

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/template_tests/test_admin.py
```

### Test Environment Setup

The template uses Docker containers for testing:

```bash
# Start test database
docker-compose up -d postgres

# Create test database
docker exec -it ${COMPOSE_PROJECT_NAME:-fast-api-template}-postgres-1 psql -U postgres -c "CREATE DATABASE fastapi_template_test;"

# Run tests
pytest
```

## 🧪 Template Tests

The template includes a comprehensive suite of template-specific tests that verify the setup and configuration work correctly.

### Template Test Categories

#### Setup and Configuration Tests
```bash
# Test setup scripts
pytest tests/template_tests/test_setup_scripts.py

# Test configuration loading
pytest tests/template_tests/test_config.py

# Test environment validation
pytest tests/template_tests/test_environment.py
```

#### Development Tools Tests
```bash
# Test pre-commit hooks
pytest tests/template_tests/test_precommit.py

# Test CRUD scaffolding
pytest tests/template_tests/test_crud_generator.py

# Test verification scripts
pytest tests/template_tests/test_verification.py
```

#### Model and Schema Tests
```bash
# Test separated models
pytest tests/template_tests/test_models.py

# Test schema validation
pytest tests/template_tests/test_schemas.py

# Test CRUD operations
pytest tests/template_tests/test_crud_user.py
```

#### Template Customization Tests
```bash
# Test template customization script
pytest tests/template_tests/test_customize_template.py

# Test customization functionality
pytest tests/template_tests/test_customize_template.py -v
```

The template customization tests verify that the customization script correctly transforms all template references into project-specific names, including:
- File content replacement
- Configuration updates
- Documentation changes
- Git remote detection
- Error handling and safety features

### Template Test Features

#### Automatic Test Isolation
Template tests are automatically excluded from regular test runs:

```python
# In tests/conftest.py
def pytest_configure(config):
    """Configure pytest to exclude template tests by default."""
    config.addinivalue_line(
        "markers",
        "template_only: marks tests as template-specific (excluded by default)"
    )
    
    # Set default marker expression to exclude template tests
    if not config.getoption("markexpr"):
        config.option.markexpr = "not template_only"
```

#### Template Test Markers
```python
@pytest.mark.template_only
class TestSetupScripts:
    """Test the comprehensive setup script functionality."""
    
    def test_setup_script_creates_env_file(self):
        """Test that the setup script creates a .env file when it doesn't exist."""
        # Test implementation
```

#### Running Template Tests
```bash
# Run only template tests
pytest -m "template_only"

# Run template tests with coverage
pytest -m "template_only" --cov=app

# Run specific template test category
pytest tests/template_tests/test_setup_scripts.py -v
pytest tests/template_tests/test_customize_template.py -v
```

## Skipped Tests and Implementation Guide

Several tests are intentionally skipped in the template due to complex setup requirements. This section explains why they're skipped and how to implement them properly.

### Why Tests Are Skipped

Tests are skipped for the following reasons:

1. **Template Limitations**: Some features require complex setup not suitable for a template
2. **External Dependencies**: Tests requiring external services (email, OAuth, etc.)
3. **Configuration Complexity**: Tests needing extensive configuration
4. **Test Isolation Issues**: Tests requiring proper database cleanup and isolation

### Categories of Skipped Tests

#### 1. Authentication Tests

**Files**: `tests/template_tests/test_admin.py`, `tests/template_tests/test_api_auth.py`

**Why Skipped**: These tests require proper JWT configuration and user verification workflows that are complex to set up in a template.

**To Implement**:
```python
# Remove the skip decorator
# @pytest.mark.skip(reason="Template test - requires proper user authentication setup")

def test_admin_user_crud_operations(db_session: AsyncSession) -> None:
    """Test admin CRUD operations."""
    # Set up proper authentication
    # Configure JWT tokens
    # Create test users with proper roles
    # Run the test
```

#### 2. Email Verification Tests

**Files**: `tests/template_tests/test_auth_email_verification.py`

**Why Skipped**: These tests require a working email service (SMTP) configuration.

**To Implement**:
```python
# Configure SMTP settings in .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Remove skip decorator and run tests
pytest tests/template_tests/test_auth_email_verification.py
```

#### 3. OAuth Tests

**Files**: `tests/template_tests/test_oauth.py`

**Why Skipped**: These tests require OAuth provider configuration (Google, Apple, etc.).

**To Implement**:
```python
# Configure OAuth settings in .env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id

# Remove skip decorator and run tests
pytest tests/template_tests/test_oauth.py
```

#### 4. Celery Tests

**Files**: `tests/template_tests/test_celery.py`

**Why Skipped**: These tests require a running Celery worker and Redis.

**To Implement**:
```bash
# Start Redis and Celery
docker-compose up -d redis
celery -A app.services.celery_app worker --loglevel=info

# Run Celery tests
pytest tests/template_tests/test_celery.py
```

#### 5. Test Isolation Issues

**Files**: `tests/template_tests/test_auth_validation.py`

**Why Skipped**: These tests require proper database cleanup between tests.

**To Implement**:
```python
# Set up proper test isolation
@pytest.fixture(autouse=True)
def clean_database():
    """Clean database between tests."""
    # Clean up test data
    yield
    # Clean up after test
```

### Implementation Steps

1. **Identify Required Services**: Check what external services the test needs
2. **Configure Environment**: Set up the required environment variables
3. **Start Services**: Ensure all required services are running
4. **Remove Skip Decorator**: Remove the `@pytest.mark.skip` decorator
5. **Fix Test Issues**: Address any test-specific issues
6. **Run Tests**: Execute the tests and verify they pass

## Development Workflow

### Setting Up Development Environment

#### 1. Automated Setup
```bash
# Use the setup script
./scripts/setup_project.sh

# This handles:
# - Virtual environment creation
# - Dependency installation
# - Environment configuration
# - Database setup
# - Verification
```

#### 2. Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Start database
docker-compose up -d postgres

# Run migrations
alembic upgrade head
```

### Code Quality Tools

#### Pre-commit Hooks
```bash
# Install pre-commit hooks
./scripts/install_precommit.sh

# Run hooks manually
pre-commit run --all-files

# Run specific hooks
pre-commit run ruff --all-files
pre-commit run black --all-files
pre-commit run mypy --all-files
```

#### Manual Code Quality Checks
```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/

# Run all quality checks
./scripts/lint.sh
```

### Development Scripts

#### Setup and Verification
```bash
# Setup project
./scripts/setup_project.sh

# Fix common issues
./scripts/fix_common_issues.sh

# Verify setup
python scripts/verify_setup.py
```

#### Testing and Debugging
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/template_tests/test_auth.py -v

# Debug tests
pytest tests/template_tests/test_auth.py -v -s --pdb
```

#### Database Management
```bash
# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Reset database
alembic downgrade base
alembic upgrade head
```

## Testing Best Practices

### 1. Test Organization

#### File Structure
```
tests/
├── conftest.py              # Global test configuration
├── template_tests/          # Template-specific tests
│   ├── conftest.py         # Template test configuration
│   ├── test_setup_scripts.py
│   ├── test_models.py
│   ├── test_auth.py
│   └── ...
└── [your_tests]/           # Your application tests
```

#### Test Naming
```python
# Use descriptive test names
def test_user_registration_with_valid_data():
    """Test user registration with valid input data."""

def test_user_registration_with_invalid_email():
    """Test user registration with invalid email format."""

def test_user_registration_with_existing_email():
    """Test user registration with already existing email."""
```

### 2. Test Data Management

#### Using Fixtures
```python
import pytest
from app.schemas.user import UserCreate

@pytest.fixture
def valid_user_data():
    """Provide valid user data for tests."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!"
    }

@pytest.fixture
def user_create_schema(valid_user_data):
    """Provide UserCreate schema for tests."""
    return UserCreate(**valid_user_data)

def test_create_user(db_session, user_create_schema):
    """Test creating a user with valid data."""
    user = crud_user.create(db_session, obj_in=user_create_schema)
    assert user.email == user_create_schema.email
```

#### Database Cleanup
```python
@pytest.fixture(autouse=True)
def clean_database(db_session):
    """Clean database between tests."""
    yield
    # Clean up after each test
    db_session.rollback()
```

### 3. Test Isolation

#### Database Transactions
```python
@pytest.fixture
def db_session():
    """Provide database session with transaction rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

#### Mocking External Services
```python
from unittest.mock import patch

def test_email_sending(mock_smtp):
    """Test email sending with mocked SMTP."""
    with patch('app.services.email_service.send_email') as mock_send:
        mock_send.return_value = True
        
        result = send_verification_email("user@example.com")
        
        assert result is True
        mock_send.assert_called_once()
```

### 4. Assertion Best Practices

#### Descriptive Assertions
```python
# Good: Descriptive assertion
assert response.status_code == 201, f"Expected 201, got {response.status_code}"

# Good: Check multiple conditions
data = response.json()
assert "id" in data, "Response should contain user ID"
assert data["email"] == user_data["email"], "Email should match"
assert "password" not in data, "Password should not be returned"

# Good: Use pytest assertions
import pytest
pytest.raises(ValueError, create_user, invalid_data)
```

#### Testing Edge Cases
```python
def test_user_registration_edge_cases():
    """Test user registration with edge cases."""
    # Test empty data
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422
    
    # Test invalid email
    response = client.post("/api/v1/auth/register", json={
        "email": "invalid-email",
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 422
    
    # Test weak password
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "123"
    })
    assert response.status_code == 422
```

## Debugging Tests

### 1. Verbose Output
```bash
# Run tests with verbose output
pytest -v

# Run with even more detail
pytest -vv

# Show print statements
pytest -s
```

### 2. Debugging Failed Tests
```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb

# Show local variables on failure
pytest --tb=long
```

### 3. Test Discovery
```bash
# Show which tests would be run
pytest --collect-only

# Show test names
pytest --collect-only -q
```

### 4. Running Specific Tests
```bash
# Run test by name
pytest -k "test_user_registration"

# Run test by file
pytest tests/template_tests/test_auth.py

# Run test by class
pytest tests/template_tests/test_auth.py::TestAuthEndpoint

# Run test by method
pytest tests/template_tests/test_auth.py::TestAuthEndpoint::test_user_registration
```

## Continuous Integration

The template includes GitHub Actions for automated testing:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
```

## Performance Testing

### 1. Load Testing
```python
import asyncio
import aiohttp
import time

async def load_test():
    """Simple load test for API endpoints."""
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        # Make multiple concurrent requests
        tasks = []
        for i in range(100):
            task = session.get("http://localhost:8000/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Made 100 requests in {duration:.2f} seconds")
        print(f"Average response time: {duration/100:.3f} seconds")
```

### 2. Database Performance Testing
```python
import time
from app.crud import user as crud_user

def test_database_performance(db_session):
    """Test database query performance."""
    start_time = time.time()
    
    # Perform database operations
    users = crud_user.get_multi(db_session, limit=1000)
    
    end_time = time.time()
    duration = end_time - start_time
    
    assert duration < 1.0, f"Query took {duration:.2f} seconds, should be under 1 second"
```

## Troubleshooting

### Common Test Issues

1. **Database Connection Errors**:
   - Ensure PostgreSQL container is running
   - Check database URL configuration
   - Verify test database exists

2. **Import Errors**:
   - Make sure you're in the project root
   - Check that virtual environment is activated
   - Verify all dependencies are installed

3. **Test Isolation Issues**:
   - Use database transactions for test isolation
   - Clean up test data between tests
   - Use unique identifiers for test data

4. **Async Test Issues**:
   - Use `pytest-asyncio` for async tests
   - Mark async tests with `@pytest.mark.asyncio`
   - Use proper async fixtures

### Debugging Commands

```bash
# Check test environment
python -c "import app; print('App imports successfully')"

# Check database connection
python -c "from app.database.database import engine; print(engine.url)"

# Check configuration
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"

# Run tests with maximum verbosity
pytest -vvv --tb=long -s
```

## Best Practices Summary

1. **Test Organization**: Keep tests organized by feature/component
2. **Test Isolation**: Ensure tests don't interfere with each other
3. **Meaningful Assertions**: Write clear, descriptive test assertions
4. **Test Data Management**: Use fixtures for common test data
5. **Error Handling**: Test both success and failure scenarios
6. **Performance**: Keep tests fast and efficient
7. **Documentation**: Document complex test scenarios
8. **Template Tests**: Use template tests for setup verification
9. **Code Quality**: Run pre-commit hooks before committing
10. **Continuous Integration**: Set up automated testing in CI/CD

## Next Steps

Now that you understand testing and development:

1. **Write tests for your features** using the established patterns
2. **Implement skipped tests** as you add the required services
3. **Set up CI/CD** for automated testing
4. **Monitor test performance** and optimize slow tests
5. **Add integration tests** for complex workflows
6. **Set up test coverage reporting** to track code quality

For more advanced topics, check out:
- [Authentication Tutorial](authentication.md) - Testing authentication flows
- [Database Management](database-management.md) - Testing database operations
- [Deployment Tutorial](deployment-and-production.md) - Testing in production 