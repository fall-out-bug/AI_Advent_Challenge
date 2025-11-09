#!/bin/bash
# Model Download Management Script
# This script provides easy commands for downloading models

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if HF_TOKEN is set
check_hf_token() {
    if [[ -z "${HF_TOKEN:-}" ]]; then
        print_warning "HF_TOKEN not set. Some models may require authentication."
        print_info "Set HF_TOKEN environment variable or create .env file"
        return 1
    fi
    return 0
}

# Function to show help
show_help() {
    cat << EOF
Model Download Management Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    download-all     Download all project models
    download-model   Download specific model
    list-models      List all project models
    cache-size       Show current cache size
    clean-cache      Clean model cache
    status           Show download status
    help             Show this help message

OPTIONS:
    --model MODEL_NAME    Specific model to download
    --parallel            Download models in parallel
    --force               Force re-download even if cached
    --dry-run            Show what would be downloaded

EXAMPLES:
    $0 download-all
    $0 download-model --model Qwen/Qwen1.5-4B-Chat
    $0 list-models
    $0 cache-size
    $0 clean-cache

MODELS:
    - Qwen/Qwen1.5-4B-Chat
    - mistralai/Mistral-7B-Instruct-v0.2
    - TinyLlama/TinyLlama-1.1B-Chat-v1.0
    - TechxGenus/starcoder2-7b-instruct

EOF
}

# Function to download all models
download_all() {
    print_info "Starting download of all project models..."
    
    if ! check_hf_token; then
        print_warning "Continuing without HF_TOKEN..."
    fi
    
    # Build download image
    print_info "Building download image..."
    docker build -f Dockerfile.download -t model-downloader .
    
    # Run download
    print_info "Downloading all models..."
    docker-compose -f docker-compose.download.yml up model-downloader
    
    print_success "All models downloaded!"
    return 0
}

# Function to download specific model
download_model() {
    local model_name="$1"
    
    print_info "Downloading model: $model_name"
    
    if ! check_hf_token; then
        print_warning "Continuing without HF_TOKEN..."
    fi
    
    # Build download image
    print_info "Building download image..."
    docker build -f Dockerfile.download -t model-downloader .
    
    # Try to use existing volume first, then fallback to hf-model-cache
    if docker volume ls | grep -q "local_models_hf-model-cache"; then
        VOLUME_NAME="local_models_hf-model-cache"
    else
        VOLUME_NAME="hf-model-cache"
    fi
    
    # Run download for specific model
    print_info "Downloading $model_name..."
    docker run --rm \
        -e HF_TOKEN="${HF_TOKEN:-}" \
        -v ${VOLUME_NAME}:/home/appuser/.cache/huggingface/hub \
        model-downloader \
        python download_model.py --model "$model_name"
    
    print_success "Model $model_name downloaded!"
    return 0
}

# Function to list models
list_models() {
    print_info "Project models:"
    docker run --rm model-downloader python download_model.py --list
}

# Function to show cache size
cache_size() {
    print_info "Checking cache size..."
    
    # Try to use existing volume first, then fallback to hf-model-cache
    if docker volume ls | grep -q "local_models_hf-model-cache"; then
        VOLUME_NAME="local_models_hf-model-cache"
    else
        VOLUME_NAME="hf-model-cache"
    fi
    
    docker run --rm \
        -v ${VOLUME_NAME}:/home/appuser/.cache/huggingface/hub \
        model-downloader \
        python download_model.py --cache-size
}

# Function to clean cache
clean_cache() {
    print_warning "This will remove all cached models!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning model cache..."
        
        # Try to remove both possible volume names
        docker volume rm local_models_hf-model-cache || true
        docker volume rm hf-model-cache || true
        
        print_success "Cache cleaned!"
    else
        print_info "Cache cleaning cancelled."
    fi
}

# Function to show status
show_status() {
    print_info "Model download status:"
    echo
    
    # Check if cache volume exists (try both possible names)
    if docker volume ls | grep -q "local_models_hf-model-cache" || docker volume ls | grep -q "hf-model-cache"; then
        print_success "Cache volume exists"
        cache_size
    else
        print_warning "Cache volume not found"
    fi
    
    echo
    print_info "Available models:"
    list_models
}

# Function to download models in parallel
download_parallel() {
    print_info "Starting parallel download of all models..."
    
    if ! check_hf_token; then
        print_warning "Continuing without HF_TOKEN..."
    fi
    
    # Build download image
    print_info "Building download image..."
    docker build -f Dockerfile.download -t model-downloader .
    
    # Start all downloads in parallel
    print_info "Starting parallel downloads..."
    docker-compose -f docker-compose.download.yml up -d download-qwen download-mistral download-tinyllama download-starcoder
    
    # Wait for completion
    print_info "Waiting for downloads to complete..."
    docker-compose -f docker-compose.download.yml logs -f
    
    print_success "All parallel downloads completed!"
}

# Main script logic
main() {
    case "${1:-help}" in
        "download-all")
            download_all
            ;;
        "download-model")
    if [[ -z "${2:-}" ]]; then
        print_error "Model name required"
        print_info "Use: $0 download-model MODEL_NAME"
        exit 1
    fi
    download_model "$2"
            ;;
        "list-models")
            list_models
            ;;
        "cache-size")
            cache_size
            ;;
        "clean-cache")
            clean_cache
            ;;
        "status")
            show_status
            ;;
        "parallel")
            download_parallel
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
