"""Unit tests for experiment templates.

Following TDD principles and the Zen of Python.
"""

import pytest
import tempfile
from pathlib import Path
import yaml

from src.domain.templates.experiment_template import (
    ExperimentTemplate,
    list_available_templates,
)


class TestExperimentTemplateLoading:
    """Test experiment template loading."""

    def test_loads_from_file(self):
        """Test loading template from file."""
        # Create temporary template file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(
                {
                    "experiment": {
                        "name": "test_experiment",
                        "description": "Test experiment",
                    }
                },
                f,
            )
            template_path = Path(f.name)

        try:
            template = ExperimentTemplate.load_from_file(template_path)
            assert template.get_experiment_name() == "test_experiment"
            assert template.get_description() == "Test experiment"
        finally:
            template_path.unlink()

    def test_loads_from_name(self):
        """Test loading template by name."""
        template = ExperimentTemplate.load_from_name("model_comparison")
        assert template is not None
        assert template.get_experiment_name() == "model_comparison"

    def test_requires_experiment_key(self):
        """Test that experiment key is required."""
        config = {"invalid": "data"}

        with pytest.raises(ValueError, match="experiment"):
            ExperimentTemplate(config)

    def test_requires_name_field(self):
        """Test that name field is required."""
        config = {"experiment": {"description": "Test"}}

        with pytest.raises(ValueError, match="name"):
            ExperimentTemplate(config)


class TestExperimentTemplateProperties:
    """Test experiment template properties."""

    def test_get_experiment_name(self):
        """Test getting experiment name."""
        template = ExperimentTemplate.load_from_name("model_comparison")
        name = template.get_experiment_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_description(self):
        """Test getting description."""
        template = ExperimentTemplate.load_from_name("model_comparison")
        description = template.get_description()
        assert isinstance(description, str)

    def test_get_models(self):
        """Test getting models list."""
        template = ExperimentTemplate.load_from_name("model_comparison")
        models = template.get_models()
        assert isinstance(models, list)

    def test_get_metrics(self):
        """Test getting metrics list."""
        template = ExperimentTemplate.load_from_name("model_comparison")
        metrics = template.get_metrics()
        assert isinstance(metrics, list)

    def test_get_aggregation_strategy(self):
        """Test getting aggregation strategy."""
        template = ExperimentTemplate.load_from_name("model_comparison")
        strategy = template.get_aggregation_strategy()
        assert isinstance(strategy, str)

    def test_get_task_description(self):
        """Test getting task description."""
        template = ExperimentTemplate.load_from_name("model_comparison")
        description = template.get_task_description()
        # May be None or string
        assert description is None or isinstance(description, str)


class TestTemplateList:
    """Test listing available templates."""

    def test_lists_available_templates(self):
        """Test listing available templates."""
        templates = list_available_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

    def test_templates_have_valid_names(self):
        """Test that template names are valid."""
        templates = list_available_templates()

        for name in templates:
            # Should be able to load template
            template = ExperimentTemplate.load_from_name(name)
            assert template is not None
