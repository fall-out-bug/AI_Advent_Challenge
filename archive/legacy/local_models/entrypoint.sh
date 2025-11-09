#!/bin/bash
set -euo pipefail

# Fix permissions for HuggingFace cache directory
# This fixes Permission denied errors when volume is mounted

CACHE_DIR="/home/appuser/.cache/huggingface"

if [ -d "$CACHE_DIR" ]; then
    echo "Fixing permissions for cache directory: $CACHE_DIR"
    chown -R appuser:appuser "$CACHE_DIR" 2>/dev/null || true
    chmod -R 777 "$CACHE_DIR" 2>/dev/null || true
fi

# Switch to appuser and execute the main command
exec gosu appuser "$@"
