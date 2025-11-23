"""Unit tests for Skill value object."""

import pytest

from src.domain.god_agent.value_objects.skill import Skill, SkillContract, SkillType


def test_skill_creation():
    """Test Skill creation with valid contract."""
    contract = SkillContract(
        input_schema={"input": "dict", "query": "string", "context": "dict"},
        output_schema={"output": "dict", "result": "string", "citations": "list"},
    )
    skill = Skill(
        skill_type=SkillType.RESEARCH,
        contract=contract,
    )

    assert skill.skill_type == SkillType.RESEARCH
    assert skill.contract == contract


def test_skill_contract_validation_empty_input():
    """Test SkillContract validation - empty input schema."""
    with pytest.raises(ValueError, match="input_schema cannot be empty"):
        SkillContract(input_schema={}, output_schema={"output": "dict"})


def test_skill_contract_validation_empty_output():
    """Test SkillContract validation - empty output schema."""
    with pytest.raises(ValueError, match="output_schema cannot be empty"):
        SkillContract(
            input_schema={"input": "dict"},
            output_schema={},
        )


def test_skill_contract_validation_missing_keys():
    """Test SkillContract validation - missing required keys."""
    with pytest.raises(ValueError, match="input_schema must contain 'input'"):
        SkillContract(
            input_schema={"wrong_key": "string"},
            output_schema={"output": "string"},
        )


def test_skill_all_types():
    """Test Skill with all skill types."""
    contract = SkillContract(
        input_schema={"input": "dict"},
        output_schema={"output": "dict"},
    )

    for skill_type in SkillType:
        skill = Skill(skill_type=skill_type, contract=contract)
        assert skill.skill_type == skill_type
        assert skill.contract == contract


def test_skill_immutability():
    """Test Skill immutability."""
    contract = SkillContract(
        input_schema={"input": "dict"},
        output_schema={"output": "dict"},
    )
    skill = Skill(skill_type=SkillType.BUILDER, contract=contract)

    with pytest.raises(AttributeError):
        skill.skill_type = SkillType.REVIEWER  # type: ignore

    with pytest.raises(AttributeError):
        skill.contract = SkillContract(  # type: ignore
            input_schema={"input": "dict", "new": "dict"},
            output_schema={"output": "dict", "new": "dict"},
        )
