.PHONY: help dev dev-down test test-go test-python build lint lint-go lint-python clean docker-build work-sync

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start local dev dependencies
	docker compose up -d

dev-down: ## Stop local dev dependencies
	docker compose down

test: test-go test-python ## Run all tests (Go + Python)

test-go: ## Run Go tests
	@for d in services/api-gateway services/backend services/operator shared/types; do (cd $$d && go test ./... -v -count=1) || exit 1; done

test-python: ## Run Python tests (reasoner)
	cd services/reasoner && python -m pytest src/reasoner/test/ -v

test-coverage: ## Run Go tests with coverage
	@for d in services/api-gateway services/backend services/operator shared/types; do (cd $$d && go test ./... -coverprofile=coverage.out) || exit 1; done

build: ## Build all Go service binaries
	cd services/api-gateway && go build -o ../../bin/api-gateway ./cmd/main.go
	cd services/backend && go build -o ../../bin/backend ./cmd/main.go
	cd services/operator && go build -o ../../bin/operator ./cmd/main.go

lint: lint-go lint-python ## Run all linters

lint-go: ## Run Go linter
	golangci-lint run ./services/.../... ./shared/...

lint-python: ## Run Python linter (reasoner)
	cd services/reasoner && ruff check src/ && ruff format --check src/

fmt: ## Format Go code
	gofmt -w services/ shared/

clean: ## Clean build artifacts
	rm -rf bin/ coverage.out coverage.html

docker-build: ## Build all Docker images (run from repo root)
	docker build -t runguard/api-gateway:dev -f services/api-gateway/Dockerfile .
	docker build -t runguard/backend:dev -f services/backend/Dockerfile .
	docker build -t runguard/operator:dev -f services/operator/Dockerfile .
	docker build -t runguard/reasoner:dev -f services/reasoner/Dockerfile services/reasoner

work-sync: ## Sync Go workspace
	go work sync
