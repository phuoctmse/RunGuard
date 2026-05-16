#!/bin/bash
# Run golangci-lint on all Go modules locally.
# Usage: ./scripts/lint-go.sh
# Prerequisites: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

set -e

GO_MODULES="services/api-gateway services/backend services/operator shared/types"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

failed=0
for d in $GO_MODULES; do
    if [ ! -d "$d" ]; then
        continue
    fi
    echo "--- Linting $d ---"
    if (cd "$d" && golangci-lint run ./...); then
        echo -e "${GREEN}PASS${NC}: $d"
    else
        echo -e "${RED}FAIL${NC}: $d"
        failed=1
    fi
    echo ""
done

if [ $failed -eq 1 ]; then
    echo -e "${RED}Lint failed.${NC}"
    exit 1
fi

echo -e "${GREEN}All modules passed.${NC}"
