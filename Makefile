.PHONY: help build up down logs clean dev prod backup restore

# Default target
help:
	@echo "GridTokenX Smart Meter Simulator - Docker Commands"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  build     - Build all Docker images"
	@echo "  up        - Start all services (detached)"
	@echo "  down      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - View logs (follow mode)"
	@echo "  ps        - Show running containers"
	@echo "  clean     - Remove containers and volumes"
	@echo ""
	@echo "  dev       - Start development environment"
	@echo "  prod      - Start production environment"
	@echo ""
	@echo "  backup    - Backup all data volumes"
	@echo "  restore   - Restore data from backup"
	@echo ""
	@echo "  ui-build  - Build UI only"
	@echo "  ui-dev    - Start UI development server"
	@echo ""
	@echo "  test      - Run tests"
	@echo "  lint      - Run linter"
	@echo ""

# Build images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# Show containers
ps:
	docker-compose ps

# Clean everything
clean:
	docker-compose down -v
	docker system prune -f

# Development mode
dev:
	docker-compose -f docker-compose.dev.yml up -d

# Production mode
prod:
	docker-compose up -d

# Backup data
backup:
	@mkdir -p ./backup
	docker run --rm \
		-v gridtokenx-influxdb-data:/source \
		-v $(pwd)/backup:/backup \
		alpine tar czf /backup/influxdb-backup-$$(date +%Y%m%d-%H%M%S).tar.gz -C /source .
	@echo "Backup created in ./backup/"

# Restore data (requires BACKUP_FILE env var)
restore:
ifndef BACKUP_FILE
	@echo "Error: BACKUP_FILE not specified"
	@echo "Usage: make restore BACKUP_FILE=./backup/influxdb-backup-20240101-120000.tar.gz"
else
	docker run --rm \
		-v gridtokenx-influxdb-data:/target \
		-v $(pwd)/backup:/backup \
		alpine tar xzf /backup/$(BACKUP_FILE) -C /target
	@echo "Data restored from $(BACKUP_FILE)"
endif

# Build UI
ui-build:
	cd ui && bun install && bun run build

# UI development
ui-dev:
	cd ui && bun run dev

# Run tests
test:
	docker-compose exec simulator pytest

# Run linter
lint:
	docker-compose exec simulator ruff check src/

# Shell access
shell:
	docker-compose exec simulator bash

# Health check
health:
	@echo "Checking service health..."
	@echo "Simulator: $$(curl -s http://localhost:8080/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "InfluxDB:  $$(curl -s http://localhost:8086/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo 'DOWN')"
	@echo "Kafka:     $$(docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >/dev/null 2>&1 && echo 'UP' || echo 'DOWN')"

# Scale simulator
scale:
ifndef COUNT
	@echo "Error: COUNT not specified"
	@echo "Usage: make scale COUNT=3"
else
	docker-compose up -d --scale simulator=$(COUNT)
endif

# View metrics
metrics:
	curl http://localhost:8080/metrics

# Reset database
reset-db:
	docker-compose down -v influxdb-data
	docker-compose up -d influxdb

# Quick start for new users
quickstart:
	@echo "Setting up GridTokenX Smart Meter Simulator..."
	@cp -n .env.example .env || true
	@echo "Please edit .env file and set required variables"
	@echo "Then run: make up"
