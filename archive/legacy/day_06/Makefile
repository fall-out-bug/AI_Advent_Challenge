# Day 06 - Model Testing System
# Based on universal Makefile template

.PHONY: install test run demo clean setup run-quiet

# Project-specific variables
PROJECT_NAME := day-06-model-testing
MAIN_SCRIPT := src/main.py
TEST_DIR := tests
SRC_DIR := src

# Detect Python executable and Poetry
PYTHON := $(shell which python3 || which python)
POETRY := $(shell which poetry 2>/dev/null)

# Colors for output
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Show this help message
	@echo "$(GREEN)Available commands for $(PROJECT_NAME):$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(RESET)"
	@if [ -n "$(POETRY)" ]; then \
		echo "$(YELLOW)Using Poetry...$(RESET)"; \
		$(POETRY) install; \
	else \
		echo "$(RED)Poetry not found! Please install Poetry first.$(RESET)"; \
		exit 1; \
	fi

test: ## Run tests
	@echo "$(GREEN)Running tests...$(RESET)"
	@if [ -n "$(POETRY)" ]; then \
		$(POETRY) run pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=html; \
	else \
		$(PYTHON) -m pytest $(TEST_DIR)/ -v; \
	fi

run: ## Run model testing
	@echo "$(GREEN)Running $(PROJECT_NAME)...$(RESET)"
	@if [ -n "$(POETRY)" ]; then \
		$(POETRY) run $(PYTHON) $(MAIN_SCRIPT); \
	else \
		$(PYTHON) $(MAIN_SCRIPT); \
	fi

run-quiet: ## Run model testing in quiet mode
	@echo "$(GREEN)Running $(PROJECT_NAME) in quiet mode...$(RESET)"
	@if [ -n "$(POETRY)" ]; then \
		$(POETRY) run $(PYTHON) $(MAIN_SCRIPT) --quiet; \
	else \
		$(PYTHON) $(MAIN_SCRIPT) --quiet; \
	fi

demo: ## Run demo
	@echo "$(GREEN)Running demo...$(RESET)"
	@if [ -n "$(POETRY)" ]; then \
		$(POETRY) run $(PYTHON) demo.py; \
	else \
		$(PYTHON) demo.py; \
	fi

clean: ## Clean cache and temporary files
	@echo "$(GREEN)Cleaning up...$(RESET)"
	@rm -rf __pycache__/ 2>/dev/null || true
	@rm -rf *.pyc 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

setup: install ## Setup project (install dependencies)
	@echo "$(GREEN)Project setup complete!$(RESET)"

check-python: ## Check Python version
	@echo "$(GREEN)Python version:$(RESET)"
	@$(PYTHON) --version

check-deps: ## Check if dependencies are installed
	@echo "$(GREEN)Checking dependencies...$(RESET)"
	@if [ -n "$(POETRY)" ]; then \
		$(POETRY) check; \
	else \
		echo "$(YELLOW)No Poetry configuration found$(RESET)"; \
	fi
