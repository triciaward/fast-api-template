# Test Organization

This template includes a comprehensive test suite organized by functionality. When you build your application, you can use this structure as a starting point for your own tests.

## 📁 Test Structure

```
tests/
├── api/                    # API endpoint tests
│   ├── test_admin_views_service.py
│   ├── test_search_filter_api.py
│   └── ...
├── core/                   # Core functionality tests
│   ├── test_models.py
│   ├── test_crud_user.py
│   ├── test_core_security.py
│   ├── test_cors.py
│   ├── test_error_responses.py
│   ├── test_logging.py
│   ├── test_main.py
│   ├── test_optional_features.py
│   ├── test_rate_limiting.py
│   ├── test_refresh_token.py
│   ├── test_security_headers.py
│   ├── test_soft_delete.py
│   └── test_superuser.py
├── services/               # Service layer tests
│   ├── test_celery.py
│   ├── test_email_service.py
│   ├── test_oauth_service.py
│   ├── test_rate_limiter_service.py
│   ├── test_redis_service.py
│   ├── test_refresh_token_service.py
│   ├── test_sentry.py
│   └── test_websocket_service.py
├── utils/                  # Utility function tests
│   ├── test_audit_log.py
│   ├── test_pagination.py
│   ├── test_search_filter.py
│   └── test_search_filter_patch.py
├── integration/            # Integration tests
│   ├── test_async_basic.py
│   ├── test_connection_pooling.py
│   └── test_pgbouncer_integration.py
├── scripts/                # Script and tool tests
│   ├── test_ci_validation.py
│   ├── test_crud_generator.py
│   ├── test_customize_template.py
│   ├── test_precommit.py
│   ├── test_setup_scripts.py
│   └── test_template_protection.py
├── conftest.py            # Shared test fixtures
└── README.md              # This file
```

## 🎯 Test Categories

### API Tests (`api/`)
Tests for API endpoints, request/response handling, and API-specific functionality.

### Core Tests (`core/`)
Tests for core application functionality:
- Database models and CRUD operations
- Authentication and security
- Configuration and settings
- Error handling and validation
- Core business logic

### Service Tests (`services/`)
Tests for service layer components:
- Email service
- OAuth integration
- Rate limiting
- Redis operations
- WebSocket handling
- Background tasks (Celery)
- Monitoring (Sentry)

### Utility Tests (`utils/`)
Tests for utility functions and helpers:
- Pagination utilities
- Search and filtering
- Audit logging
- Helper functions

### Integration Tests (`integration/`)
Tests that verify multiple components work together:
- Database connection pooling
- Async operations
- External service integration

### Script Tests (`scripts/`)
Tests for development tools and scripts:
- Template customization
- CRUD generation
- CI/CD validation
- Pre-commit hooks

## 🚀 Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run tests by category:
```bash
# API tests only
pytest tests/api/

# Core functionality tests
pytest tests/core/

# Service layer tests
pytest tests/services/

# Integration tests
pytest tests/integration/
```

### Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## 📝 Adding Your Own Tests

When building your application, follow this structure:

1. **API endpoints** → `tests/api/`
2. **Business logic** → `tests/core/`
3. **Custom services** → `tests/services/`
4. **Helper functions** → `tests/utils/`
5. **Complex workflows** → `tests/integration/`

### Example: Adding a new API endpoint test
```python
# tests/api/test_my_new_endpoint.py
import pytest
from fastapi.testclient import TestClient

def test_my_new_endpoint(client: TestClient):
    response = client.get("/api/v1/my-endpoint")
    assert response.status_code == 200
```

## 🔧 Test Configuration

- **Shared fixtures**: `tests/conftest.py`
- **Test database**: Configured for isolated testing
- **Mock services**: External services are mocked
- **Async support**: Both sync and async tests included

## 📊 Coverage Goals

- **Template**: ~60% coverage (infrastructure tested)
- **Your app**: Aim for 80%+ coverage on business logic
- **Critical paths**: 100% coverage on security and data operations

This organization makes it easy to find, write, and maintain tests as your application grows!
