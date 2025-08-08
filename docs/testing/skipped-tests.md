## Skipped tests in this template

Some tests are intentionally skipped to keep the default test run fast and infra-free. Enable them when you configure the corresponding features/services.

### Why tests are skipped

- Feature flags are disabled by default (websockets, rate limiting, Redis, Celery, Sentry)
- Some scenarios require infrastructure the template doesn’t provision (Redis, broker/backend, DSN)
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

### Currently skipped areas (and where)

- Rate limit exceeded tests when `ENABLE_RATE_LIMITING=false`
  - `tests/api/auth/test_register_rate_limit_exceeded.py`
  - `tests/api/auth/test_password_reset_rate_limit_exceeded.py`
  - `tests/api/auth/test_oauth_rate_limit_exceeded.py`
  - `tests/api/auth/test_login_invalid_email_and_rate_limit.py`
- Websocket enabled-path tests when `ENABLE_WEBSOCKETS=false`
  - `tests/api/integrations/test_websockets.py`
  - `tests/api/integrations/test_websockets_enabled.py`
- Redis detailed readiness checks when `ENABLE_REDIS=false`
  - `tests/api/system/test_health_redis.py`
- Celery smoke tests (broker not configured in template)
  - `tests/services/background/test_celery_smoke.py`
- Sentry initialization path (DSN not provided in template)
  - `tests/services/external/test_sentry_smoke.py`

These skips were observed in the latest run:

```
SKIPPED tests/api/auth/test_login_invalid_email_and_rate_limit.py::...  (Rate limiting not enabled)
SKIPPED tests/api/auth/test_oauth_rate_limit_exceeded.py::...          (Rate limiting not configured at app startup)
SKIPPED tests/api/auth/test_password_reset_rate_limit_exceeded.py::... (Rate limiting not configured at app startup)
SKIPPED tests/api/auth/test_register_rate_limit_exceeded.py::...       (Rate limiting not configured at app startup)
SKIPPED tests/api/integrations/test_websockets.py::...                 (Websockets disabled in settings)
SKIPPED tests/api/integrations/test_websockets_enabled.py::...         (Websockets not enabled)
SKIPPED tests/services/background/test_celery_smoke.py::...            (Celery broker not configured)
SKIPPED tests/services/external/test_sentry_smoke.py::...              (Sentry DSN not configured)
```

### Recommendation

Keep feature-dependent tests guarded by flags until your project uses those features. Once enabled in production, unskip or remove the guards and provide the necessary test doubles/infra in CI.

