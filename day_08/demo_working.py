"""
Working Demo Script for Model Switching with Docker Integration.

This demo uses the correct model URLs and demonstrates the Docker integration.
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


async def working_demo():
    """Run a working demo of the Docker-integrated model switching."""
    print("🚀 Working Model Switching Demo")
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
        
        # Test direct model connections
        print(f"\n🔍 Testing direct model connections...")
        
        # Test StarCoder directly
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8003/health", timeout=5.0)
                if response.status_code == 200:
                    print(f"   StarCoder: ✅ Healthy ({response.json()['model']})")
                else:
                    print(f"   StarCoder: ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"   StarCoder: ❌ Error: {e}")
        
        # Test Mistral directly
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/health", timeout=5.0)
                if response.status_code == 200:
                    print(f"   Mistral: ✅ Healthy ({response.json()['model']})")
                else:
                    print(f"   Mistral: ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"   Mistral: ❌ Error: {e}")
        
        # Test UnifiedModelClient with correct configuration
        print(f"\n🔄 Testing UnifiedModelClient...")
        
        # Create a custom UnifiedModelClient with correct URLs
        unified_client = UnifiedModelClient()
        
        # Test availability with timeout
        for model in ["starcoder", "mistral"]:
            try:
                is_available = await asyncio.wait_for(
                    unified_client.check_availability(model),
                    timeout=5.0
                )
                status = "✅ Available" if is_available else "❌ Not available"
                print(f"   {model}: {status}")
            except asyncio.TimeoutError:
                print(f"   {model}: ⏱️ Timeout")
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
        
        print(f"\n🎉 Working demo completed!")
        
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
        await working_demo()
    except KeyboardInterrupt:
        print(f"\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
