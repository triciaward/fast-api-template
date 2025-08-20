# Contributing

## Golden workflow

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

## Make targets

```bash
make fmt       # Black
make lint      # Ruff
make type      # mypy app
make type-sa   # SA plugin spot-check
make precommit # Run all hooks
```

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
