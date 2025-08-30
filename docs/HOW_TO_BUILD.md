# How to Build: Golden Workflow

## Quick commands

- Lint + format:
  ```bash
  ruff check .
  black .
  ```
- Type check (app only):
  ```bash
  python -m mypy app
  ```
- SQLAlchemy plugin targeted check:
  ```bash
  ./scripts/development/mypy_sa_check.sh
  ```
- Run all pre-commit hooks:
  ```bash
  pre-commit run --all-files
  ```

## Debt-free build workflow

- Run during feature development before writing tests/docs:
  ```bash
  make debt-check
  # or
  ./scripts/development/prevent_technical_debt.sh [feature_name]
  ```
  This runs mypy, ruff, black, basic perf scans, and an import smoke-test.

## Prompt templates

- Migrate models in a feature
  "Convert app/models/<feature>/* to SQLAlchemy 2.0 typing. Use Mapped[...] and mapped_column(...), typed relationship annotations, TYPE_CHECKING for forward refs, and the assigned hybrid_property + .expression pattern. Remove broad ignores. Ensure ./scripts/development/mypy_sa_check.sh and mypy app pass, then add strict mypy overrides for these modules."

- Fix service initializer/decorators
  "Refactor app/services/**/__init__.py optional imports to predeclared typed Optionals, alias imports, and safe no-op fallbacks. Type custom decorators using ParamSpec/TypeVar so wrapped functions preserve their signatures. Ensure mypy app passes."

- Normalize dynamic values
  "Search for headers/cookies access and ORM scalar returns across services and crud. Ensure returns are str or str | None; assign ORM scalars to typed locals before returning. Remove ‘returning Any’ and unused-ignore. Keep ruff+mypy clean."

## PR checklist

- [ ] SQLAlchemy typed ORM used (`Mapped[...]`, `mapped_column(...)`, typed `relationship(...)`)
- [ ] Forward refs via `TYPE_CHECKING` blocks
- [ ] Decorators preserve signatures via `ParamSpec`/`TypeVar`
- [ ] Optional imports predeclared as Optionals with safe fallbacks
- [ ] Endpoints have `response_model` and return matching schema types
- [ ] Headers/cookies return `str | None` consistently
- [ ] ORM scalars assigned to typed locals before return
- [ ] mypy (app only) is clean; plugin script is green
- [ ] Ruff + Black clean
