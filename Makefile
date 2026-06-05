# FinOps platform - common dev commands
# Usage: make <target>

.DEFAULT_GOAL := help
COMMON_DIR := libs/common
GEN_DIR := services/billing-generator
INGEST_DIR := services/ingestion-service

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install shared lib + all services (editable, with dev extras)
	pip install -e "$(COMMON_DIR)"
	cd $(GEN_DIR) && pip install -e ".[dev]"
	cd $(INGEST_DIR) && pip install -e ".[dev]"

.PHONY: gen
gen: ## Run the billing generator to stdout
	cd $(GEN_DIR) && billing-generator --sink stdout --interval 2 --batch-size 5

.PHONY: gen-file
gen-file: ## Run the billing generator to a file (data/billing.ndjson)
	cd $(GEN_DIR) && billing-generator --sink file --interval 1 --batch-size 10

.PHONY: gen-broker
gen-broker: ## Stream the billing generator to the broker (Red Panda :9092)
	cd $(GEN_DIR) && billing-generator --sink broker --interval 2 --batch-size 5

.PHONY: ingest
ingest: ## Consume the topic into SQLite (from the beginning)
	cd $(INGEST_DIR) && ingestion-service --from-beginning

.PHONY: test
test: ## Run tests for all services
	cd $(GEN_DIR) && pytest -q
	cd $(INGEST_DIR) && pytest -q

.PHONY: lint
lint: ## Lint with ruff
	cd $(GEN_DIR) && ruff check .

.PHONY: fmt
fmt: ## Format with ruff
	cd $(GEN_DIR) && ruff format .

.PHONY: up
up: ## Start local environment via docker-compose
	docker compose up --build

.PHONY: down
down: ## Stop local environment
	docker compose down -v
