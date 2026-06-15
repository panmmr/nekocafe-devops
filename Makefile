.PHONY: help install test lint coverage build up down clean scan

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies for all services
	pip install -r services/reservation-service/requirements.txt
	pip install -r services/member-service/requirements.txt

test: ## Run all tests with coverage
	cd services/reservation-service && pytest --cov=src --cov-report=term --cov-report=html -v
	cd services/member-service && pytest --cov=src --cov-report=term --cov-report=html -v

lint: ## Run all linters
	ruff check services/
	ruff format --check services/
	hadolint services/*/Dockerfile
	yamllint .

coverage: ## Generate coverage report
	cd services/reservation-service && coverage run -m pytest && coverage html
	cd services/member-service && coverage run -m pytest && coverage html

build: ## Build Docker images
	docker build -t nekocafe-reservation:latest services/reservation-service/
	docker build -t nekocafe-member:latest services/member-service/

up: ## Start all services with Docker Compose
	docker compose up -d --build

down: ## Stop all services
	docker compose down

logs: ## View service logs
	docker compose logs -f

scan: ## Security scan images with Trivy
	trivy image --severity HIGH,CRITICAL nekocafe-reservation:latest
	trivy image --severity HIGH,CRITICAL nekocafe-member:latest

monitoring-up: ## Start monitoring stack
	docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

rollback: ## Rollback to previous deployment version
	./scripts/rollback.sh

clean: ## Clean up build artifacts and containers
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	find . -type d -name .coverage -delete
