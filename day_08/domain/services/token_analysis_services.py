"""
Domain services for the token analysis system.

This module contains domain services that encapsulate complex business logic
that doesn't naturally belong to any single entity.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..entities.token_analysis_entities import TokenAnalysisDomain, CompressionJob, ExperimentSession
from ..value_objects.token_analysis_values import (
    TokenCount, CompressionRatio, ModelSpecification, 
    ProcessingTime, QualityScore
)


class TokenAnalysisService(ABC):
    """
    Domain service for token analysis operations.
    
    This service encapsulates complex business logic related to token analysis
    that doesn't belong to any single entity.
    """
    
    @abstractmethod
    async def analyze_text(
        self,
        text: str,
        model_spec: ModelSpecification,
        target_compression: Optional[CompressionRatio] = None
    ) -> TokenAnalysisDomain:
        """
        Analyze text for token counting and compression.
        
        Args:
            text: Text to analyze
            model_spec: Model specification
            target_compression: Optional target compression ratio
            
        Returns:
            TokenAnalysisDomain: Analysis result
        """
        pass
    
    @abstractmethod
    async def batch_analyze(
        self,
        texts: List[str],
        model_spec: ModelSpecification,
        target_compression: Optional[CompressionRatio] = None
    ) -> List[TokenAnalysisDomain]:
        """
        Analyze multiple texts in batch.
        
        Args:
            texts: List of texts to analyze
            model_spec: Model specification
            target_compression: Optional target compression ratio
            
        Returns:
            List[TokenAnalysisDomain]: List of analysis results
        """
        pass
    
    @abstractmethod
    async def compare_models(
        self,
        text: str,
        model_specs: List[ModelSpecification],
        target_compression: Optional[CompressionRatio] = None
    ) -> Dict[str, TokenAnalysisDomain]:
        """
        Compare multiple models on the same text.
        
        Args:
            text: Text to analyze
            model_specs: List of model specifications
            target_compression: Optional target compression ratio
            
        Returns:
            Dict[str, TokenAnalysisDomain]: Analysis results by model name
        """
        pass
    
    @abstractmethod
    async def validate_analysis(self, analysis: TokenAnalysisDomain) -> List[str]:
        """
        Validate an analysis result.
        
        Args:
            analysis: Analysis to validate
            
        Returns:
            List[str]: List of validation errors
        """
        pass
    
    @abstractmethod
    async def calculate_quality_metrics(
        self,
        analyses: List[TokenAnalysisDomain]
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for a set of analyses.
        
        Args:
            analyses: List of analyses
            
        Returns:
            Dict[str, Any]: Quality metrics
        """
        pass


class CompressionService(ABC):
    """
    Domain service for compression operations.
    
    This service encapsulates complex business logic related to text compression
    and compression job management.
    """
    
    @abstractmethod
    async def create_compression_job(
        self,
        original_text: str,
        target_ratio: CompressionRatio,
        strategy: str,
        priority: int = 1
    ) -> CompressionJob:
        """
        Create a new compression job.
        
        Args:
            original_text: Text to compress
            target_ratio: Target compression ratio
            strategy: Compression strategy
            priority: Job priority
            
        Returns:
            CompressionJob: Created compression job
        """
        pass
    
    @abstractmethod
    async def execute_compression(self, job: CompressionJob) -> CompressionJob:
        """
        Execute a compression job.
        
        Args:
            job: Compression job to execute
            
        Returns:
            CompressionJob: Updated compression job
        """
        pass
    
    @abstractmethod
    async def batch_compress(
        self,
        jobs: List[CompressionJob]
    ) -> List[CompressionJob]:
        """
        Execute multiple compression jobs in batch.
        
        Args:
            jobs: List of compression jobs
            
        Returns:
            List[CompressionJob]: List of updated jobs
        """
        pass
    
    @abstractmethod
    async def retry_failed_jobs(self) -> List[CompressionJob]:
        """
        Retry all failed compression jobs that can be retried.
        
        Returns:
            List[CompressionJob]: List of retried jobs
        """
        pass
    
    @abstractmethod
    async def get_compression_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get compression statistics for a date range.
        
        Args:
            start_date: Start date (None for all time)
            end_date: End date (None for all time)
            
        Returns:
            Dict[str, Any]: Compression statistics
        """
        pass


class ExperimentService(ABC):
    """
    Domain service for experiment operations.
    
    This service encapsulates complex business logic related to experiment
    management and execution.
    """
    
    @abstractmethod
    async def create_experiment_session(
        self,
        experiment_name: str,
        model_spec: ModelSpecification,
        configuration: Dict[str, Any]
    ) -> ExperimentSession:
        """
        Create a new experiment session.
        
        Args:
            experiment_name: Name of the experiment
            model_spec: Model specification
            configuration: Experiment configuration
            
        Returns:
            ExperimentSession: Created experiment session
        """
        pass
    
    @abstractmethod
    async def execute_experiment(
        self,
        session: ExperimentSession,
        test_data: List[str]
    ) -> ExperimentSession:
        """
        Execute an experiment session.
        
        Args:
            session: Experiment session to execute
            test_data: Test data for the experiment
            
        Returns:
            ExperimentSession: Updated experiment session
        """
        pass
    
    @abstractmethod
    async def compare_experiments(
        self,
        session_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple experiment sessions.
        
        Args:
            session_ids: List of session IDs to compare
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        pass
    
    @abstractmethod
    async def get_experiment_recommendations(
        self,
        session: ExperimentSession
    ) -> List[str]:
        """
        Get recommendations based on experiment results.
        
        Args:
            session: Experiment session
            
        Returns:
            List[str]: List of recommendations
        """
        pass
    
    @abstractmethod
    async def get_experiment_summary(
        self,
        experiment_name: str
    ) -> Dict[str, Any]:
        """
        Get summary of all sessions for an experiment.
        
        Args:
            experiment_name: Experiment name
            
        Returns:
            Dict[str, Any]: Experiment summary
        """
        pass


class ModelEvaluationService(ABC):
    """
    Domain service for model evaluation operations.
    
    This service encapsulates complex business logic related to model
    evaluation and performance assessment.
    """
    
    @abstractmethod
    async def evaluate_model_performance(
        self,
        model_spec: ModelSpecification,
        test_data: List[str],
        ground_truth: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate model performance on test data.
        
        Args:
            model_spec: Model specification
            test_data: Test data
            ground_truth: Optional ground truth data
            
        Returns:
            Dict[str, Any]: Performance evaluation results
        """
        pass
    
    @abstractmethod
    async def compare_model_performance(
        self,
        model_specs: List[ModelSpecification],
        test_data: List[str],
        ground_truth: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare performance of multiple models.
        
        Args:
            model_specs: List of model specifications
            test_data: Test data
            ground_truth: Optional ground truth data
            
        Returns:
            Dict[str, Dict[str, Any]]: Performance comparison results
        """
        pass
    
    @abstractmethod
    async def detect_performance_drift(
        self,
        model_spec: ModelSpecification,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect performance drift in model.
        
        Args:
            model_spec: Model specification
            current_metrics: Current performance metrics
            baseline_metrics: Baseline performance metrics
            
        Returns:
            Dict[str, Any]: Drift detection results
        """
        pass
    
    @abstractmethod
    async def generate_performance_report(
        self,
        model_spec: ModelSpecification,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate performance report for a model.
        
        Args:
            model_spec: Model specification
            metrics: Performance metrics
            
        Returns:
            Dict[str, Any]: Performance report
        """
        pass


class QualityAssessmentService(ABC):
    """
    Domain service for quality assessment operations.
    
    This service encapsulates complex business logic related to quality
    assessment and scoring.
    """
    
    @abstractmethod
    async def assess_analysis_quality(
        self,
        analysis: TokenAnalysisDomain
    ) -> QualityScore:
        """
        Assess the quality of an analysis.
        
        Args:
            analysis: Analysis to assess
            
        Returns:
            QualityScore: Quality score
        """
        pass
    
    @abstractmethod
    async def assess_compression_quality(
        self,
        job: CompressionJob
    ) -> QualityScore:
        """
        Assess the quality of a compression job.
        
        Args:
            job: Compression job to assess
            
        Returns:
            QualityScore: Quality score
        """
        pass
    
    @abstractmethod
    async def assess_experiment_quality(
        self,
        session: ExperimentSession
    ) -> QualityScore:
        """
        Assess the quality of an experiment session.
        
        Args:
            session: Experiment session to assess
            
        Returns:
            QualityScore: Quality score
        """
        pass
    
    @abstractmethod
    async def get_quality_benchmarks(self) -> Dict[str, QualityScore]:
        """
        Get quality benchmarks for different operations.
        
        Returns:
            Dict[str, QualityScore]: Quality benchmarks
        """
        pass
    
    @abstractmethod
    async def generate_quality_report(
        self,
        analyses: List[TokenAnalysisDomain],
        jobs: List[CompressionJob],
        sessions: List[ExperimentSession]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quality report.
        
        Args:
            analyses: List of analyses
            jobs: List of compression jobs
            sessions: List of experiment sessions
            
        Returns:
            Dict[str, Any]: Quality report
        """
        pass
