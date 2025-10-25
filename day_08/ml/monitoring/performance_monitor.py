"""
Performance monitoring system for tracking predictions and latency with drift detection.

This module provides comprehensive monitoring capabilities for ML models,
including performance tracking, drift detection, and alerting.
"""

import asyncio
import json
import statistics
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from utils.logging import LoggerFactory


class PerformanceMetrics(BaseModel):
    """Performance metrics for monitoring."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    model_name: str = Field(description="Name of the model")
    model_version: str = Field(description="Version of the model")
    
    # Latency metrics
    avg_latency: float = Field(description="Average latency in seconds")
    p50_latency: float = Field(description="50th percentile latency")
    p95_latency: float = Field(description="95th percentile latency")
    p99_latency: float = Field(description="99th percentile latency")
    
    # Throughput metrics
    requests_per_second: float = Field(description="Requests per second")
    total_requests: int = Field(description="Total number of requests")
    
    # Prediction metrics
    avg_prediction_confidence: float = Field(description="Average prediction confidence")
    prediction_accuracy: float = Field(description="Prediction accuracy")
    
    # Error metrics
    error_rate: float = Field(description="Error rate (0-1)")
    timeout_rate: float = Field(description="Timeout rate (0-1)")
    
    # Resource metrics
    cpu_usage: float = Field(description="CPU usage percentage")
    memory_usage: float = Field(description="Memory usage percentage")


class DriftDetectionResult(BaseModel):
    """Result of drift detection analysis."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    model_name: str = Field(description="Name of the model")
    
    # Drift indicators
    latency_drift: bool = Field(description="Latency drift detected")
    accuracy_drift: bool = Field(description="Accuracy drift detected")
    confidence_drift: bool = Field(description="Confidence drift detected")
    error_rate_drift: bool = Field(description="Error rate drift detected")
    
    # Drift severity
    overall_drift_score: float = Field(description="Overall drift score (0-1)")
    drift_severity: str = Field(description="Drift severity (low/medium/high)")
    
    # Detailed metrics
    latency_change: float = Field(description="Latency change percentage")
    accuracy_change: float = Field(description="Accuracy change percentage")
    confidence_change: float = Field(description="Confidence change percentage")
    error_rate_change: float = Field(description="Error rate change percentage")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")


class Alert(BaseModel):
    """Alert for performance issues."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    alert_type: str = Field(description="Type of alert")
    severity: str = Field(description="Alert severity (low/medium/high/critical)")
    model_name: str = Field(description="Model name")
    message: str = Field(description="Alert message")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Related metrics")
    resolved: bool = Field(default=False, description="Whether alert is resolved")


class PerformanceMonitor:
    """
    Performance monitor for tracking predictions and latency with drift detection.
    
    Provides comprehensive monitoring capabilities including:
    - Real-time performance tracking
    - Statistical drift detection
    - Performance alerting
    - Historical analysis
    - Resource monitoring
    """
    
    def __init__(
        self,
        window_size: int = 1000,
        drift_threshold: float = 0.1,
        alert_threshold: float = 0.2
    ):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Size of sliding window for metrics
            drift_threshold: Threshold for drift detection (0-1)
            alert_threshold: Threshold for alerting (0-1)
        """
        self.logger = LoggerFactory.create_logger(__name__)
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.alert_threshold = alert_threshold
        
        # Performance data storage
        self.performance_history: Dict[str, deque] = {
            'latency': deque(maxlen=window_size),
            'accuracy': deque(maxlen=window_size),
            'confidence': deque(maxlen=window_size),
            'error_rate': deque(maxlen=window_size),
            'requests_per_second': deque(maxlen=window_size),
            'cpu_usage': deque(maxlen=window_size),
            'memory_usage': deque(maxlen=window_size)
        }
        
        # Baseline metrics for drift detection
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        self.baseline_window_size = min(100, window_size // 10)
        
        # Alerting
        self.alerts: List[Alert] = []
        self.alert_cooldown = timedelta(minutes=5)
        self.last_alert_time: Dict[str, datetime] = {}
        
        # Model tracking
        self.current_model_name: Optional[str] = None
        self.current_model_version: Optional[str] = None
    
    def set_model(self, model_name: str, model_version: str) -> None:
        """
        Set the current model being monitored.
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
        """
        self.current_model_name = model_name
        self.current_model_version = model_version
        self.logger.info(f"Monitoring model: {model_name} v{model_version}")
    
    async def record_prediction(
        self,
        latency: float,
        accuracy: float,
        confidence: float,
        error_occurred: bool = False,
        timeout_occurred: bool = False,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None
    ) -> None:
        """
        Record a prediction with performance metrics.
        
        Args:
            latency: Prediction latency in seconds
            accuracy: Prediction accuracy (0-1)
            confidence: Prediction confidence (0-1)
            error_occurred: Whether an error occurred
            timeout_occurred: Whether a timeout occurred
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage percentage
        """
        timestamp = datetime.now()
        
        # Record metrics
        self.performance_history['latency'].append(latency)
        self.performance_history['accuracy'].append(accuracy)
        self.performance_history['confidence'].append(confidence)
        
        error_rate = 1.0 if error_occurred else 0.0
        self.performance_history['error_rate'].append(error_rate)
        
        # Calculate requests per second (simplified)
        if len(self.performance_history['latency']) > 1:
            recent_latencies = list(self.performance_history['latency'])[-10:]
            avg_latency = statistics.mean(recent_latencies)
            rps = 1.0 / max(avg_latency, 0.001)  # Avoid division by zero
            self.performance_history['requests_per_second'].append(rps)
        
        # Record resource usage
        if cpu_usage is not None:
            self.performance_history['cpu_usage'].append(cpu_usage)
        if memory_usage is not None:
            self.performance_history['memory_usage'].append(memory_usage)
        
        # Check for drift and alerts
        await self._check_drift_and_alerts()
    
    async def _check_drift_and_alerts(self) -> None:
        """Check for drift and generate alerts if necessary."""
        if len(self.performance_history['latency']) < self.baseline_window_size:
            return
        
        # Calculate current metrics
        current_metrics = self._calculate_current_metrics()
        
        # Update baseline if needed
        if self.baseline_metrics is None:
            self.baseline_metrics = current_metrics
            self.logger.info("Baseline metrics established")
            return
        
        # Detect drift
        drift_result = self._detect_drift(current_metrics)
        
        # Generate alerts if drift detected
        if drift_result.overall_drift_score > self.alert_threshold:
            await self._generate_drift_alert(drift_result)
    
    def _calculate_current_metrics(self) -> PerformanceMetrics:
        """Calculate current performance metrics."""
        if not self.performance_history['latency']:
            return PerformanceMetrics(
                model_name=self.current_model_name or "unknown",
                model_version=self.current_model_version or "unknown"
            )
        
        latencies = list(self.performance_history['latency'])
        accuracies = list(self.performance_history['accuracy'])
        confidences = list(self.performance_history['confidence'])
        error_rates = list(self.performance_history['error_rate'])
        rps_values = list(self.performance_history['requests_per_second'])
        cpu_values = list(self.performance_history['cpu_usage'])
        memory_values = list(self.performance_history['memory_usage'])
        
        return PerformanceMetrics(
            model_name=self.current_model_name or "unknown",
            model_version=self.current_model_version or "unknown",
            avg_latency=statistics.mean(latencies),
            p50_latency=self._percentile(latencies, 50),
            p95_latency=self._percentile(latencies, 95),
            p99_latency=self._percentile(latencies, 99),
            requests_per_second=statistics.mean(rps_values) if rps_values else 0.0,
            total_requests=len(latencies),
            avg_prediction_confidence=statistics.mean(confidences) if confidences else 0.0,
            prediction_accuracy=statistics.mean(accuracies) if accuracies else 0.0,
            error_rate=statistics.mean(error_rates) if error_rates else 0.0,
            timeout_rate=0.0,  # Simplified for now
            cpu_usage=statistics.mean(cpu_values) if cpu_values else 0.0,
            memory_usage=statistics.mean(memory_values) if memory_values else 0.0
        )
    
    def _detect_drift(self, current_metrics: PerformanceMetrics) -> DriftDetectionResult:
        """Detect drift in performance metrics."""
        if not self.baseline_metrics:
            return DriftDetectionResult(
                model_name=current_metrics.model_name,
                overall_drift_score=0.0,
                drift_severity="low"
            )
        
        # Calculate changes
        latency_change = self._calculate_change(
            self.baseline_metrics.avg_latency, current_metrics.avg_latency
        )
        accuracy_change = self._calculate_change(
            self.baseline_metrics.prediction_accuracy, current_metrics.prediction_accuracy
        )
        confidence_change = self._calculate_change(
            self.baseline_metrics.avg_prediction_confidence, current_metrics.avg_prediction_confidence
        )
        error_rate_change = self._calculate_change(
            self.baseline_metrics.error_rate, current_metrics.error_rate
        )
        
        # Detect drift
        latency_drift = abs(latency_change) > self.drift_threshold
        accuracy_drift = abs(accuracy_change) > self.drift_threshold
        confidence_drift = abs(confidence_change) > self.drift_threshold
        error_rate_drift = abs(error_rate_change) > self.drift_threshold
        
        # Calculate overall drift score
        drift_indicators = [latency_drift, accuracy_drift, confidence_drift, error_rate_drift]
        drift_score = sum(drift_indicators) / len(drift_indicators)
        
        # Determine severity
        if drift_score >= 0.75:
            severity = "high"
        elif drift_score >= 0.5:
            severity = "medium"
        else:
            severity = "low"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            latency_drift, accuracy_drift, confidence_drift, error_rate_drift,
            latency_change, accuracy_change, confidence_change, error_rate_change
        )
        
        return DriftDetectionResult(
            model_name=current_metrics.model_name,
            latency_drift=latency_drift,
            accuracy_drift=accuracy_drift,
            confidence_drift=confidence_drift,
            error_rate_drift=error_rate_drift,
            overall_drift_score=drift_score,
            drift_severity=severity,
            latency_change=latency_change,
            accuracy_change=accuracy_change,
            confidence_change=confidence_change,
            error_rate_change=error_rate_change,
            recommendations=recommendations
        )
    
    def _calculate_change(self, baseline: float, current: float) -> float:
        """Calculate percentage change between baseline and current values."""
        if baseline == 0:
            return 0.0 if current == 0 else float('inf')
        return (current - baseline) / baseline
    
    def _generate_recommendations(
        self,
        latency_drift: bool, accuracy_drift: bool, confidence_drift: bool, error_rate_drift: bool,
        latency_change: float, accuracy_change: float, confidence_change: float, error_rate_change: float
    ) -> List[str]:
        """Generate recommendations based on drift detection."""
        recommendations = []
        
        if latency_drift and latency_change > 0:
            recommendations.append("Consider optimizing model inference or increasing resources")
        
        if accuracy_drift and accuracy_change < 0:
            recommendations.append("Model accuracy has decreased - consider retraining or data validation")
        
        if confidence_drift and confidence_change < 0:
            recommendations.append("Model confidence has decreased - investigate input data quality")
        
        if error_rate_drift and error_rate_change > 0:
            recommendations.append("Error rate has increased - check model stability and input validation")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges")
        
        return recommendations
    
    async def _generate_drift_alert(self, drift_result: DriftDetectionResult) -> None:
        """Generate alert for drift detection."""
        alert_key = f"drift_{drift_result.model_name}"
        now = datetime.now()
        
        # Check cooldown
        if alert_key in self.last_alert_time:
            if now - self.last_alert_time[alert_key] < self.alert_cooldown:
                return
        
        # Create alert
        alert = Alert(
            alert_type="drift_detection",
            severity=drift_result.drift_severity,
            model_name=drift_result.model_name,
            message=f"Performance drift detected: {drift_result.overall_drift_score:.2f} drift score",
            metrics={
                "drift_score": drift_result.overall_drift_score,
                "latency_change": drift_result.latency_change,
                "accuracy_change": drift_result.accuracy_change,
                "confidence_change": drift_result.confidence_change,
                "error_rate_change": drift_result.error_rate_change
            }
        )
        
        self.alerts.append(alert)
        self.last_alert_time[alert_key] = now
        
        self.logger.warning(f"Drift alert generated: {alert.message}")
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for the specified time period.
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            Dict[str, Any]: Performance summary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent alerts
        recent_alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time
        ]
        
        # Calculate current metrics
        current_metrics = self._calculate_current_metrics()
        
        return {
            "current_metrics": current_metrics.dict(),
            "baseline_metrics": self.baseline_metrics.dict() if self.baseline_metrics else None,
            "recent_alerts": len(recent_alerts),
            "total_alerts": len(self.alerts),
            "unresolved_alerts": len([a for a in self.alerts if not a.resolved]),
            "data_points": len(self.performance_history['latency']),
            "monitoring_active": self.current_model_name is not None
        }
    
    def get_drift_report(self) -> Optional[DriftDetectionResult]:
        """Get latest drift detection report."""
        if not self.baseline_metrics:
            return None
        
        current_metrics = self._calculate_current_metrics()
        return self._detect_drift(current_metrics)
    
    def resolve_alert(self, alert_id: int) -> bool:
        """
        Resolve an alert by ID.
        
        Args:
            alert_id: ID of the alert to resolve
            
        Returns:
            bool: True if alert was resolved, False if not found
        """
        if 0 <= alert_id < len(self.alerts):
            self.alerts[alert_id].resolved = True
            self.logger.info(f"Alert {alert_id} resolved")
            return True
        return False
    
    def save_monitoring_data(self, file_path: Path) -> None:
        """Save monitoring data to file."""
        try:
            data = {
                "performance_history": {
                    key: list(values) for key, values in self.performance_history.items()
                },
                "baseline_metrics": self.baseline_metrics.dict() if self.baseline_metrics else None,
                "alerts": [alert.dict() for alert in self.alerts],
                "current_model": {
                    "name": self.current_model_name,
                    "version": self.current_model_version
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Saved monitoring data to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save monitoring data: {e}")
    
    def load_monitoring_data(self, file_path: Path) -> None:
        """Load monitoring data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore performance history
            for key, values in data.get("performance_history", {}).items():
                if key in self.performance_history:
                    self.performance_history[key] = deque(values, maxlen=self.window_size)
            
            # Restore baseline metrics
            if data.get("baseline_metrics"):
                self.baseline_metrics = PerformanceMetrics(**data["baseline_metrics"])
            
            # Restore alerts
            self.alerts = [Alert(**alert) for alert in data.get("alerts", [])]
            
            # Restore current model
            model_info = data.get("current_model", {})
            self.current_model_name = model_info.get("name")
            self.current_model_version = model_info.get("version")
            
            self.logger.info(f"Loaded monitoring data from {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to load monitoring data: {e}")
