"""Tests for Code Review Workflow

Tests the complete hybrid code review workflow.
"""

import pytest
from datetime import datetime

from app.core.state import WorkflowState
from app.workflows.code_review import create_code_review_workflow, run_code_review


# Test code samples
SIMPLE_GOOD_CODE = """
def add(a: int, b: int) -> int:
    '''Add two numbers'''
    return a + b

def subtract(a: int, b: int) -> int:
    '''Subtract b from a'''
    return a - b
"""

SIMPLE_BAD_CODE = """
def bad_function(a, b, c, d, e, f, g):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return f + g
    return 0
"""

COMPLEX_BAD_CODE = """
def process_data(data, config, options, params, flags, mode):
    result = []
    for item in data:
        if mode == 'strict':
            if item > 0:
                if item % 2 == 0:
                    if item < 100:
                        if config.get('filter'):
                            result.append(item)
        elif mode == 'lenient':
            result.append(item)
    return result
"""


@pytest.mark.asyncio
async def test_workflow_creation():
    """Test workflow graph creation"""
    graph = create_code_review_workflow()

    assert graph is not None
    assert graph.name == "code_review"


@pytest.mark.asyncio
async def test_run_code_review_simple_good():
    """Test code review on simple good code"""
    result = await run_code_review(SIMPLE_GOOD_CODE, use_llm=False)

    # Check state
    assert result.workflow_id == "code_review"
    assert "quality_score" in result.data

    # Should have high quality score
    quality_score = result.data["quality_score"]
    assert quality_score >= 70.0

    # Should pass quality check
    assert result.data["quality_pass"] is True

    # Should have functions extracted
    assert result.data["function_count"] == 2

    # Should have complexity calculated
    assert "complexity" in result.data
    assert len(result.data["complexity"]) == 2

    # Should have few or no issues
    assert result.data["issue_count"] <= 5  # May have minor info issues


@pytest.mark.asyncio
async def test_run_code_review_simple_bad():
    """Test code review on simple bad code"""
    result = await run_code_review(SIMPLE_BAD_CODE, use_llm=False)

    # Check state
    assert result.workflow_id == "code_review"

    # Should have functions extracted
    assert result.data["function_count"] == 1

    # Should detect issues
    assert result.data["issue_count"] > 0

    # Should detect specific issues
    issues = result.data["issues"]
    issue_types = [i["type"] for i in issues]

    # Should have too many args
    assert "too_many_args" in issue_types

    # Should have deep nesting
    assert "deep_nesting" in issue_types

    # Should have missing docstring
    assert "missing_docstring" in issue_types

    # Should generate suggestions
    assert len(result.data["suggestions"]) > 0


@pytest.mark.asyncio
async def test_run_code_review_quality_threshold():
    """Test quality threshold checking"""
    # Run with high threshold (should fail)
    result = await run_code_review(
        SIMPLE_BAD_CODE,
        use_llm=False,
        quality_threshold=90.0
    )

    # Should fail quality check
    assert result.data["quality_pass"] is False

    # Run with low threshold (should pass)
    result2 = await run_code_review(
        SIMPLE_BAD_CODE,
        use_llm=False,
        quality_threshold=30.0
    )

    # Should pass quality check
    assert result2.data["quality_pass"] is True


@pytest.mark.asyncio
async def test_run_code_review_complex():
    """Test code review on complex code"""
    result = await run_code_review(COMPLEX_BAD_CODE, use_llm=False)

    # Check complexity
    assert "avg_complexity" in result.data
    complexity = result.data["complexity"]

    # Should have high complexity
    assert any(c > 5 for c in complexity.values())

    # Should detect issues (though high_complexity requires > 10)
    issues = result.data["issues"]
    assert len(issues) > 0

    # Should have other issue types detected
    issue_types = [i["type"] for i in issues]
    assert "too_many_args" in issue_types or "deep_nesting" in issue_types

    # Should have suggestions
    suggestions = result.data["suggestions"]
    assert len(suggestions) > 0


@pytest.mark.asyncio
async def test_run_code_review_syntax_error():
    """Test code review with syntax error"""
    syntax_error_code = """
def broken(
    print("missing closing paren"
"""

    result = await run_code_review(syntax_error_code, use_llm=False)

    # Should have error in state
    assert len(result.errors) > 0

    # Should detect syntax error issue
    issues = result.data.get("issues", [])
    if issues:
        assert any(i["type"] == "syntax_error" for i in issues)


@pytest.mark.asyncio
async def test_run_code_review_empty_code():
    """Test code review with empty code"""
    result = await run_code_review("", use_llm=False)

    # Should have error
    assert len(result.errors) > 0
    assert "No code provided" in result.errors[0]


@pytest.mark.asyncio
async def test_workflow_state_progression():
    """Test that workflow state progresses correctly"""
    result = await run_code_review(SIMPLE_GOOD_CODE, use_llm=False)

    # Check that all expected keys are present
    expected_keys = [
        "code",
        "functions",
        "function_count",
        "complexity",
        "avg_complexity",
        "issues",
        "issue_count",
        "suggestions",
        "quality_score",
        "quality_pass"
    ]

    for key in expected_keys:
        assert key in result.data, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_workflow_iteration_tracking():
    """Test that iterations are tracked correctly"""
    result = await run_code_review(SIMPLE_BAD_CODE, use_llm=False)

    # Should have iteration count
    assert result.iteration >= 0

    # Should not exceed max iterations
    assert result.iteration < 100  # From MAX_WORKFLOW_ITERATIONS


@pytest.mark.asyncio
async def test_workflow_rule_based_suggestions():
    """Test that rule-based suggestions are always generated"""
    result = await run_code_review(SIMPLE_BAD_CODE, use_llm=False)

    # Should have rule suggestions
    assert "rule_suggestions" in result.data
    assert len(result.data["rule_suggestions"]) > 0

    # Should match combined suggestions (no LLM)
    assert result.data["suggestions"] == result.data["rule_suggestions"]


@pytest.mark.asyncio
async def test_workflow_llm_disabled():
    """Test workflow with LLM explicitly disabled"""
    result = await run_code_review(SIMPLE_BAD_CODE, use_llm=False)

    # Should not have LLM suggestions
    llm_suggestions = result.data.get("llm_suggestions", [])
    assert len(llm_suggestions) == 0

    # Should not have LLM analysis
    llm_analysis = result.data.get("llm_analysis", "")
    assert llm_analysis == ""


@pytest.mark.asyncio
async def test_workflow_issue_categorization():
    """Test that issues are properly categorized by severity"""
    result = await run_code_review(COMPLEX_BAD_CODE, use_llm=False)

    # Should have issue counts by severity
    assert "error_count" in result.data
    assert "warning_count" in result.data
    assert "info_count" in result.data

    # Total should match
    total = (
        result.data["error_count"] +
        result.data["warning_count"] +
        result.data["info_count"]
    )
    assert total == result.data["issue_count"]


@pytest.mark.asyncio
async def test_workflow_quality_scoring():
    """Test quality score calculation"""
    # Good code should have high score
    result_good = await run_code_review(SIMPLE_GOOD_CODE, use_llm=False)
    score_good = result_good.data["quality_score"]

    # Bad code should have lower score
    result_bad = await run_code_review(COMPLEX_BAD_CODE, use_llm=False)
    score_bad = result_bad.data["quality_score"]

    # Good should be higher than bad
    assert score_good > score_bad

    # Scores should be in valid range
    assert 0 <= score_good <= 100
    assert 0 <= score_bad <= 100
