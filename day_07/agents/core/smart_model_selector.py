"""Smart model selection system for ChadGPT."""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"


class TaskType(Enum):
    """Task types."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ANALYSIS = "analysis"


@dataclass
class ModelRecommendation:
    """Model recommendation for a specific task."""
    model: str
    confidence: float
    reasoning: str
    max_tokens: int
    temperature: float


class SmartModelSelector:
    """Smart model selection based on task analysis."""

    def __init__(self):
        """Initialize the smart model selector."""
        self.model_capabilities = {
            "gpt-5": {
                "display_name": "GPT-5",
                "description": "Most powerful GPT model",
                "strengths": ["complex_reasoning", "code_generation", "analysis"],
                "best_for": [TaskType.CODE_GENERATION, TaskType.ANALYSIS, TaskType.OPTIMIZATION],
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.EXPERT],
                "max_tokens": 8000,
                "temperature": 0.7,
                "speed": "medium",
                "cost": "high"
            },
            "gpt-5-mini": {
                "display_name": "GPT-5 Mini",
                "description": "Fast and efficient GPT model",
                "strengths": ["fast_generation", "code_generation", "debugging"],
                "best_for": [TaskType.CODE_GENERATION, TaskType.DEBUGGING, TaskType.TESTING],
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MEDIUM],
                "max_tokens": 4000,
                "temperature": 0.7,
                "speed": "fast",
                "cost": "medium"
            },
            "gpt-5-nano": {
                "display_name": "GPT-5 Nano",
                "description": "Lightweight GPT model",
                "strengths": ["quick_tasks", "simple_generation"],
                "best_for": [TaskType.DOCUMENTATION, TaskType.TESTING],
                "complexity": [TaskComplexity.SIMPLE],
                "max_tokens": 2000,
                "temperature": 0.8,
                "speed": "very_fast",
                "cost": "low"
            },
            "claude-4.1-opus": {
                "display_name": "Claude 4.1 Opus",
                "description": "Most capable Claude model",
                "strengths": ["code_review", "analysis", "reasoning"],
                "best_for": [TaskType.CODE_REVIEW, TaskType.ANALYSIS, TaskType.OPTIMIZATION],
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.EXPERT],
                "max_tokens": 6000,
                "temperature": 0.6,
                "speed": "medium",
                "cost": "high"
            },
            "claude-4.5-sonnet": {
                "display_name": "Claude 4.5 Sonnet",
                "description": "Balanced Claude model",
                "strengths": ["balanced_performance", "code_review", "generation"],
                "best_for": [TaskType.CODE_GENERATION, TaskType.CODE_REVIEW, TaskType.DEBUGGING],
                "complexity": [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX],
                "max_tokens": 5000,
                "temperature": 0.7,
                "speed": "medium",
                "cost": "medium"
            }
        }

    def analyze_task(self, task_description: str, language: str = "python") -> Dict[str, Any]:
        """Analyze task to determine complexity and type.
        
        Args:
            task_description: Description of the task
            language: Programming language
            
        Returns:
            Dict with task analysis
        """
        task_lower = task_description.lower()
        
        # Determine task type
        task_type = self._determine_task_type(task_lower)
        
        # Determine complexity
        complexity = self._determine_complexity(task_lower, language)
        
        # Estimate code length
        estimated_length = self._estimate_code_length(task_lower)
        
        # Check for special requirements
        special_requirements = self._check_special_requirements(task_lower)
        
        return {
            "task_type": task_type,
            "complexity": complexity,
            "estimated_length": estimated_length,
            "special_requirements": special_requirements,
            "language": language
        }

    def _determine_task_type(self, task_lower: str) -> TaskType:
        """Determine the type of task."""
        if any(word in task_lower for word in ["review", "analyze", "check", "evaluate"]):
            return TaskType.CODE_REVIEW
        elif any(word in task_lower for word in ["debug", "fix", "error", "bug"]):
            return TaskType.DEBUGGING
        elif any(word in task_lower for word in ["optimize", "improve", "performance", "speed"]):
            return TaskType.OPTIMIZATION
        elif any(word in task_lower for word in ["document", "comment", "explain", "readme"]):
            return TaskType.DOCUMENTATION
        elif any(word in task_lower for word in ["test", "unit test", "pytest", "testing"]):
            return TaskType.TESTING
        elif any(word in task_lower for word in ["analyze", "analysis", "metrics", "statistics"]):
            return TaskType.ANALYSIS
        else:
            return TaskType.CODE_GENERATION

    def _determine_complexity(self, task_lower: str, language: str) -> TaskComplexity:
        """Determine task complexity."""
        # Simple tasks
        simple_keywords = ["hello world", "simple", "basic", "add", "multiply", "print"]
        if any(keyword in task_lower for keyword in simple_keywords):
            return TaskComplexity.SIMPLE
        
        # Expert tasks
        expert_keywords = [
            "machine learning", "ai", "neural network", "algorithm", "optimization",
            "distributed", "concurrent", "parallel", "microservices", "architecture",
            "design pattern", "refactoring", "scalability", "performance"
        ]
        if any(keyword in task_lower for keyword in expert_keywords):
            return TaskComplexity.EXPERT
        
        # Complex tasks
        complex_keywords = [
            "class", "inheritance", "polymorphism", "database", "api", "web",
            "framework", "library", "integration", "authentication", "security"
        ]
        if any(keyword in task_lower for keyword in complex_keywords):
            return TaskComplexity.COMPLEX
        
        # Medium tasks (default)
        return TaskComplexity.MEDIUM

    def _estimate_code_length(self, task_lower: str) -> int:
        """Estimate the length of code to be generated."""
        if "hello world" in task_lower or "simple" in task_lower:
            return 50
        elif "function" in task_lower and "class" not in task_lower:
            return 200
        elif "class" in task_lower:
            return 500
        elif "framework" in task_lower or "application" in task_lower:
            return 1000
        else:
            return 300

    def _check_special_requirements(self, task_lower: str) -> List[str]:
        """Check for special requirements."""
        requirements = []
        
        if "async" in task_lower or "await" in task_lower:
            requirements.append("async")
        if "test" in task_lower:
            requirements.append("testing")
        if "error" in task_lower or "exception" in task_lower:
            requirements.append("error_handling")
        if "type" in task_lower and "hint" in task_lower:
            requirements.append("type_hints")
        if "docstring" in task_lower or "documentation" in task_lower:
            requirements.append("documentation")
        
        return requirements

    def recommend_model(
        self, 
        task_description: str, 
        language: str = "python",
        prefer_speed: bool = False,
        prefer_quality: bool = False
    ) -> ModelRecommendation:
        """Recommend the best model for a task.
        
        Args:
            task_description: Description of the task
            language: Programming language
            prefer_speed: Prefer faster models
            prefer_quality: Prefer higher quality models
            
        Returns:
            Model recommendation
        """
        analysis = self.analyze_task(task_description, language)
        
        # Score each model
        model_scores = {}
        for model, capabilities in self.model_capabilities.items():
            score = self._calculate_model_score(
                model, capabilities, analysis, prefer_speed, prefer_quality
            )
            model_scores[model] = score
        
        # Find best model
        best_model = max(model_scores.items(), key=lambda x: x[1])
        model_name = best_model[0]
        score = best_model[1]
        
        # Get model capabilities
        capabilities = self.model_capabilities[model_name]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(model_name, capabilities, analysis, score)
        
        return ModelRecommendation(
            model=model_name,
            confidence=score,
            reasoning=reasoning,
            max_tokens=capabilities["max_tokens"],
            temperature=capabilities["temperature"]
        )

    def _calculate_model_score(
        self, 
        model: str, 
        capabilities: Dict[str, Any], 
        analysis: Dict[str, Any],
        prefer_speed: bool,
        prefer_quality: bool
    ) -> float:
        """Calculate score for a model based on task analysis."""
        score = 0.0
        
        # Task type match
        if analysis["task_type"] in capabilities["best_for"]:
            score += 0.3
        
        # Complexity match
        if analysis["complexity"] in capabilities["complexity"]:
            score += 0.3
        
        # Code length consideration
        if analysis["estimated_length"] <= capabilities["max_tokens"]:
            score += 0.2
        else:
            score -= 0.1  # Penalty for insufficient tokens
        
        # Speed preference
        if prefer_speed:
            if capabilities["speed"] == "very_fast":
                score += 0.2
            elif capabilities["speed"] == "fast":
                score += 0.1
            elif capabilities["speed"] == "slow":
                score -= 0.1
        
        # Quality preference
        if prefer_quality:
            if capabilities["cost"] == "high":  # Usually indicates higher quality
                score += 0.2
            elif capabilities["cost"] == "low":
                score -= 0.1
        
        # Special requirements
        special_reqs = analysis["special_requirements"]
        if "async" in special_reqs and "async" in capabilities.get("strengths", []):
            score += 0.1
        if "error_handling" in special_reqs and "reasoning" in capabilities.get("strengths", []):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0

    def _generate_reasoning(
        self, 
        model: str, 
        capabilities: Dict[str, Any], 
        analysis: Dict[str, Any],
        score: float
    ) -> str:
        """Generate human-readable reasoning for model selection."""
        reasons = []
        
        if analysis["task_type"] in capabilities["best_for"]:
            reasons.append(f"excellent for {analysis['task_type'].value} tasks")
        
        if analysis["complexity"] in capabilities["complexity"]:
            reasons.append(f"well-suited for {analysis['complexity'].value} complexity")
        
        if capabilities["speed"] == "very_fast":
            reasons.append("very fast execution")
        elif capabilities["speed"] == "fast":
            reasons.append("fast execution")
        
        if capabilities["cost"] == "low":
            reasons.append("cost-effective")
        elif capabilities["cost"] == "high":
            reasons.append("high-quality results")
        
        if analysis["estimated_length"] > capabilities["max_tokens"]:
            reasons.append("⚠️ may need to split large tasks")
        
        if not reasons:
            reasons.append("general purpose model")
        
        return f"{model}: {', '.join(reasons)} (confidence: {score:.2f})"

    def get_all_recommendations(
        self, 
        task_description: str, 
        language: str = "python"
    ) -> List[ModelRecommendation]:
        """Get recommendations for all models.
        
        Args:
            task_description: Description of the task
            language: Programming language
            
        Returns:
            List of model recommendations sorted by confidence
        """
        recommendations = []
        
        for model in self.model_capabilities.keys():
            analysis = self.analyze_task(task_description, language)
            capabilities = self.model_capabilities[model]
            score = self._calculate_model_score(model, capabilities, analysis, False, False)
            reasoning = self._generate_reasoning(model, capabilities, analysis, score)
            
            recommendations.append(ModelRecommendation(
                model=model,
                confidence=score,
                reasoning=reasoning,
                max_tokens=capabilities["max_tokens"],
                temperature=capabilities["temperature"]
            ))
        
        return sorted(recommendations, key=lambda x: x.confidence, reverse=True)

    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all available models.

        Returns:
            Dict with model capabilities
        """
        return self.model_capabilities.copy()


# Global instance
_smart_selector: Optional[SmartModelSelector] = None


def get_smart_selector() -> SmartModelSelector:
    """Get global smart model selector instance."""
    global _smart_selector
    if _smart_selector is None:
        _smart_selector = SmartModelSelector()
    return _smart_selector
