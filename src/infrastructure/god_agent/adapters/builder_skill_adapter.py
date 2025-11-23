"""Builder skill adapter for God Agent."""

import uuid
from typing import Any, Dict, List

from src.application.test_agent.use_cases.generate_code_use_case import (
    GenerateCodeUseCase,
)
from src.application.test_agent.use_cases.generate_tests_use_case import (
    GenerateTestsUseCase,
)
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus
from src.domain.god_agent.interfaces.skill_adapter import ISkillAdapter
from src.domain.god_agent.value_objects.skill import SkillType
from src.domain.test_agent.entities.test_case import TestCase
from src.infrastructure.logging import get_logger

logger = get_logger("builder_skill_adapter")


class BuilderSkillAdapter:
    """Builder skill adapter.

    Purpose:
        Wraps GenerateCodeUseCase and GenerateTestsUseCase to provide
        builder skill interface for God Agent.

    Attributes:
        generate_code_use_case: Use case for code generation.
        generate_tests_use_case: Use case for test generation.

    Example:
        >>> adapter = BuilderSkillAdapter(
        ...     generate_code_use_case,
        ...     generate_tests_use_case
        ... )
        >>> result = await adapter.execute(
        ...     {"requirements": "Create add function", "test_cases": []},
        ...     memory_snapshot
        ... )
    """

    def __init__(
        self,
        generate_code_use_case: GenerateCodeUseCase,
        generate_tests_use_case: GenerateTestsUseCase,
    ) -> None:
        """Initialize builder skill adapter.

        Args:
            generate_code_use_case: Use case for code generation.
            generate_tests_use_case: Use case for test generation.
        """
        self.generate_code_use_case = generate_code_use_case
        self.generate_tests_use_case = generate_tests_use_case
        logger.info("BuilderSkillAdapter initialized")

    async def execute(
        self, input_data: Dict[str, Any], memory_snapshot: MemorySnapshot
    ) -> SkillResult:
        """Execute builder skill.

        Purpose:
            Execute code and test generation using GenerateCodeUseCase
            and GenerateTestsUseCase, and convert result to SkillResult.

        Args:
            input_data: Input dictionary with 'requirements', optional
                'test_cases', optional 'source_code'.
            memory_snapshot: Memory snapshot for context (not used directly,
                but available for future enhancements).

        Returns:
            SkillResult with generated code, tests, and metadata.

        Example:
            >>> result = await adapter.execute(
            ...     {"requirements": "Create add function", "test_cases": []},
            ...     memory_snapshot
            ... )
            >>> result.status
            <SkillResultStatus.SUCCESS: 'success'>
        """
        try:
            # Extract input data
            requirements = input_data.get("requirements", "")
            test_cases_data = input_data.get("test_cases", [])
            source_code = input_data.get("source_code", "")

            if not requirements:
                return SkillResult(
                    result_id=str(uuid.uuid4()),
                    status=SkillResultStatus.FAILURE,
                    error="Missing 'requirements' in input_data",
                )

            # Convert test_cases_data to TestCase entities
            test_cases: List[TestCase] = []
            for tc_data in test_cases_data:
                if isinstance(tc_data, dict):
                    test_cases.append(
                        TestCase(
                            name=tc_data.get("name", "test_unknown"),
                            code=tc_data.get("code", ""),
                        )
                    )
                elif isinstance(tc_data, TestCase):
                    test_cases.append(tc_data)

            # Step 1: Generate code
            code_file = await self.generate_code_use_case.generate_code(
                requirements=requirements,
                test_cases=test_cases,
                source_code=source_code,
            )

            # Step 2: Generate tests for the generated code
            generated_tests = await self.generate_tests_use_case.generate_tests(
                code_file
            )

            # Convert to SkillResult
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.SUCCESS,
                output={
                    "code": {
                        "path": code_file.path,
                        "content": code_file.content,
                        "metadata": code_file.metadata,
                    },
                    "tests": [
                        {
                            "name": tc.name,
                            "code": tc.code,
                            "metadata": tc.metadata,
                        }
                        for tc in generated_tests
                    ],
                    "test_count": len(generated_tests),
                },
                metadata={
                    "skill_type": SkillType.BUILDER.value,
                    "code_file_path": code_file.path,
                },
            )

        except Exception as e:
            logger.error(
                "Builder skill execution failed",
                extra={"error": str(e), "input_data": input_data},
                exc_info=True,
            )
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.FAILURE,
                error=f"Builder skill error: {str(e)}",
            )

    def get_skill_id(self) -> str:
        """Get skill identifier.

        Purpose:
            Return unique identifier for builder skill.

        Returns:
            Skill type as string ('builder').

        Example:
            >>> adapter.get_skill_id()
            'builder'
        """
        return SkillType.BUILDER.value
