.PHONY: help build up down restart logs clean test shell shell-db migrate deploy

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)   AI Agency - Available Commands$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ═══════════════════════════════════════════════
# Development Commands
# ═══════════════════════════════════════════════

build: ## Build Docker containers
	@echo "$(BLUE)Building Docker containers...$(NC)"
	docker-compose build --no-cache

up: ## Start all services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Services started!$(NC)"
	@echo "$(BLUE)Backend API:$(NC) http://localhost:8000"
	@echo "$(BLUE)API Docs:$(NC) http://localhost:8000/docs"

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(YELLOW)Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

build-up: build up ## Build and start all services

# ═══════════════════════════════════════════════
# Logs & Monitoring
# ═══════════════════════════════════════════════

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-postgres: ## Show PostgreSQL logs
	docker-compose logs -f postgres

logs-redis: ## Show Redis logs
	docker-compose logs -f redis

ps: ## Show running containers
	docker-compose ps

# ═══════════════════════════════════════════════
# Database Commands
# ═══════════════════════════════════════════════

shell: ## Open shell in backend container
	docker-compose exec backend bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U aiagency -d ai_agency

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

migrate-down: ## Rollback last migration
	docker-compose exec backend alembic downgrade -1

migrate-history: ## Show migration history
	docker-compose exec backend alembic history

migrate-current: ## Show current migration
	docker-compose exec backend alembic current

migrate-create: ## Create new migration (use: make migrate-create MSG="your message")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please provide migration message$(NC)"; \
		echo "Usage: make migrate-create MSG=\"your message\""; \
		exit 1; \
	fi
	docker-compose exec backend alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)⚠️  WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		docker-compose up -d backend; \
		echo "$(GREEN)✅ Database reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# ═══════════════════════════════════════════════
# Testing
# ═══════════════════════════════════════════════

test: ## Run tests
	docker-compose exec backend pytest

test-cov: ## Run tests with coverage
	docker-compose exec backend pytest --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	docker-compose exec backend pytest-watch

# ═══════════════════════════════════════════════
# Cleanup Commands
# ═══════════════════════════════════════════════

clean: ## Stop and remove all containers, volumes, and networks
	@echo "$(RED)Cleaning up Docker resources...$(NC)"
	docker-compose down -v --remove-orphans
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including images
	@echo "$(RED)Removing Docker images...$(NC)"
	docker-compose down -v --rmi all --remove-orphans
	@echo "$(GREEN)✅ Full cleanup complete$(NC)"

prune: ## Prune Docker system
	@echo "$(YELLOW)Pruning Docker system...$(NC)"
	docker system prune -af --volumes
	@echo "$(GREEN)✅ Prune complete$(NC)"

# ═══════════════════════════════════════════════
# Frontend Commands
# ═══════════════════════════════════════════════

frontend-install: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

frontend-dev: ## Start frontend development server
	@echo "$(BLUE)Starting frontend dev server...$(NC)"
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)✅ Frontend built$(NC)"

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

# ═══════════════════════════════════════════════
# Deployment Commands
# ═══════════════════════════════════════════════

deploy: ## Full deployment (build, migrate, start)
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)   Starting Full Deployment$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(BLUE)Step 1:$(NC) Building containers..."
	@make build
	@echo ""
	@echo "$(BLUE)Step 2:$(NC) Starting services..."
	@make up
	@echo ""
	@echo "$(BLUE)Step 3:$(NC) Waiting for services to be healthy..."
	@sleep 10
	@echo ""
	@echo "$(GREEN)✅ Deployment complete!$(NC)"
	@echo ""
	@echo "$(BLUE)Services:$(NC)"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"
	@echo ""

setup: ## Initial setup (creates .env, builds, and deploys)
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)   AI Agency - Initial Setup$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✅ .env file created$(NC)"; \
		echo "$(YELLOW)⚠️  Please edit .env and add your CLAUDE_API_KEY$(NC)"; \
		echo ""; \
		read -p "Press enter when you've added your API key..."; \
	else \
		echo "$(GREEN)✅ .env file already exists$(NC)"; \
	fi
	@echo ""
	@make deploy

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo ""
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker-compose exec postgres pg_isready -U aiagency || echo "$(RED)❌ Not ready$(NC)"
	@echo ""
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose exec redis redis-cli ping || echo "$(RED)❌ Not ready$(NC)"
	@echo ""
	@echo "$(YELLOW)Backend API:$(NC)"
	@curl -s http://localhost:8000/health | jq . || echo "$(RED)❌ Not responding$(NC)"
	@echo ""

status: health ## Alias for health

backup-db: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	@docker-compose exec -T postgres pg_dump -U aiagency ai_agency > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backed up to backups/$(NC)"

restore-db: ## Restore database (use: make restore-db FILE=backups/backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please provide backup file$(NC)"; \
		echo "Usage: make restore-db FILE=backups/backup_20231117_120000.sql"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	@cat $(FILE) | docker-compose exec -T postgres psql -U aiagency ai_agency
	@echo "$(GREEN)✅ Database restored$(NC)"

# ═══════════════════════════════════════════════
# Information Commands
# ═══════════════════════════════════════════════

info: ## Show project information
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)   AI Agency - Project Information$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Version:$(NC) 1.0.0"
	@echo "$(YELLOW)Python:$(NC) 3.13"
	@echo "$(YELLOW)FastAPI:$(NC) 0.121.2"
	@echo "$(YELLOW)PostgreSQL:$(NC) 17"
	@echo "$(YELLOW)Redis:$(NC) 8"
	@echo "$(YELLOW)Node.js:$(NC) 20+"
	@echo "$(YELLOW)Next.js:$(NC) 15.5.1"
	@echo "$(YELLOW)React:$(NC) 19.2.0"
	@echo ""
	@echo "$(YELLOW)Agents:$(NC) 10 specialized AI agents"
	@echo "  1. Marketing Agent"
	@echo "  2. Frontend Developer"
	@echo "  3. Backend Developer"
	@echo "  4. Data Analyst"
	@echo "  5. UX/UI Designer"
	@echo "  6. Content Writer"
	@echo "  7. Mobile Developer"
	@echo "  8. DevOps Engineer"
	@echo "  9. Project Manager"
	@echo "  10. QA Engineer"
	@echo ""

version: info ## Show version information

# Default target
.DEFAULT_GOAL := help
