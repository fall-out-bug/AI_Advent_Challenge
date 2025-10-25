"""
Quick Demo Script for Model Switching with Docker Integration.

This is a simplified version that demonstrates the Docker integration
without hanging on container startup.
"""

import asyncio
import sys
from pathlib import Path

# Add shared package to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient
from core.model_switcher import ModelSwitcherOrchestrator
from utils.logging import LoggerFactory

logger = LoggerFactory.create_logger(__name__)


async def quick_demo():
    """Run a quick demo of the Docker-integrated model switching."""
    print("🚀 Quick Model Switching Demo")
    print("=" * 40)
    
    try:
        # Initialize orchestrator
        orchestrator = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
        
        print(f"✅ Orchestrator initialized")
        print(f"✅ Container management: {orchestrator.use_container_management}")
        print(f"✅ Docker manager: {orchestrator.docker_manager is not None}")
        
        # Check what containers are running
        if orchestrator.use_container_management and orchestrator.docker_manager:
            running_models = orchestrator.docker_manager.get_running_models()
            print(f"📦 Currently running containers: {running_models}")
        
        # Quick availability check with timeout
        print(f"\n🔍 Quick availability check...")
        
        for model in ["starcoder", "mistral"]:
            try:
                # Use a shorter timeout for quick demo
                is_available = await asyncio.wait_for(
                    orchestrator.unified_client.check_availability(model),
                    timeout=5.0
                )
                status = "✅ Available" if is_available else "❌ Not available"
                print(f"   {model}: {status}")
            except asyncio.TimeoutError:
                print(f"   {model}: ⏱️ Timeout (taking too long)")
            except Exception as e:
                print(f"   {model}: ❌ Error: {e}")
        
        # Test model switching if models are available
        print(f"\n🔄 Testing model switching...")
        
        # Try to switch to starcoder
        try:
            success = await asyncio.wait_for(
                orchestrator.switch_to_model("starcoder"),
                timeout=10.0
            )
            if success:
                print(f"✅ Successfully switched to starcoder")
                print(f"   Current model: {orchestrator.get_current_model()}")
            else:
                print(f"❌ Failed to switch to starcoder")
        except asyncio.TimeoutError:
            print(f"⏱️ Model switching timed out")
        except Exception as e:
            print(f"❌ Model switching error: {e}")
        
        # Show statistics
        print(f"\n📊 Statistics:")
        stats = orchestrator.get_model_statistics()
        for model, stat in stats.items():
            print(f"   {model}: {stat['availability_checks']} availability checks")
        
        print(f"\n🎉 Quick demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")
    
    finally:
        # Always cleanup
        print(f"\n🧹 Cleaning up...")
        try:
            await orchestrator.cleanup_containers()
            print(f"✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


async def main():
    """Main function."""
    try:
        await quick_demo()
    except KeyboardInterrupt:
        print(f"\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
