"""Test agent domain interfaces."""

from src.domain.test_agent.interfaces.code_chunker import ICodeChunker
from src.domain.test_agent.interfaces.code_summarizer import ICodeSummarizer
from src.domain.test_agent.interfaces.coverage_aggregator import ICoverageAggregator
from src.domain.test_agent.interfaces.llm_service import ITestAgentLLMService
from src.domain.test_agent.interfaces.orchestrator import ITestAgentOrchestrator
from src.domain.test_agent.interfaces.reporter import ITestResultReporter
from src.domain.test_agent.interfaces.test_executor import ITestExecutor
from src.domain.test_agent.interfaces.token_counter import ITokenCounter
from src.domain.test_agent.interfaces.use_cases import (
    IExecuteTestsUseCase,
    IGenerateCodeUseCase,
    IGenerateTestsUseCase,
)

__all__ = [
    "ICodeChunker",
    "ICodeSummarizer",
    "ICoverageAggregator",
    "ITestAgentLLMService",
    "ITestAgentOrchestrator",
    "ITestResultReporter",
    "ITestExecutor",
    "ITokenCounter",
    "IGenerateTestsUseCase",
    "IGenerateCodeUseCase",
    "IExecuteTestsUseCase",
]
