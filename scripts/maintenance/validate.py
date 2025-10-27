#!/usr/bin/env python
"""Validation script.

Features:
- Validate all configuration files
- Check model endpoints
- Verify storage integrity
- Test all components

Usage:
    python -m scripts.maintenance.validate
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List

from yaml import safe_load

from src.infrastructure.config.settings import Settings
from src.infrastructure.debug.debug_utils import DebugUtils
from src.infrastructure.health.model_health import ModelHealthChecker
from src.infrastructure.health.storage_health import StorageHealthChecker


def validate_yaml_file(file_path: Path) -> bool:
    """Validate YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        True if valid
    """
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        with file_path.open() as f:
            safe_load(f)
        print(f"✅ Valid YAML: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Invalid YAML: {file_path} - {e}")
        return False


def validate_json_file(file_path: Path) -> bool:
    """Validate JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        True if valid
    """
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False

    try:
        with file_path.open() as f:
            json.load(f)
        print(f"✅ Valid JSON: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Invalid JSON: {file_path} - {e}")
        return False


def validate_config_files() -> bool:
    """Validate configuration files.

    Returns:
        True if all valid
    """
    print("\n📋 Validating configuration files...")

    config_files = [
        Path("config/models.yaml"),
        Path("config/agents.yaml")
    ]

    all_valid = True
    for config_file in config_files:
        if not validate_yaml_file(config_file):
            all_valid = False

    return all_valid


def validate_storage_files(settings: Settings) -> bool:
    """Validate storage files.

    Args:
        settings: Application settings

    Returns:
        True if all valid
    """
    print("\n📋 Validating storage files...")

    storage_files = [
        settings.get_agent_storage_path(),
        settings.get_experiment_storage_path()
    ]

    all_valid = True
    for storage_file in storage_files:
        if not validate_json_file(storage_file):
            all_valid = False

    return all_valid


async def validate_health_checks() -> bool:
    """Validate health checks.

    Returns:
        True if healthy
    """
    print("\n📋 Running health checks...")

    settings = Settings.from_env()

    # Storage check
    storage_checker = StorageHealthChecker(settings)
    storage_result = await storage_checker.check()

    print(f"   Storage: {storage_result.status.value}")
    if storage_result.status.value != "healthy":
        print(f"   ⚠️  {storage_result.message}")

    # Model check
    model_checker = ModelHealthChecker()
    model_result = await model_checker.check()

    print(f"   Models: {model_result.status.value}")
    if model_result.status.value != "healthy":
        print(f"   ⚠️  {model_result.message}")

    return (
        storage_result.status.value == "healthy" and
        model_result.status.value in ["healthy", "degraded"]
    )


def validate_dependencies() -> bool:
    """Validate installed dependencies.

    Returns:
        True if dependencies are installed
    """
    print("\n📋 Checking dependencies...")

    debug = DebugUtils(Settings.from_env())
    deps = debug.check_dependencies()

    all_ok = True
    required = ["httpx", "fastapi", "pyyaml", "rich"]

    for package in required:
        status = deps.get(package, {})
        if status.get("installed"):
            print(f"   ✅ {package}")
        else:
            print(f"   ❌ {package} - not installed")
            all_ok = False

    return all_ok


def main() -> None:
    """Main entry point."""
    print("🔍 Validation Script\n")

    settings = Settings.from_env()

    results = {
        "config": validate_config_files(),
        "storage": validate_storage_files(settings),
        "health": asyncio.run(validate_health_checks()),
        "dependencies": validate_dependencies()
    }

    print("\n" + "="*50)
    print("📊 Validation Results:")
    print("="*50)

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*50)
    if all_passed:
        print("✅ All checks passed!")
    else:
        print("⚠️  Some checks failed")
    print("="*50)


if __name__ == "__main__":
    main()


