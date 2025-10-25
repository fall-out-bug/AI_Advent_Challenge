"""
Docker container management for model comparison.

This module provides functionality to manage Docker containers
for different models, enabling automatic swapping during experiments.
"""

import asyncio
import logging
from typing import Dict, List, Optional

import docker

logger = logging.getLogger(__name__)


class ModelDockerManager:
    """
    Manages Docker containers for model comparison.

    Provides methods to start, stop, and swap model containers
    automatically during multi-model experiments.
    """

    def __init__(self, compose_project: str = "local_models"):
        """
        Initialize Docker manager.

        Args:
            compose_project: Docker Compose project name
        """
        try:
            self.client = docker.from_env()
            self.compose_project = compose_project
            logger.info(f"Docker manager initialized for project: {compose_project}")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def get_running_models(self) -> List[str]:
        """
        Get list of currently running model containers.

        Returns:
            List[str]: List of running model names
        """
        try:
            containers = self.client.containers.list(
                filters={"label": f"com.docker.compose.project={self.compose_project}"}
            )

            running_models = []
            for container in containers:
                # Extract model name from container name
                # Format: local_models-{model}-chat-1
                name_parts = container.name.split("-")
                if len(name_parts) >= 3:
                    model_name = name_parts[1]  # Extract model name
                    running_models.append(model_name)

            logger.info(f"Running models: {running_models}")
            return running_models

        except Exception as e:
            logger.error(f"Failed to get running models: {e}")
            return []

    def get_container_name(self, model_name: str) -> str:
        """
        Get Docker container name for model.

        Args:
            model_name: Name of the model

        Returns:
            str: Container name
        """
        return f"{self.compose_project}-{model_name}-chat-1"

    async def stop_model(self, model_name: str, timeout: int = 30) -> bool:
        """
        Stop specific model container.

        Args:
            model_name: Name of the model to stop
            timeout: Timeout in seconds

        Returns:
            bool: True if successfully stopped, False otherwise
        """
        try:
            container_name = self.get_container_name(model_name)
            container = self.client.containers.get(container_name)

            logger.info(f"Stopping container: {container_name}")
            container.stop(timeout=timeout)

            # Wait for container to actually stop
            await asyncio.sleep(2)

            logger.info(f"Successfully stopped {model_name}")
            return True

        except docker.errors.NotFound:
            logger.warning(f"Container for {model_name} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to stop {model_name}: {e}")
            return False

    async def start_model(self, model_name: str, wait_time: int = 10) -> bool:
        """
        Start specific model container.

        Args:
            model_name: Name of the model to start
            wait_time: Time to wait for health check

        Returns:
            bool: True if successfully started, False otherwise
        """
        try:
            container_name = self.get_container_name(model_name)
            container = self.client.containers.get(container_name)

            logger.info(f"Starting container: {container_name}")
            container.start()

            # Wait for health check
            logger.info(f"Waiting {wait_time}s for {model_name} to be ready...")
            await asyncio.sleep(wait_time)

            # Check if container is running
            container.reload()
            if container.status == "running":
                logger.info(f"Successfully started {model_name}")
                return True
            else:
                logger.error(f"Container {model_name} failed to start properly")
                return False

        except docker.errors.NotFound:
            logger.error(f"Container for {model_name} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to start {model_name}: {e}")
            return False

    async def swap_models(self, stop_model: str, start_model: str) -> Dict[str, bool]:
        """
        Stop one model and start another.

        Args:
            stop_model: Model to stop
            start_model: Model to start

        Returns:
            Dict[str, bool]: Results of stop and start operations
        """
        logger.info(f"Swapping models: {stop_model} -> {start_model}")

        results = {}

        # Stop the current model
        if stop_model:
            logger.info(f"Stopping {stop_model}...")
            results["stopped"] = await self.stop_model(stop_model)
        else:
            results["stopped"] = True

        # Start the new model
        logger.info(f"Starting {start_model}...")
        results["started"] = await self.start_model(start_model)

        return results

    async def ensure_model_running(self, model_name: str) -> bool:
        """
        Ensure specific model is running, start if not.

        Args:
            model_name: Name of the model

        Returns:
            bool: True if model is running, False otherwise
        """
        try:
            container_name = self.get_container_name(model_name)
            container = self.client.containers.get(container_name)

            if container.status == "running":
                logger.info(f"Model {model_name} is already running")
                return True
            else:
                logger.info(f"Model {model_name} is not running, starting...")
                return await self.start_model(model_name)

        except docker.errors.NotFound:
            logger.error(f"Container for {model_name} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to ensure {model_name} is running: {e}")
            return False

    def get_container_status(self, model_name: str) -> Optional[str]:
        """
        Get status of model container.

        Args:
            model_name: Name of the model

        Returns:
            Optional[str]: Container status or None if not found
        """
        try:
            container_name = self.get_container_name(model_name)
            container = self.client.containers.get(container_name)
            return container.status
        except docker.errors.NotFound:
            return None
        except Exception as e:
            logger.error(f"Failed to get status for {model_name}: {e}")
            return None

    async def cleanup_stopped_containers(self) -> int:
        """
        Clean up stopped containers to free resources.

        Returns:
            int: Number of containers cleaned up
        """
        try:
            containers = self.client.containers.list(
                all=True,
                filters={
                    "label": f"com.docker.compose.project={self.compose_project}",
                    "status": "exited",
                },
            )

            cleaned = 0
            for container in containers:
                try:
                    container.remove()
                    cleaned += 1
                    logger.info(f"Cleaned up container: {container.name}")
                except Exception as e:
                    logger.error(f"Failed to clean up {container.name}: {e}")

            return cleaned

        except Exception as e:
            logger.error(f"Failed to cleanup containers: {e}")
            return 0
