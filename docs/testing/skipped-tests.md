## Skipped tests in this template

Some tests are intentionally skipped to keep the default test run fast and infra-free. Enable them when you configure the corresponding features/services.

### Why tests are skipped

- Feature flags are disabled by default (websockets, rate limiting, Redis, Celery, Sentry)
- Some scenarios require infrastructure the template doesn't provision (Redis, broker/backend, DSN)
- A few tests are placeholders to demonstrate structure and best practices

### How to enable the skipped tests

Set environment variables accordingly, for example:

```bash
# Rate limiting scenarios
ENABLE_RATE_LIMITING=true pytest -q

# Websockets endpoints
ENABLE_WEBSOCKETS=true pytest -q

# Redis-backed checks (requires Redis)
ENABLE_REDIS=true pytest -q

# Celery smoke tests (requires broker/result backend)
ENABLE_CELERY=true \
CELERY_BROKER_URL=redis://localhost:6379/0 \
CELERY_RESULT_BACKEND=redis://localhost:6379/0 \
pytest -q

# Sentry tests (requires DSN)
ENABLE_SENTRY=true \
SENTRY_DSN=https://public@sentry.example/1 \
pytest -q
```

### Currently skipped areas (and why)

**Total: 10 skipped tests across 8 files**

#### Rate Limiting Tests (4 tests, 4 files)
These tests verify rate limiting behavior but are skipped because rate limiting is disabled by default:

- **`tests/api/auth/test_login_invalid_email_and_rate_limit.py`** (1 test)
  - `test_login_rate_limited` - Tests repeated login attempts hitting rate limits
  - **Why skipped**: `ENABLE_RATE_LIMITING=false` by default

- **`tests/api/auth/test_oauth_rate_limit_exceeded.py`** (1 test)
  - `test_oauth_rate_limit_exceeded` - Tests OAuth endpoint rate limiting
  - **Why skipped**: Rate limiter not configured at app startup

- **`tests/api/auth/test_register_rate_limit_exceeded.py`** (1 test)
  - `test_register_rate_limit_exceeded` - Tests registration endpoint rate limiting
  - **Why skipped**: Rate limiter not configured at app startup

- **`tests/api/auth/test_password_reset_rate_limit_exceeded.py`** (1 test)
  - `test_password_reset_rate_limit_exceeded` - Tests password reset rate limiting
  - **Why skipped**: Rate limiter not configured at app startup

#### Websocket Tests (4 tests, 2 files)
These tests verify websocket functionality but are skipped because websockets are disabled by default:

- **`tests/api/integrations/test_websockets.py`** (1 test)
  - `test_websocket_echo_flow_with_testclient` - Tests basic websocket echo functionality
  - **Why skipped**: `ENABLE_WEBSOCKETS=false` by default

- **`tests/api/integrations/test_websockets_enabled.py`** (3 tests)
  - `test_websocket_echo_when_enabled` - Tests websocket echo when enabled
  - `test_websocket_room_and_broadcast_when_enabled` - Tests room-based messaging
  - `test_websocket_status_endpoint_when_enabled` - Tests websocket status endpoint
  - **Why skipped**: `ENABLE_WEBSOCKETS=false` by default

#### Infrastructure Tests (2 tests, 2 files)
These tests verify external service integration but are skipped because the infrastructure isn't provisioned:

- **`tests/services/background/test_celery_smoke.py`** (1 test)
  - `test_submit_task_eager_mode` - Tests Celery task submission
  - **Why skipped**: Celery broker not configured in template by default

- **`tests/services/external/test_sentry_smoke.py`** (1 test)
  - `test_sentry_init_when_enabled` - Tests Sentry initialization
  - **Why skipped**: Sentry DSN not configured in template

### Test run summary

When you run the full test suite, you'll see output like:

```
======================= 561 passed, 10 skipped in 8.79s ========================
```

The skipped tests are indicated by `.s` in the progress output:
- `.s` = 1 test skipped
- `sss` = 3 tests skipped
- etc.

### Recommendation

Keep feature-dependent tests guarded by flags until your project uses those features. Once enabled in production, unskip or remove the guards and provide the necessary test doubles/infra in CI.

**To see which specific tests are skipped**, run:
```bash
python -m pytest --tb=short -q -v 2>&1 | grep -E "(SKIPPED|\.s)"
```

