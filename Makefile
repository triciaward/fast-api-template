SHELL := /bin/bash

.PHONY: fmt lint type type-sa precommit

fmt:
	@echo "Formatting with Black..."
	@black .

lint:
	@echo "Linting with Ruff..."
	@ruff check .

type:
	@echo "Type-checking app with mypy..."
	@python -m mypy app

type-sa:
	@echo "Type-checking SQLAlchemy-typed models..."
	@bash ./scripts/development/mypy_sa_check.sh

precommit:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files


.PHONY: debt-check
debt-check: ## Run technical debt prevention check
	./scripts/development/prevent_technical_debt.sh


