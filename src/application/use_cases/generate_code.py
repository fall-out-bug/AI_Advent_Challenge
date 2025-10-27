"""Code generation use case."""

from typing import Optional

from src.domain.entities.agent_task import AgentTask, TaskStatus, TaskType
from src.domain.repositories.agent_repository import AgentRepository
from src.domain.repositories.model_repository import ModelRepository
from src.domain.services.code_quality_checker import CodeQualityChecker
from src.domain.services.token_analyzer import TokenAnalyzer
from src.domain.value_objects.quality_metrics import Metrics
from src.domain.value_objects.token_info import TokenInfo


class GenerateCodeUseCase:
    """Use case for generating code."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        model_repository: ModelRepository,
        model_client: "ModelClient",  # Forward reference
    ) -> None:
        """
        Initialize use case.

        Args:
            agent_repository: Agent repository interface
            model_repository: Model repository interface
            model_client: Model client interface
        """
        self.agent_repository = agent_repository
        self.model_repository = model_repository
        self.model_client = model_client

    async def execute(
        self,
        prompt: str,
        agent_name: str,
        model_config_id: Optional[str] = None,
    ) -> AgentTask:
        """
        Generate code based on prompt.

        Args:
            prompt: Generation prompt
            agent_name: Name of the agent
            model_config_id: Optional model configuration ID

        Returns:
            Completed agent task with generated code
        """
        task = AgentTask(
            task_id=self._generate_id(),
            task_type=TaskType.CODE_GENERATION,
            status=TaskStatus.IN_PROGRESS,
            prompt=prompt,
            agent_name=agent_name,
            model_config_id=model_config_id,
        )

        await self.agent_repository.save(task)

        try:
            response = await self._generate_code(prompt, model_config_id)
            task.mark_completed(response)

            quality_metrics = self._analyze_quality(response)
            task.quality_metrics = quality_metrics

            token_info = self._analyze_tokens(prompt, response)
            task.token_info = token_info

        except Exception as e:
            task.mark_failed()
            task.add_metadata("error", str(e))

        await self.agent_repository.save(task)
        return task

    async def _generate_code(self, prompt: str, model_config_id: Optional[str]) -> str:
        """
        Generate code using model client.

        Args:
            prompt: Generation prompt
            model_config_id: Optional model configuration ID

        Returns:
            Generated code
        """
        config = None
        if model_config_id:
            config = await self.model_repository.get_by_id(model_config_id)

        return await self.model_client.generate(prompt, config)

    def _analyze_quality(self, code: str) -> Metrics:
        """
        Analyze code quality.

        Args:
            code: Code to analyze

        Returns:
            Quality metrics
        """
        return CodeQualityChecker.calculate_overall_metrics(code)

    def _analyze_tokens(self, prompt: str, response: str) -> TokenInfo:
        """
        Analyze token usage.

        Args:
            prompt: Input prompt
            response: Output response

        Returns:
            Token information
        """
        token_count = TokenAnalyzer.create_token_count(prompt, response)
        return TokenAnalyzer.create_token_info(
            token_count=token_count,
            model_name="default",
        )

    def _generate_id(self) -> str:
        """
        Generate unique task ID.

        Returns:
            Unique identifier
        """
        import uuid

        return str(uuid.uuid4())
