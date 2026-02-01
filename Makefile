.DEFAULT_GOAL := all
sources = app tests scripts

.PHONY: .uv  # Check that uv is installed
.uv:
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: install  # Install the package, dependencies for local development
install: .uv
	uv sync --all-extras --all-groups

.PHONY: githooks # Append git hooks to the repository
githooks: .uv
	uv run pre-commit install --install-hooks
	uv run pre-commit autoupdate

.PHONY: format  # Format the code
format: .uv
	uv run ruff format
	uv run ruff check --fix --fix-only

.PHONY: lint  # Lint the code
lint: .uv
	uv run ruff format --check
	uv run ruff check

.PHONY: typecheck # Check the types
typecheck: .uv
	uv run pyright

.PHONY: test # Run tests
test: .uv
	uv run pytest

.PHONY: testcov  # Run tests and collect coverage data
testcov: .uv
	uv run coverage run -m pytest
	@uv run coverage report
	@uv run coverage html

.PHONY: all # Run all basic development tasks
all: format lint typecheck testcov

# =============================================================================
# Running the application
# =============================================================================

.PHONY: run
run: .uv
	uv run python app/main.py
