"""
Primary demo script for Day 08 Token Analysis System.

This is the main entry point for running demonstrations.
Uses the enhanced demo system with comprehensive reporting.
"""

import asyncio
import argparse
from demo_enhanced import EnhancedModelSwitchingDemo, main as enhanced_main


async def main():
    """
    Run the enhanced demo (primary demo system).
    
    This function serves as the main entry point for running demonstrations
    of the token analysis system with comprehensive reporting.
    
    Example:
        ```bash
        python demo.py
        python demo.py --model starcoder
        python demo.py --all
        ```
    """
    print("🚀 Day 08 Token Analysis Demo")
    print("=" * 80)
    print("Running enhanced demonstration with comprehensive reporting...")
    print()
    
    # Delegate to enhanced demo
    await enhanced_main()


if __name__ == "__main__":
    asyncio.run(main())
