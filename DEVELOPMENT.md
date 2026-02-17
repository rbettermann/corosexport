# Getting Started with Corosexport Development

This guide walks you through setting up the corosexport project for development using `uv` and Poetry-compatible configuration.

## Prerequisites

- Python 3.9 or later
- [uv](https://github.com/astral-sh/uv) installed
- Git

### Installing uv

uv is a fast Python package manager and is much faster than pip/Poetry.

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy BypassCurrentUser -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**With Homebrew (macOS):**
```bash
brew install uv
```

Verify installation:
```bash
uv --version
```

## Project Setup

### 1. Clone and Initialize

```bash
# Clone the repository
git clone https://github.com/rbettermann/corosexport.git
cd corosexport

# Create virtual environment and install dependencies
uv sync
```

This creates a `.venv` directory and installs all dependencies from `pyproject.toml`.

### 2. Verify Installation

```bash
# Activate the virtual environment (optional - uv run handles this)
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Verify the CLI is available
uv run coros-backup --help

# Run a simple Python import test
python -c "import corosexport; print(corosexport.__version__)"
```

### 3. Project Structure

```
corosexport/
├── src/corosexport/
│   ├── __init__.py                 # Main package init
│   ├── client.py                   # Coros API client (reverse-engineered)
│   ├── backup.py                   # Incremental backup logic
│   ├── models.py                   # Pydantic data models
│   ├── formats.py                  # (TODO) Format exporters
│   └── cli/
│       ├── __init__.py
│       └── backup.py               # CLI entry point
│
├── tests/
│   ├── __init__.py
│   ├── test_client.py              # (TODO) Client tests
│   ├── test_backup.py              # (TODO) Backup manager tests
│   └── conftest.py                 # (TODO) Pytest configuration
│
├── examples/
│   └── basic_backup.py             # Usage examples
│
├── pyproject.toml                  # Project config + dependencies
├── uv.lock                         # Dependency lock file (auto-generated)
├── README.md                       # User documentation
├── DEVELOPMENT.md                  # This file
└── .gitignore
```

## Development Workflow

### 1. Install Development Dependencies

```bash
# Already done by 'uv sync', but explicitly:
uv sync --all-groups  # Installs main + dev dependencies
```

This installs tools for:
- Testing (pytest, pytest-cov)
- Code formatting (black)
- Linting (ruff)
- Type checking (mypy)

### 2. Code Formatting

Format all code with Black:

```bash
uv run black src/ tests/
```

Single file:
```bash
uv run black src/corosexport/client.py
```

### 3. Linting

Check code quality with Ruff:

```bash
# Check for issues
uv run ruff check src/ tests/

# Auto-fix what can be fixed
uv run ruff check --fix src/ tests/
```

### 4. Type Checking

Verify type hints with mypy:

```bash
# Check entire codebase
uv run mypy src/

# Check specific file
uv run mypy src/corosexport/client.py
```

### 5. Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/corosexport --cov-report=html

# Run specific test file
uv run pytest tests/test_client.py -v

# Run specific test function
uv run pytest tests/test_client.py::test_authentication -v

# Run with detailed output and print statements
uv run pytest -v -s

# Run only tests matching a pattern
uv run pytest -k "test_auth" -v
```

### 6. Testing the CLI

```bash
# Run the CLI with test data
uv run coros-backup --help

# Test authentication (will prompt for credentials)
uv run coros-backup --backup-dir ./test_backup --verbose

# Run with custom email
uv run coros-backup --email test@example.com --backup-dir ./test_backup
```

## Development Commands Cheat Sheet

```bash
# Sync dependencies (after updating pyproject.toml)
uv sync

# Run Python in project context
uv run python script.py

# Run CLI tools
uv run coros-backup --help
uv run pytest
uv run black src/
uv run ruff check src/
uv run mypy src/

# Enter shell with .venv activated
uv run bash  # or: source .venv/bin/activate

# Remove and recreate venv
rm -rf .venv uv.lock
uv sync

# Show installed packages
uv pip list

# Show package tree
uv pip tree
```