.PHONY: help install install-dev test lint format check-format type-check docs clean

# Variables
PYTHON = python
PIP = pip
PYTEST = pytest
FLAKE8 = flake8
BLACK = black
ISORT = isort
MYPY = mypy
SPHINX_BUILD = sphinx-build

# Directories
SRC_DIR = src
TESTS_DIR = tests
DOCS_DIR = docs

# Help message
help:
	@echo "Please use 'make <target>' where <target> is one of:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  test           Run tests"
	@echo "  test-cov       Run tests with coverage report"
	@echo "  lint           Check code style with flake8"
	@echo "  format         Format code with black and isort"
	@echo "  check-format   Check code formatting without making changes"
	@echo "  type-check     Run type checking with mypy"
	@echo "  docs           Build documentation"
	@echo "  clean          Remove build artifacts and cache"

# Installation
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .


# Testing
test:
	$(PYTEST) $(TESTS_DIR) -v

test-cov:
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=xml $(TESTS_DIR) -v

# Linting and Formatting
lint:
	$(FLAKE8) $(SRC_DIR) $(TESTS_DIR)

format:
	$(BLACK) $(SRC_DIR) $(TESTS_DIR) $(DOCS_DIR)
	$(ISORT) $(SRC_DIR) $(TESTS_DIR)

check-format:
	$(BLACK) --check $(SRC_DIR) $(TESTS_DIR) $(DOCS_DIR)
	$(ISORT) --check-only $(SRC_DIR) $(TESTS_DIR)

type-check:
	$(MYPY) $(SRC_DIR) $(TESTS_DIR)

# Documentation
docs:
	$(SPHINX_BUILD) -b html $(DOCS_DIR) $(DOCS_DIR)/_build/html

# Cleanup
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/ build/ dist/ *.egg-info/
	$(MAKE) -C $(DOCS_DIR) clean

# Default target
.DEFAULT_GOAL := help
