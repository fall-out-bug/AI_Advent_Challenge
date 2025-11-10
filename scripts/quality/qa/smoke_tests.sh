#!/bin/bash
# Smoke tests for post-deployment verification
# Following shell script best practices: set -euo pipefail

set -euo pipefail

echo "🔍 Running Post-Deployment Smoke Tests"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -e "${YELLOW}Testing: ${name}${NC}"
    if response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null); then
        http_code=$(echo "$response" | tail -n1)
        if [ "$http_code" = "$expected_status" ]; then
            echo -e "${GREEN}✓ ${name} - OK (${http_code})${NC}"
            return 0
        else
            echo -e "${RED}✗ ${name} - Failed (expected ${expected_status}, got ${http_code})${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ ${name} - Failed (connection error)${NC}"
        return 1
    fi
}

# Test MCP Server
echo "=== MCP Server ==="
if test_endpoint "MCP Server Health" "http://localhost:8004/health" 200; then
    echo ""
else
    ERRORS=$((ERRORS + 1))
    echo ""
fi

# Test Prometheus
echo "=== Prometheus ==="
if test_endpoint "Prometheus Health" "http://localhost:9090/-/healthy" 200; then
    echo ""
else
    ERRORS=$((ERRORS + 1))
    echo ""
fi

# Test Grafana
echo "=== Grafana ==="
if test_endpoint "Grafana Health" "http://localhost:3000/api/health" 200; then
    echo ""
else
    ERRORS=$((ERRORS + 1))
    echo ""
fi

# Test Prometheus metrics endpoint
echo "=== Metrics Endpoints ==="
if response=$(curl -s "http://localhost:8004/metrics" 2>/dev/null); then
    if echo "$response" | grep -q "prometheus"; then
        echo -e "${GREEN}✓ MCP Server metrics endpoint - OK${NC}"
    else
        echo -e "${YELLOW}⚠ MCP Server metrics endpoint - No prometheus metrics found${NC}"
    fi
else
    echo -e "${RED}✗ MCP Server metrics endpoint - Failed${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Test Docker services
echo ""
echo "=== Docker Services ==="
if command -v docker &> /dev/null; then
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "mcp-server-day12"; then
        echo -e "${GREEN}✓ MCP Server container - Running${NC}"
    else
        echo -e "${RED}✗ MCP Server container - Not running${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "prometheus-day12"; then
        echo -e "${GREEN}✓ Prometheus container - Running${NC}"
    else
        echo -e "${YELLOW}⚠ Prometheus container - Not running (optional)${NC}"
    fi

    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "grafana-day12"; then
        echo -e "${GREEN}✓ Grafana container - Running${NC}"
    else
        echo -e "${YELLOW}⚠ Grafana container - Not running (optional)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Docker not available - Skipping container checks${NC}"
fi

# Summary
echo ""
echo "=============================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ ${ERRORS} test(s) failed${NC}"
    exit 1
fi
