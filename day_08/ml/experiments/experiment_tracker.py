"""
Experiment tracking system for managing ML experiments with configuration management and artifact storage.

This module provides comprehensive experiment tracking capabilities including:
- Experiment configuration management
- Artifact storage and versioning
- Metrics tracking and comparison
- Experiment comparison and analysis
"""

import asyncio
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from utils.logging import LoggerFactory


class ExperimentConfig(BaseModel):
    """Configuration for an experiment."""
    
    experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="Experiment name")
    description: str = Field(description="Experiment description")
    
    # Model configuration
    model_name: str = Field(description="Model name")
    model_version: str = Field(description="Model version")
    model_parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters")
    
    # Training configuration
    training_config: Dict[str, Any] = Field(default_factory=dict, description="Training configuration")
    data_config: Dict[str, Any] = Field(default_factory=dict, description="Data configuration")
    
    # Experiment metadata
    tags: List[str] = Field(default_factory=list, description="Experiment tags")
    created_by: str = Field(description="Creator of the experiment")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Status tracking
    status: str = Field(default="created", description="Experiment status")
    started_at: Optional[datetime] = Field(default=None, description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")


class ExperimentMetrics(BaseModel):
    """Metrics for an experiment."""
    
    experiment_id: str = Field(description="Experiment ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Performance metrics
    accuracy: float = Field(description="Model accuracy")
    precision: float = Field(description="Precision score")
    recall: float = Field(description="Recall score")
    f1_score: float = Field(description="F1 score")
    
    # Training metrics
    loss: float = Field(description="Training loss")
    validation_loss: float = Field(description="Validation loss")
    epochs: int = Field(description="Number of epochs")
    
    # Resource metrics
    training_time: float = Field(description="Training time in seconds")
    memory_usage: float = Field(description="Memory usage in MB")
    cpu_usage: float = Field(description="CPU usage percentage")
    
    # Custom metrics
    custom_metrics: Dict[str, Any] = Field(default_factory=dict, description="Custom metrics")


class ExperimentArtifact(BaseModel):
    """Artifact for an experiment."""
    
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = Field(description="Experiment ID")
    artifact_type: str = Field(description="Type of artifact")
    artifact_name: str = Field(description="Name of the artifact")
    file_path: str = Field(description="Path to the artifact file")
    file_size: int = Field(description="File size in bytes")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Artifact metadata")


class ExperimentRun(BaseModel):
    """A single run of an experiment."""
    
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = Field(description="Experiment ID")
    run_number: int = Field(description="Run number within experiment")
    
    # Run configuration
    config_snapshot: Dict[str, Any] = Field(description="Configuration snapshot")
    
    # Run metrics
    metrics: List[ExperimentMetrics] = Field(default_factory=list, description="Run metrics")
    
    # Run artifacts
    artifacts: List[ExperimentArtifact] = Field(default_factory=list, description="Run artifacts")
    
    # Run status
    status: str = Field(default="running", description="Run status")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    
    # Run results
    best_metrics: Optional[ExperimentMetrics] = Field(default=None, description="Best metrics")
    final_model_path: Optional[str] = Field(default=None, description="Path to final model")


class ExperimentComparison(BaseModel):
    """Comparison between experiments."""
    
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_ids: List[str] = Field(description="IDs of experiments being compared")
    comparison_metrics: List[str] = Field(description="Metrics to compare")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Comparison results
    results: Dict[str, Any] = Field(default_factory=dict, description="Comparison results")
    best_experiment: Optional[str] = Field(default=None, description="Best experiment ID")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class ExperimentTracker:
    """
    Experiment tracker for managing ML experiments with configuration management and artifact storage.
    
    Provides comprehensive experiment tracking capabilities including:
    - Experiment lifecycle management
    - Configuration versioning
    - Artifact storage and retrieval
    - Metrics tracking and analysis
    - Experiment comparison
    - Best run selection
    """
    
    def __init__(self, base_path: Path = Path("experiments")):
        """
        Initialize experiment tracker.
        
        Args:
            base_path: Base path for storing experiments
        """
        self.logger = LoggerFactory.create_logger(__name__)
        self.base_path = base_path
        self.artifacts_path = base_path / "artifacts"
        self.configs_path = base_path / "configs"
        self.metrics_path = base_path / "metrics"
        
        # Create directories
        self._create_directories()
        
        # In-memory storage
        self.experiments: Dict[str, ExperimentConfig] = {}
        self.runs: Dict[str, List[ExperimentRun]] = {}
        self.comparisons: Dict[str, ExperimentComparison] = {}
        
        # Load existing data
        self._load_existing_data()
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        for path in [self.base_path, self.artifacts_path, self.configs_path, self.metrics_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _load_existing_data(self) -> None:
        """Load existing experiment data."""
        try:
            # Load experiments
            experiments_file = self.base_path / "experiments.json"
            if experiments_file.exists():
                with open(experiments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for exp_data in data:
                        exp = ExperimentConfig(**exp_data)
                        self.experiments[exp.experiment_id] = exp
            
            # Load runs
            runs_file = self.base_path / "runs.json"
            if runs_file.exists():
                with open(runs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for exp_id, runs_data in data.items():
                        runs = [ExperimentRun(**run_data) for run_data in runs_data]
                        self.runs[exp_id] = runs
            
            # Load comparisons
            comparisons_file = self.base_path / "comparisons.json"
            if comparisons_file.exists():
                with open(comparisons_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for comp_data in data:
                        comp = ExperimentComparison(**comp_data)
                        self.comparisons[comp.comparison_id] = comp
            
            self.logger.info(f"Loaded {len(self.experiments)} experiments, {sum(len(runs) for runs in self.runs.values())} runs")
        except Exception as e:
            self.logger.error(f"Failed to load existing data: {e}")
    
    def create_experiment(
        self,
        name: str,
        description: str,
        model_name: str,
        model_version: str,
        model_parameters: Optional[Dict[str, Any]] = None,
        training_config: Optional[Dict[str, Any]] = None,
        data_config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        created_by: str = "system"
    ) -> ExperimentConfig:
        """
        Create a new experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
            model_name: Model name
            model_version: Model version
            model_parameters: Model parameters
            training_config: Training configuration
            data_config: Data configuration
            tags: Experiment tags
            created_by: Creator of the experiment
            
        Returns:
            ExperimentConfig: Created experiment configuration
        """
        experiment = ExperimentConfig(
            name=name,
            description=description,
            model_name=model_name,
            model_version=model_version,
            model_parameters=model_parameters or {},
            training_config=training_config or {},
            data_config=data_config or {},
            tags=tags or [],
            created_by=created_by
        )
        
        self.experiments[experiment.experiment_id] = experiment
        self.runs[experiment.experiment_id] = []
        
        # Save experiment configuration
        self._save_experiment_config(experiment)
        
        self.logger.info(f"Created experiment: {experiment.name} ({experiment.experiment_id})")
        return experiment
    
    def start_experiment_run(self, experiment_id: str) -> ExperimentRun:
        """
        Start a new run for an experiment.
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            ExperimentRun: Started experiment run
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        run_number = len(self.runs[experiment_id]) + 1
        
        run = ExperimentRun(
            experiment_id=experiment_id,
            run_number=run_number,
            config_snapshot=experiment.dict()
        )
        
        self.runs[experiment_id].append(run)
        
        # Update experiment status
        experiment.status = "running"
        experiment.started_at = run.started_at
        
        self.logger.info(f"Started run {run_number} for experiment {experiment.name}")
        return run
    
    def log_metrics(
        self,
        run_id: str,
        metrics: Dict[str, Any],
        custom_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log metrics for an experiment run.
        
        Args:
            run_id: ID of the experiment run
            metrics: Metrics to log
            custom_metrics: Custom metrics to log
        """
        run = self._find_run_by_id(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        experiment_metrics = ExperimentMetrics(
            experiment_id=run.experiment_id,
            accuracy=metrics.get("accuracy", 0.0),
            precision=metrics.get("precision", 0.0),
            recall=metrics.get("recall", 0.0),
            f1_score=metrics.get("f1_score", 0.0),
            loss=metrics.get("loss", 0.0),
            validation_loss=metrics.get("validation_loss", 0.0),
            epochs=metrics.get("epochs", 0),
            training_time=metrics.get("training_time", 0.0),
            memory_usage=metrics.get("memory_usage", 0.0),
            cpu_usage=metrics.get("cpu_usage", 0.0),
            custom_metrics=custom_metrics or {}
        )
        
        run.metrics.append(experiment_metrics)
        
        # Update best metrics
        if not run.best_metrics or experiment_metrics.f1_score > run.best_metrics.f1_score:
            run.best_metrics = experiment_metrics
        
        self.logger.debug(f"Logged metrics for run {run_id}")
    
    def log_artifact(
        self,
        run_id: str,
        artifact_type: str,
        artifact_name: str,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExperimentArtifact:
        """
        Log an artifact for an experiment run.
        
        Args:
            run_id: ID of the experiment run
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
            file_path: Path to the artifact file
            metadata: Artifact metadata
            
        Returns:
            ExperimentArtifact: Created artifact
        """
        run = self._find_run_by_id(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact file not found: {file_path}")
        
        # Create artifact directory
        artifact_dir = self.artifacts_path / run.experiment_id / run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy artifact file
        artifact_file_path = artifact_dir / artifact_name
        shutil.copy2(file_path, artifact_file_path)
        
        artifact = ExperimentArtifact(
            experiment_id=run.experiment_id,
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            file_path=str(artifact_file_path),
            file_size=artifact_file_path.stat().st_size,
            metadata=metadata or {}
        )
        
        run.artifacts.append(artifact)
        
        self.logger.info(f"Logged artifact {artifact_name} for run {run_id}")
        return artifact
    
    def complete_experiment_run(
        self,
        run_id: str,
        final_model_path: Optional[str] = None
    ) -> None:
        """
        Complete an experiment run.
        
        Args:
            run_id: ID of the experiment run
            final_model_path: Path to the final model
        """
        run = self._find_run_by_id(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        run.status = "completed"
        run.completed_at = datetime.now()
        run.final_model_path = final_model_path
        
        # Update experiment status
        experiment = self.experiments[run.experiment_id]
        experiment.status = "completed"
        experiment.completed_at = run.completed_at
        
        self.logger.info(f"Completed run {run_id}")
    
    def _find_run_by_id(self, run_id: str) -> Optional[ExperimentRun]:
        """Find a run by its ID."""
        for runs in self.runs.values():
            for run in runs:
                if run.run_id == run_id:
                    return run
        return None
    
    def _save_experiment_config(self, experiment: ExperimentConfig) -> None:
        """Save experiment configuration to file."""
        try:
            config_file = self.configs_path / f"{experiment.experiment_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(experiment.dict(), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save experiment config: {e}")
    
    def get_experiment(self, experiment_id: str) -> Optional[ExperimentConfig]:
        """Get experiment by ID."""
        return self.experiments.get(experiment_id)
    
    def get_experiment_runs(self, experiment_id: str) -> List[ExperimentRun]:
        """Get all runs for an experiment."""
        return self.runs.get(experiment_id, [])
    
    def get_best_run(self, experiment_id: str) -> Optional[ExperimentRun]:
        """Get the best run for an experiment."""
        runs = self.runs.get(experiment_id, [])
        if not runs:
            return None
        
        return max(runs, key=lambda r: r.best_metrics.f1_score if r.best_metrics else 0.0)
    
    def compare_experiments(
        self,
        experiment_ids: List[str],
        comparison_metrics: Optional[List[str]] = None
    ) -> ExperimentComparison:
        """
        Compare multiple experiments.
        
        Args:
            experiment_ids: IDs of experiments to compare
            comparison_metrics: Metrics to compare
            
        Returns:
            ExperimentComparison: Comparison results
        """
        if not comparison_metrics:
            comparison_metrics = ["accuracy", "precision", "recall", "f1_score"]
        
        comparison = ExperimentComparison(
            experiment_ids=experiment_ids,
            comparison_metrics=comparison_metrics
        )
        
        # Collect best runs for each experiment
        best_runs = {}
        for exp_id in experiment_ids:
            best_run = self.get_best_run(exp_id)
            if best_run and best_run.best_metrics:
                best_runs[exp_id] = best_run.best_metrics
        
        # Compare metrics
        comparison_results = {}
        for metric in comparison_metrics:
            metric_values = {}
            for exp_id, metrics in best_runs.items():
                metric_values[exp_id] = getattr(metrics, metric, 0.0)
            
            comparison_results[metric] = metric_values
        
        comparison.results = comparison_results
        
        # Find best experiment
        if best_runs:
            best_experiment = max(
                best_runs.keys(),
                key=lambda exp_id: best_runs[exp_id].f1_score
            )
            comparison.best_experiment = best_experiment
        
        # Generate recommendations
        comparison.recommendations = self._generate_comparison_recommendations(comparison)
        
        self.comparisons[comparison.comparison_id] = comparison
        
        self.logger.info(f"Created comparison for {len(experiment_ids)} experiments")
        return comparison
    
    def _generate_comparison_recommendations(self, comparison: ExperimentComparison) -> List[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []
        
        if not comparison.results:
            return recommendations
        
        # Analyze each metric
        for metric, values in comparison.results.items():
            if not values:
                continue
            
            max_value = max(values.values())
            min_value = min(values.values())
            
            if max_value - min_value > 0.1:  # Significant difference
                best_exp = max(values.keys(), key=lambda k: values[k])
                recommendations.append(
                    f"Experiment {best_exp} performs best on {metric} ({max_value:.3f})"
                )
        
        # Overall recommendation
        if comparison.best_experiment:
            recommendations.append(
                f"Overall best experiment: {comparison.best_experiment}"
            )
        
        return recommendations
    
    def get_experiment_summary(self) -> Dict[str, Any]:
        """Get summary of all experiments."""
        total_experiments = len(self.experiments)
        total_runs = sum(len(runs) for runs in self.runs.values())
        completed_experiments = len([exp for exp in self.experiments.values() if exp.status == "completed"])
        
        return {
            "total_experiments": total_experiments,
            "total_runs": total_runs,
            "completed_experiments": completed_experiments,
            "running_experiments": total_experiments - completed_experiments,
            "total_comparisons": len(self.comparisons),
            "experiments_by_status": {
                status: len([exp for exp in self.experiments.values() if exp.status == status])
                for status in ["created", "running", "completed", "failed"]
            }
        }
    
    def save_all_data(self) -> None:
        """Save all experiment data to files."""
        try:
            # Save experiments
            experiments_file = self.base_path / "experiments.json"
            with open(experiments_file, 'w', encoding='utf-8') as f:
                json.dump([exp.dict() for exp in self.experiments.values()], f, indent=2, default=str)
            
            # Save runs
            runs_file = self.base_path / "runs.json"
            runs_data = {
                exp_id: [run.dict() for run in runs]
                for exp_id, runs in self.runs.items()
            }
            with open(runs_file, 'w', encoding='utf-8') as f:
                json.dump(runs_data, f, indent=2, default=str)
            
            # Save comparisons
            comparisons_file = self.base_path / "comparisons.json"
            with open(comparisons_file, 'w', encoding='utf-8') as f:
                json.dump([comp.dict() for comp in self.comparisons.values()], f, indent=2, default=str)
            
            self.logger.info("Saved all experiment data")
        except Exception as e:
            self.logger.error(f"Failed to save experiment data: {e}")
