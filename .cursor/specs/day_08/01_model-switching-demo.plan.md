<!-- de888c88-0325-4a45-ba4b-9c9087ff0fef 2e722b10-e065-4b58-89b3-468dd97978d1 -->
# Docker Container Management Integration for Model Switching Demo

## Overview

Integrate the existing ModelDockerManager into the Model Switching Demo to automatically manage Docker containers when switching between models, implementing sequential container management (stop previous before starting next), retry with exponential backoff, health endpoint polling, and reuse of already-running containers.

## Implementation Steps

### Step 1: Enhance ModelSwitcherOrchestrator with Docker Integration

**File:** `day_08/core/model_switcher.py`

Add Docker management capabilities:

```python
# In __init__ method, add:
try:
    from utils.docker_manager import ModelDockerManager
    self.docker_manager = ModelDockerManager()
    self.use_container_management = True
    self.logger.info("Docker container management enabled")
except ImportError as e:
    self.docker_manager = None
    self.use_container_management = False
    self.logger.warning(f"Docker management disabled: {e}")
except Exception as e:
    self.docker_manager = None
    self.use_container_management = False
    self.logger.warning(f"Docker client unavailable: {e}")

# Add tracking for container state
self.running_containers: Set[str] = set()
```

### Step 2: Implement Health Endpoint Polling

**File:** `day_08/core/model_switcher.py`

Add new method for polling model health:

```python
async def _poll_model_health(
    self, 
    model_name: str, 
    max_attempts: int = 30,
    poll_interval: float = 2.0,
    timeout: float = 60.0
) -> bool:
    """
    Poll model health endpoint until ready or timeout.
    
    Args:
        model_name: Name of the model to check
        max_attempts: Maximum number of polling attempts
        poll_interval: Seconds between polls
        timeout: Total timeout in seconds
        
    Returns:
        True if model becomes healthy, False if timeout
    """
    start_time = asyncio.get_event_loop().time()
    
    for attempt in range(1, max_attempts + 1):
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout:
            self.logger.error(f"Health check timeout for {model_name} after {elapsed:.1f}s")
            return False
        
        try:
            is_available = await self.model_client.check_availability(model_name)
            if is_available:
                self.logger.info(f"{model_name} is healthy after {elapsed:.1f}s ({attempt} attempts)")
                return True
        except Exception as e:
            self.logger.debug(f"Health check attempt {attempt} failed: {e}")
        
        await asyncio.sleep(poll_interval)
    
    return False
```

### Step 3: Implement Container Start with Retry and Exponential Backoff

**File:** `day_08/core/model_switcher.py`

Add method for starting containers with retry:

```python
async def _start_container_with_retry(
    self,
    model_name: str,
    max_retries: int = 3,
    base_delay: float = 2.0
) -> bool:
    """
    Start container with exponential backoff retry.
    
    Args:
        model_name: Name of the model
        max_retries: Maximum retry attempts
        base_delay: Base delay for exponential backoff
        
    Returns:
        True if container started successfully
    """
    for attempt in range(max_retries):
        try:
            self.logger.info(f"Starting {model_name} container (attempt {attempt + 1}/{max_retries})")
            
            # Start the container
            success = await self.docker_manager.start_model(model_name, wait_time=5)
            if not success:
                raise Exception(f"Failed to start {model_name} container")
            
            # Poll health endpoint until ready
            is_healthy = await self._poll_model_health(model_name)
            if is_healthy:
                self.running_containers.add(model_name)
                return True
            else:
                self.logger.warning(f"{model_name} container started but health check failed")
                # Stop unhealthy container
                await self.docker_manager.stop_model(model_name)
                
        except Exception as e:
            self.logger.error(f"Attempt {attempt + 1} failed to start {model_name}: {e}")
        
        # Exponential backoff
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)
            self.logger.info(f"Retrying in {delay}s...")
            await asyncio.sleep(delay)
    
    return False
```

### Step 4: Update check_model_availability with Container Management

**File:** `day_08/core/model_switcher.py`

Replace existing `check_model_availability` method:

```python
async def check_model_availability(self, model_name: str) -> bool:
    """
    Check if a model is available, starting container if needed.
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        True if model is available, False otherwise
    """
    try:
        self.statistics[model_name]["availability_checks"] += 1
        
        # First check if container management is available
        if self.use_container_management and self.docker_manager:
            # Check if container is already running
            running_models = self.docker_manager.get_running_models()
            
            if model_name in running_models:
                self.logger.info(f"{model_name} container already running")
                self.running_containers.add(model_name)
            else:
                # Container not running, start it with retry
                self.logger.info(f"{model_name} container not running, starting...")
                success = await self._start_container_with_retry(model_name)
                if not success:
                    self.logger.error(f"Failed to start {model_name} after retries")
                    return False
        
        # Verify model is responding via API
        is_available = await self.model_client.check_availability(model_name)
        
        if is_available:
            self.logger.info(f"Model {model_name} is available and responding")
        else:
            self.logger.warning(f"Model {model_name} container running but not responding")
            
        return is_available
        
    except Exception as e:
        self.logger.error(f"Error checking availability for {model_name}: {e}")
        return False
```

### Step 5: Update switch_to_model with Sequential Container Management

**File:** `day_08/core/model_switcher.py`

Replace existing `switch_to_model` method:

```python
async def switch_to_model(self, model_name: str) -> bool:
    """
    Switch to the specified model, managing containers sequentially.
    
    Stops current model container before starting the new one to save resources.
    
    Args:
        model_name: Name of the model to switch to
        
    Returns:
        True if switch was successful, False otherwise
    """
    try:
        # Stop current model container if container management is enabled
        if self.use_container_management and self.docker_manager and self.current_model:
            if self.current_model != model_name and self.current_model in self.running_containers:
                self.logger.info(f"Stopping previous model: {self.current_model}")
                stop_success = await self.docker_manager.stop_model(self.current_model, timeout=30)
                if stop_success:
                    self.running_containers.discard(self.current_model)
                    self.logger.info(f"Successfully stopped {self.current_model}")
                else:
                    self.logger.warning(f"Failed to stop {self.current_model}, continuing anyway")
        
        # Check if new model is available (will start container if needed)
        if not await self.check_model_availability(model_name):
            self.statistics[model_name]["failed_switches"] += 1
            self.logger.error(f"Cannot switch to {model_name}: model not available")
            return False
        
        # Update current model
        previous_model = self.current_model
        self.current_model = model_name
        
        # Update statistics
        self.statistics[model_name]["successful_switches"] += 1
        self.statistics[model_name]["last_used"] = datetime.now()
        
        self.logger.info(f"Successfully switched from {previous_model} to {model_name}")
        return True
        
    except Exception as e:
        self.statistics[model_name]["failed_switches"] += 1
        self.logger.error(f"Failed to switch to {model_name}: {e}")
        return False
```

### Step 6: Add Cleanup Method

**File:** `day_08/core/model_switcher.py`

Add cleanup method for stopping all containers:

```python
async def cleanup_containers(self) -> None:
    """
    Stop all running model containers.
    
    Should be called at the end of the demo to clean up resources.
    """
    if not self.use_container_management or not self.docker_manager:
        return
    
    self.logger.info("Cleaning up running containers...")
    
    for model_name in list(self.running_containers):
        try:
            self.logger.info(f"Stopping {model_name}...")
            success = await self.docker_manager.stop_model(model_name, timeout=30)
            if success:
                self.running_containers.discard(model_name)
                self.logger.info(f"Successfully stopped {model_name}")
            else:
                self.logger.warning(f"Failed to stop {model_name}")
        except Exception as e:
            self.logger.error(f"Error stopping {model_name}: {e}")
    
    self.logger.info("Container cleanup completed")
```

### Step 7: Update Demo Script to Use Cleanup

**File:** `day_08/demo_model_switching.py`

Update the `ModelSwitchingDemo` class:

```python
# In run_complete_demo method, wrap with try/finally:
async def run_complete_demo(self) -> Dict[str, Any]:
    try:
        self.logger.info("Starting complete model switching demo")
        print("🚀 Starting Model Switching Demo")
        print("=" * 50)
        
        # Check model availability
        await self._check_model_availability()
        
        # Run tests for each model
        for model_name in self.config["models"]:
            if is_model_supported(model_name):
                await self._test_model(model_name)
            else:
                self.logger.warning(f"Model {model_name} not supported, skipping")
        
        # Generate summary
        self._generate_summary()
        
        # Print results
        self._print_results()
        
        self.logger.info("Model switching demo completed successfully")
        return self.results
        
    except Exception as e:
        self.logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        raise
    finally:
        # Always cleanup containers
        print("\n🧹 Cleaning up containers...")
        await self.orchestrator.cleanup_containers()
```

### Step 8: Update Configuration

**File:** `day_08/config/demo_config.py`

Add container management settings:

```python
# Add to DEMO_CONFIG:
"container_management": {
    "enabled": True,
    "sequential_switching": True,  # Stop previous before starting next
    "health_check_timeout": 60,
    "health_poll_interval": 2.0,
    "max_health_attempts": 30,
    "start_retry_attempts": 3,
    "start_retry_base_delay": 2.0,
    "stop_timeout": 30
}
```

### Step 9: Add Import for asyncio.get_event_loop

**File:** `day_08/core/model_switcher.py`

Add at the top of the file:

```python
import asyncio
```

### Step 10: Update Tests

**File:** `day_08/tests/test_model_switching_demo.py`

Add tests for container management:

```python
class TestModelSwitcherWithDocker:
    """Test cases for ModelSwitcher with Docker integration."""
    
    @pytest.fixture
    def orchestrator_with_docker(self):
        """Create orchestrator with mocked docker manager."""
        from unittest.mock import MagicMock
        orchestrator = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
        orchestrator.docker_manager = MagicMock()
        orchestrator.use_container_management = True
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_start_container_with_retry(self, orchestrator_with_docker):
        """Test container start with retry logic."""
        orchestrator_with_docker.docker_manager.start_model = AsyncMock(return_value=True)
        orchestrator_with_docker.docker_manager.get_running_models = MagicMock(return_value=["starcoder"])
        
        with patch.object(orchestrator_with_docker, '_poll_model_health', return_value=True):
            success = await orchestrator_with_docker._start_container_with_retry("starcoder")
            assert success is True
    
    @pytest.mark.asyncio
    async def test_sequential_model_switching(self, orchestrator_with_docker):
        """Test that previous model is stopped before starting new one."""
        orchestrator_with_docker.docker_manager.stop_model = AsyncMock(return_value=True)
        orchestrator_with_docker.docker_manager.start_model = AsyncMock(return_value=True)
        orchestrator_with_docker.docker_manager.get_running_models = MagicMock(return_value=[])
        orchestrator_with_docker.current_model = "starcoder"
        orchestrator_with_docker.running_containers.add("starcoder")
        
        with patch.object(orchestrator_with_docker, 'check_model_availability', return_value=True):
            with patch.object(orchestrator_with_docker, '_poll_model_health', return_value=True):
                success = await orchestrator_with_docker.switch_to_model("mistral")
                
                assert success is True
                orchestrator_with_docker.docker_manager.stop_model.assert_called_once_with("starcoder", timeout=30)
    
    @pytest.mark.asyncio
    async def test_cleanup_containers(self, orchestrator_with_docker):
        """Test container cleanup."""
        orchestrator_with_docker.running_containers = {"starcoder", "mistral"}
        orchestrator_with_docker.docker_manager.stop_model = AsyncMock(return_value=True)
        
        await orchestrator_with_docker.cleanup_containers()
        
        assert len(orchestrator_with_docker.running_containers) == 0
        assert orchestrator_with_docker.docker_manager.stop_model.call_count == 2
```

## Summary of Changes

1. **ModelSwitcherOrchestrator** enhanced with:

   - Docker manager integration
   - Health endpoint polling with timeout
   - Exponential backoff retry logic
   - Sequential container management (stop previous, start next)
   - Container state tracking
   - Cleanup method

2. **Demo script** updated to call cleanup on exit

3. **Configuration** extended with container management settings

4. **Tests** added for Docker integration scenarios

This implementation ensures efficient resource usage by running only one model at a time, with robust health checking and retry mechanisms for reliable container management.

### To-dos

- [ ] Add Docker manager integration to ModelSwitcherOrchestrator __init__ with error handling
- [ ] Implement _poll_model_health method with configurable timeout and interval
- [ ] Implement _start_container_with_retry with exponential backoff
- [ ] Update check_model_availability to use container management and reuse running containers
- [ ] Update switch_to_model to stop previous container before starting new one
- [ ] Add cleanup_containers method to stop all running containers
- [ ] Update demo_model_switching.py to call cleanup in finally block
- [ ] Add container_management configuration to demo_config.py
- [ ] Add asyncio import to model_switcher.py
- [ ] Add comprehensive tests for Docker container management in test_model_switching_demo.py