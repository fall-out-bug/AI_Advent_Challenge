#!/bin/bash
# Secret detection script for pre-commit hook
# Following shell script best practices: set -euo pipefail

set -euo pipefail

echo "🔍 Scanning for secrets..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Patterns to detect secrets
PATTERNS=(
    "api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}"
    "password\s*[:=]\s*['\"]?[a-zA-Z0-9]{8,}"
    "secret\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}"
    "token\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}"
    "aws[_-]?access[_-]?key[_-]?id"
    "aws[_-]?secret[_-]?access[_-]?key"
    "sk_live_[a-zA-Z0-9]{24,}"
    "pk_live_[a-zA-Z0-9]{24,}"
    "AIza[0-9A-Za-z\\-_]{35}"
    "sk-[0-9a-zA-Z]{32}"
    "xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{32}"
)

# Files to check (only staged files in pre-commit mode)
if [ -n "${1:-}" ]; then
    FILES="$1"
else
    # Check all Python files
    FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|yml|yaml|json|sh|env)$' || true)
fi

if [ -z "$FILES" ]; then
    echo -e "${GREEN}✓ No files to check${NC}"
    exit 0
fi

ERRORS=0

for file in $FILES; do
    if [ ! -f "$file" ]; then
        continue
    fi
    
    # Skip files in .gitignore
    if git check-ignore -q "$file"; then
        continue
    fi
    
    for pattern in "${PATTERNS[@]}"; do
        if grep -qEi "$pattern" "$file" 2>/dev/null; then
            echo -e "${RED}✗ Potential secret found in: $file${NC}"
            echo -e "${YELLOW}   Pattern: $pattern${NC}"
            grep -nEi "$pattern" "$file" | head -3 | sed 's/^/   /'
            ERRORS=$((ERRORS + 1))
        fi
    done
    
    # Check for api_key.txt or .env files
    if [[ "$file" == *"api_key.txt"* ]] || [[ "$file" == *".env"* ]]; then
        if ! git check-ignore -q "$file"; then
            echo -e "${RED}✗ Security risk: $file should be in .gitignore${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo -e "${RED}✗ Found $ERRORS potential secret(s)${NC}"
    echo -e "${YELLOW}Please remove secrets before committing${NC}"
    exit 1
fi

echo -e "${GREEN}✓ No secrets detected${NC}"
exit 0

