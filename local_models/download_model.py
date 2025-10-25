#!/usr/bin/env python3
"""
Model Pre-download Script for AI Challenge Project

This script downloads all models used in the project to local cache
for faster startup times and offline usage.

Usage:
    python download_model.py [--model MODEL_NAME] [--all]
    
Examples:
    python download_model.py --model Qwen/Qwen1.5-4B-Chat
    python download_model.py --all
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# All models used in the project
PROJECT_MODELS = [
    "Qwen/Qwen1.5-4B-Chat",
    "mistralai/Mistral-7B-Instruct-v0.2", 
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "TechxGenus/starcoder2-7b-instruct"
]

def get_hf_token() -> Optional[str]:
    """Get HuggingFace token from environment."""
    return os.environ.get("HF_TOKEN")

def download_model(model_name: str, cache_dir: Optional[str] = None) -> bool:
    """
    Download a single model to cache.
    
    Args:
        model_name: Name of the model to download
        cache_dir: Optional cache directory override
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"🔄 Starting download of {model_name}")
        
        hf_token = get_hf_token()
        if not hf_token:
            logger.warning(f"⚠️  No HF_TOKEN found for {model_name}")
        
        # Download tokenizer
        logger.info(f"📥 Downloading tokenizer for {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            token=hf_token,
            cache_dir=cache_dir
        )
        logger.info(f"✅ Tokenizer downloaded for {model_name}")
        
        # Download model with quantization config
        logger.info(f"📥 Downloading model {model_name}")
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype="float16",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quant_config,
            device_map="cpu",  # Use CPU for downloading
            token=hf_token,
            cache_dir=cache_dir
        )
        
        logger.info(f"✅ Model {model_name} downloaded and cached successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {model_name}: {str(e)}")
        return False

def download_all_models(cache_dir: Optional[str] = None) -> None:
    """
    Download all project models to cache.
    
    Args:
        cache_dir: Optional cache directory override
    """
    logger.info("🚀 Starting download of all project models")
    logger.info(f"📋 Models to download: {len(PROJECT_MODELS)}")
    
    success_count = 0
    failed_models = []
    
    for i, model_name in enumerate(PROJECT_MODELS, 1):
        logger.info(f"\n📦 [{i}/{len(PROJECT_MODELS)}] Processing {model_name}")
        
        if download_model(model_name, cache_dir):
            success_count += 1
        else:
            failed_models.append(model_name)
    
    # Summary
    logger.info(f"\n📊 Download Summary:")
    logger.info(f"✅ Successfully downloaded: {success_count}/{len(PROJECT_MODELS)}")
    
    if failed_models:
        logger.warning(f"❌ Failed models: {', '.join(failed_models)}")
    else:
        logger.info("🎉 All models downloaded successfully!")

def get_cache_size(cache_dir: Optional[str] = None) -> str:
    """Get human-readable cache size."""
    if not cache_dir:
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return "0 B"
    
    total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
    
    # Convert to human readable
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if total_size < 1024.0:
            return f"{total_size:.1f} {unit}"
        total_size /= 1024.0
    
    return f"{total_size:.1f} PB"

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Download models for AI Challenge project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_model.py --all
  python download_model.py --model Qwen/Qwen1.5-4B-Chat
  python download_model.py --model mistralai/Mistral-7B-Instruct-v0.2
  python download_model.py --list
        """
    )
    
    parser.add_argument(
        "--model", 
        help="Specific model to download"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Download all project models"
    )
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List all project models"
    )
    parser.add_argument(
        "--cache-dir",
        help="Override cache directory"
    )
    parser.add_argument(
        "--cache-size",
        action="store_true", 
        help="Show current cache size"
    )
    
    args = parser.parse_args()
    
    # Handle different commands
    if args.list:
        logger.info("📋 Project models:")
        for i, model in enumerate(PROJECT_MODELS, 1):
            logger.info(f"  {i}. {model}")
        return
    
    if args.cache_size:
        cache_size = get_cache_size(args.cache_dir)
        logger.info(f"💾 Current cache size: {cache_size}")
        return
    
    if args.all:
        download_all_models(args.cache_dir)
    elif args.model:
        if args.model not in PROJECT_MODELS:
            logger.warning(f"⚠️  Model {args.model} not in project models list")
            logger.info("Available models:")
            for model in PROJECT_MODELS:
                logger.info(f"  - {model}")
            sys.exit(1)
        
        download_model(args.model, args.cache_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
