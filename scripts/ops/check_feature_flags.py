#!/usr/bin/env python3
"""Validate Epic 21 feature flags configuration.

Purpose:
    Ensure all required feature flags are present and set to safe defaults
    before starting Epic 21 refactoring stages.

Usage:
    python scripts/ops/check_feature_flags.py --epic 21

Exit Codes:
    0: All flags configured correctly
    1: Configuration incomplete or invalid
"""

import os
import sys
from pathlib import Path
from typing import Dict, Tuple

# Epic 21 Feature Flags Definition
EPIC_21_FLAGS: Dict[str, str] = {
    "USE_NEW_DIALOG_CONTEXT_REPO": "Stage 21_01a: Dialog Context Repository",
    "USE_NEW_HOMEWORK_REVIEW_SERVICE": "Stage 21_01b: Homework Review Service",
    "USE_NEW_STORAGE_SERVICE": "Stage 21_01c: Storage Abstraction",
    "USE_DECOMPOSED_USE_CASE": "Stage 21_01d: Use Case Decomposition",
}

# Valid flag values
VALID_VALUES = {"true", "false"}


def check_flags(epic: str) -> int:
    """Check feature flags for specified epic.

    Args:
        epic: Epic number (e.g., "21")

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    if epic != "21":
        print(f"❌ Unknown epic: {epic}")
        print("Supported epics: 21")
        return 1

    print(f"Epic {epic} Feature Flags:")
    print("-" * 60)

    all_present = True
    all_safe = True

    for flag, description in EPIC_21_FLAGS.items():
        value = os.getenv(flag)

        if value is None:
            print(f"❌ {flag}: NOT SET (required)")
            print(f"   └─ {description}")
            print("   💡 Add to .env.infra:")
            print(f"   {flag}=false")
            all_present = False
        elif value.lower() not in VALID_VALUES:
            print(f"❌ {flag}: Invalid value '{value}' (must be true/false)")
            print(f"   └─ {description}")
            all_present = False
        elif value.lower() == "false":
            print(f"✅ {flag}: False (safe)")
            print(f"   └─ {description}")
        elif value.lower() == "true":
            print(f"⚠️  {flag}: True (enabled)")
            print(f"   └─ {description}")
            print("   ⚠️  Feature enabled - ensure staging validation complete")
            all_safe = False

    print()

    if not all_present:
        print("❌ Configuration incomplete. Add missing flags to .env.infra")
        print("\nExample .env.infra additions:")
        print("# Epic 21 Feature Flags (added YYYY-MM-DD)")
        print("# Reference: docs/specs/epic_21/stage_21_00_preparation.md")
        for flag in EPIC_21_FLAGS.keys():
            if os.getenv(flag) is None:
                print(f"{flag}=false")
        return 1

    if all_safe:
        print("✅ All flags configured correctly (safe defaults)")
        print("\n🚀 Ready to start Epic 21 implementation")
    else:
        print("⚠️  Some flags enabled - proceed with caution")
        print("   Ensure staging validation is complete before production rollout")

    return 0


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check Epic feature flags configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ops/check_feature_flags.py --epic 21
  python scripts/ops/check_feature_flags.py --epic 21  # Check all Epic 21 flags

Exit Codes:
  0: All flags configured correctly
  1: Configuration incomplete or invalid
        """,
    )

    parser.add_argument(
        "--epic", default="21", help="Epic number to check (default: 21)"
    )

    args = parser.parse_args()

    try:
        exit_code = check_flags(args.epic)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
