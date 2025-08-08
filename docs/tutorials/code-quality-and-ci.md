# Code quality and CI guardrails

This template ships with opinionated tooling for formatting, linting, and type-checking, wired for both local development (pre-commit) and CI.

## What you already have

- **Pre-commit hooks** (`.pre-commit-config.yaml`)
  - Ruff (lint, with `--fix --unsafe-fixes`)
  - Black (format)
  - Mypy (type check; extra stub packages installed)
  - Custom guard: prevents accidental commits/pushes to the template repo (`scripts/development/prevent_template_push.py`)
  - Install hooks:
    ```bash
    ./scripts/git-hooks/install_precommit.sh
    # or
    pre-commit install && pre-commit run --all-files
    ```
  - Optional Git hook to block pushing to the template's upstream:
    ```bash
    ./scripts/git-hooks/install_git_hooks.sh
    # Remove if you intentionally want to push:
    rm .git/hooks/pre-commit
    ```

- **CI workflow** (`.github/workflows/ci.yml`)
  - Lint job: runs Ruff (`ruff check .`) and Black (`black --check .`)
  - Type-check job: runs Mypy (`mypy app/ scripts/`)
  - Copies `.env.example` → `.env` for CI execution

- **Project config** (`pyproject.toml`)
  - Ruff rules tuned for modern Python and pragmatic ignores
  - Black formatter configured (line-length 88)
  - Mypy strict mode with sensible relaxations; defaults to checking the `app/` package
  - Coverage configuration included

- **Additional config files**
  - `mypy.ini` - MyPy configuration with per-module settings
  - `pytest.ini` - Pytest configuration with warning filters and markers

### Recommended defaults (and how this template maps)

- **Formatting**: Let Black handle formatting. In CI, keep `black --check .` (already configured).
- **Linting**: Use Ruff for fast linting and safe autofixes. Consider limiting CI lint scope to `app/` if your tests intentionally violate style:
  ```bash
  ruff check app/
  ```
  In this template, CI currently runs `ruff check .`. You can adjust if your project prefers.
- **Typing**: Default to checking `app/` for production code. This template's `pyproject.toml` sets mypy to `packages = ["app"]`. CI still runs `mypy app/ scripts/` to keep scripts in good shape. If you want to add tests later:
  ```bash
  mypy app/ tests/  # only if you want typed tests
  ```
- **Template safety**: The custom pre-commit hook prevents accidental commits/pushes to the template remote. Keep it enabled for template forks; remove only when you intend to push upstream deliberately.

### Quickstart: local quality checks

```bash
# Install dev deps
pip install -r requirements-dev.txt

# Install pre-commit hooks and run once on all files
pre-commit install
pre-commit run --all-files

# Ad-hoc runs
ruff check app/
black .
mypy app/
```

### Optional enhancements

- **Security**
  - Add `pip-audit` to CI to scan Python dependencies:
    ```yaml
    - name: Security audit (pip-audit)
      run: pipx run pip-audit -r requirements.txt -r requirements-dev.txt
    ```
  - Optionally add `bandit` for basic static security checks on `app/`.

- **Pre-commit CI**
  - Consider enabling `pre-commit.ci` for automatic PR autofixes and status checks.

- **Coverage**
  - If you track coverage in CI:
    ```bash
    pytest --cov=app --cov-report=xml
    ```
    Then upload the report to your coverage service of choice.

### Production checklist alignment

- **Secrets**: Set a strong `SECRET_KEY`, enable `REFRESH_TOKEN_COOKIE_SECURE`, enable HSTS if you terminate TLS upstream.
- **Observability**: Configure Sentry DSN and structured logs. The app supports JSON logs via existing logging config.
- **Rate limiting**: Use Redis-backed limiter in production and set sane limits.
- **Database**: Run migrations, tune pool size/timeout, verify health/readiness endpoints.
- **CI gates**: Keep pytest + Ruff + Black + Mypy green on `main`/PRs.

This file reflects what the template ships with and how to tailor checks to your team's preferences while preserving strong defaults for production code quality.


