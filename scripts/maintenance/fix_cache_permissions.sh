#!/bin/bash
# Fix permissions for HuggingFace cache directory
# This fixes Permission denied errors in mistral-chat container

set -euo pipefail

CACHE_DIR="${1:-./cache/models}"

if [ ! -d "$CACHE_DIR" ]; then
    echo "Creating cache directory: $CACHE_DIR"
    mkdir -p "$CACHE_DIR"
fi

echo "Fixing permissions for: $CACHE_DIR"
chmod -R 777 "$CACHE_DIR"

echo "✅ Permissions fixed for cache directory"
