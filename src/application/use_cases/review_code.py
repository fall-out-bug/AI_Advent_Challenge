"""Code review use case."""

from typing import Optional

from src.domain.entities.agent_task import AgentTask, TaskStatus, TaskType
from src.domain.repositories.agent_repository import AgentRepository
from src.domain.repositories.model_repository import ModelRepository
from src.domain.services.code_quality_checker import CodeQualityChecker
from src.domain.services.token_analyzer import TokenAnalyzer
from src.domain.value_objects.token_info import TokenInfo


class ReviewCodeUseCase:
    """Use case for reviewing code."""

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
        code: str,
        agent_name: str,
        model_config_id: Optional[str] = None,
    ) -> AgentTask:
        """
        Review code and provide feedback.

        Args:
            code: Code to review
            agent_name: Name of the agent
            model_config_id: Optional model configuration ID

        Returns:
            Completed agent task with review
        """
        prompt = f"Review the following code:\n\n{code}"
        task = AgentTask(
            task_id=self._generate_id(),
            task_type=TaskType.CODE_REVIEW,
            status=TaskStatus.IN_PROGRESS,
            prompt=prompt,
            agent_name=agent_name,
            model_config_id=model_config_id,
        )

        await self.agent_repository.save(task)

        try:
            quality_metrics = CodeQualityChecker.calculate_overall_metrics(code)
            task.quality_metrics = quality_metrics

            review = await self._generate_review(code, model_config_id)
            task.mark_completed(review)

            token_info = self._analyze_tokens(prompt, review)
            task.token_info = token_info

        except Exception as e:
            task.mark_failed()
            task.add_metadata("error", str(e))

        await self.agent_repository.save(task)
        return task

    async def _generate_review(self, code: str, model_config_id: Optional[str]) -> str:
        """
        Generate code review using model.

        Args:
            code: Code to review
            model_config_id: Optional model configuration ID

        Returns:
            Review feedback
        """
        config = None
        if model_config_id:
            config = await self.model_repository.get_by_id(model_config_id)

        prompt = (
            f"Review this code for quality, best practices, "
            f"and potential issues:\n\n{code}"
        )
        return await self.model_client.generate(prompt, config)

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
