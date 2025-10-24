# otto-agent Makefile
# Note: This project uses Python 3.12

PROJECT_NAME := otto-agent
VERSION := latest
PYTHON_COMMAND := python3.12
PIP_COMMAND := pip
VENV_PATH ?= venv
VENV_BIN ?= $(VENV_PATH)/bin/

help: ## Show all Makefile targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'

venv: ## Set up virtual environment
	$(PYTHON_COMMAND) -m venv $(VENV_PATH)

clean-venv: ## Remove and recreate virtual environment
	rm -rf $(VENV_PATH)
	$(PYTHON_COMMAND) -m venv $(VENV_PATH)

install: venv ## Install dependencies
	$(VENV_BIN)$(PIP_COMMAND) install --upgrade pip
	$(VENV_BIN)$(PIP_COMMAND) install -r requirements.txt
	$(VENV_BIN)patchright install

format: ## Format code
	$(VENV_BIN)$(PYTHON_COMMAND) -m black .

check-format: ## Check code formatting
	$(VENV_BIN)$(PYTHON_COMMAND) -m black --check .

lint: ## Lint code
	$(VENV_BIN)$(PYTHON_COMMAND) -m pylint --extension-pkg-whitelist='pydantic' .

run: ## Run the agent in API mode
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	$(VENV_BIN)$(PYTHON_COMMAND) -m main

# run-cli: ## Run the agent in CLI mode
# 	$(VENV_BIN)$(PYTHON_COMMAND) -m main --mode cli

# test-tools: ## Test tools directly (proper pytest version)
# 	@if [ ! -d "$(VENV_PATH)" ]; then \
# 		echo "Virtual environment not found. Running make install..."; \
# 		make install; \
# 	fi
# 	@echo "Testing tools using pytest..."
# 	$(VENV_BIN)$(PYTHON_COMMAND) -m pytest tests/test_tools.py -v

# test-basic: ## Run only basic tests to verify pytest setup
# 	$(VENV_BIN)$(PYTHON_COMMAND) -m pytest tests/test_basic.py -v

# test-weather: ## Test weather tool
# 	@if [ ! -d "$(VENV_PATH)" ]; then \
# 		echo "Virtual environment not found. Running make install..."; \
# 		make install; \
# 	fi
# 	@echo "Testing weather tool..."
# 	$(VENV_BIN)$(PYTHON_COMMAND) -m tools.test_tools weather "London"

# stop: ## Stop running services
# 	@echo "Stopping services..."
# 	pkill -f "python -m main" || echo "No running services found"

# test: ## Run tests
# 	$(VENV_BIN)$(PYTHON_COMMAND) -m pytest tests

clean: ## Clean up temporary files
	rm -rf $(VENV_PATH)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# setup-env: ## Create .env from example
# 	@if [ ! -f .env ]; then \
# 		cp .env.example .env; \
# 		echo ".env file created. Please edit with your API keys."; \
# 	else \
# 		echo ".env file already exists."; \
# 	fi

# Add a new target for running the API server
run-api: ## Run the agent API server
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	$(VENV_BIN)$(PYTHON_COMMAND) -m uvicorn api:app --reload

# Add a new target for running the API tests
test-api: ## Run the API server tests
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	$(VENV_BIN)$(PYTHON_COMMAND) -m pytest test_api.py -v

run-client: ## Run the client
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	$(VENV_BIN)$(PYTHON_COMMAND) -m client

test-token-optimization: ## Test token optimization fixes
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	$(VENV_BIN)$(PYTHON_COMMAND) test_token_optimization.py

test-cache-persistence: ## Test cache persistence across function calls
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	$(VENV_BIN)$(PYTHON_COMMAND) test_cache_persistence.py

test-performance: ## Test task completion speed optimizations (requires live browser)
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	@echo "⚠️  This test performs real browser automation and may take 30-60 seconds"
	$(VENV_BIN)$(PYTHON_COMMAND) test_performance.py

test-model-config: ## Test AI model configuration and provider switching
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Virtual environment not found. Running make install..."; \
		make install; \
	fi
	$(VENV_BIN)$(PYTHON_COMMAND) test_model_config.py
