# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1] - 2025-08-10

### Fixed
- Prevent blank Swagger UI at `/docs` due to CSP and upstream template issues:
  - Added custom `/docs` route in `app/main.py` with CDN fallbacks (unpkg → cdnjs) and pinned Swagger UI version.
  - Disabled FastAPI's default docs to avoid overrides.
  - Relaxed CSP only for `/docs` (and `/redoc`) in `app/core/security/security_headers.py` to allow required assets.

### Improved
- Setup UX when Docker isn't running:
  - `scripts/setup/setup_project.py` now attempts to start Docker Desktop (macOS/Windows) or the Docker service (Linux), offers retry, allows continuing without Docker, and provides follow-up commands.
  - Added Windows-specific handling for launching Docker Desktop.

### Docs
- Updated `README.md`, `docs/TEMPLATE_README.md`, `docs/tutorials/deployment-and-production.md`, and troubleshooting docs with notes on the custom `/docs` page and friendlier Docker startup flow.

### Meta
- Version bump to 1.1.1; tests remain green (570 passed, 10 skipped).

---

## [1.1.0] - 2025-07-XX
- Previous release details.


