"""Tests for Code Review Tools

Tests AST-based static analysis tools.
"""

import pytest
from app.workflows.code_review.tools import (
    extract_functions,
    calculate_cyclomatic_complexity,
    calculate_nesting_depth,
    detect_issues,
    generate_suggestions,
    calculate_quality_score
)


# Test code samples
SIMPLE_CODE = """
def hello(name):
    print(f"Hello {name}")
"""

COMPLEX_CODE = """
def complex_function(a, b, c, d, e, f):
    '''A complex function with issues'''
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return f
    for i in range(10):
        if i % 2 == 0:
            if i % 3 == 0:
                if i % 5 == 0:
                    print(i)
    return None
"""

GOOD_CODE = """
def calculate_sum(numbers: list) -> int:
    '''
    Calculate sum of numbers in a list.

    Args:
        numbers: List of integers

    Returns:
        Sum of all numbers
    '''
    return sum(numbers)

def multiply(a: int, b: int) -> int:
    '''Multiply two numbers'''
    return a * b
"""

SYNTAX_ERROR_CODE = """
def broken(
    print("missing closing paren"
"""


def test_extract_functions_simple():
    """Test extracting functions from simple code"""
    functions = extract_functions(SIMPLE_CODE)

    assert len(functions) == 1
    assert functions[0]["name"] == "hello"
    assert functions[0]["args"] == ["name"]
    assert functions[0]["lineno"] == 2


def test_extract_functions_complex():
    """Test extracting functions from complex code"""
    functions = extract_functions(COMPLEX_CODE)

    assert len(functions) == 1
    func = functions[0]
    assert func["name"] == "complex_function"
    assert len(func["args"]) == 6
    assert func["docstring"] == "A complex function with issues"


def test_extract_functions_multiple():
    """Test extracting multiple functions"""
    functions = extract_functions(GOOD_CODE)

    assert len(functions) == 2
    assert functions[0]["name"] == "calculate_sum"
    assert functions[1]["name"] == "multiply"
    assert functions[0]["docstring"] is not None
    assert functions[1]["docstring"] is not None


def test_extract_functions_syntax_error():
    """Test handling syntax errors"""
    functions = extract_functions(SYNTAX_ERROR_CODE)

    assert len(functions) == 1
    assert "error" in functions[0]


def test_calculate_complexity_simple():
    """Test complexity calculation for simple code"""
    complexity = calculate_cyclomatic_complexity(SIMPLE_CODE)

    assert "hello" in complexity
    assert complexity["hello"] == 1  # No decision points


def test_calculate_complexity_complex():
    """Test complexity calculation for complex code"""
    complexity = calculate_cyclomatic_complexity(COMPLEX_CODE)

    assert "complex_function" in complexity
    assert complexity["complex_function"] >= 10  # Many decision points


def test_calculate_complexity_multiple():
    """Test complexity for multiple functions"""
    complexity = calculate_cyclomatic_complexity(GOOD_CODE)

    assert len(complexity) == 2
    assert "calculate_sum" in complexity
    assert "multiply" in complexity
    assert complexity["calculate_sum"] == 1
    assert complexity["multiply"] == 1


def test_calculate_complexity_syntax_error():
    """Test complexity calculation with syntax error"""
    complexity = calculate_cyclomatic_complexity(SYNTAX_ERROR_CODE)

    assert complexity == {}


def test_detect_issues_simple():
    """Test issue detection on simple code"""
    functions = extract_functions(SIMPLE_CODE)
    issues = detect_issues(SIMPLE_CODE, functions)

    # Should have missing docstring issue
    assert any(i["type"] == "missing_docstring" for i in issues)


def test_detect_issues_complex():
    """Test issue detection on complex code"""
    functions = extract_functions(COMPLEX_CODE)
    issues = detect_issues(COMPLEX_CODE, functions)

    # Should detect multiple issues
    assert len(issues) > 0

    # Should detect too many arguments
    assert any(i["type"] == "too_many_args" for i in issues)

    # Should detect deep nesting
    assert any(i["type"] == "deep_nesting" for i in issues)

    # Note: high_complexity detection is based on complexity > 10
    # The COMPLEX_CODE has complexity of exactly 10, so it won't be flagged
    # This is correct behavior - we only flag functions with complexity > 10


def test_detect_issues_good_code():
    """Test issue detection on good code"""
    functions = extract_functions(GOOD_CODE)
    issues = detect_issues(GOOD_CODE, functions)

    # Should have no errors or warnings, only info (docstrings are present)
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    assert len(errors) == 0
    assert len(warnings) == 0


def test_detect_issues_syntax_error():
    """Test issue detection with syntax error"""
    functions = extract_functions(SYNTAX_ERROR_CODE)
    issues = detect_issues(SYNTAX_ERROR_CODE, functions)

    assert len(issues) > 0
    assert issues[0]["type"] == "syntax_error"
    assert issues[0]["severity"] == "error"


def test_generate_suggestions_no_issues():
    """Test suggestion generation with no issues"""
    suggestions = generate_suggestions([], {})

    assert len(suggestions) == 0


def test_generate_suggestions_with_issues():
    """Test suggestion generation with issues"""
    functions = extract_functions(COMPLEX_CODE)
    issues = detect_issues(COMPLEX_CODE, functions)
    complexity = calculate_cyclomatic_complexity(COMPLEX_CODE)

    suggestions = generate_suggestions(issues, complexity)

    assert len(suggestions) > 0
    # Should suggest reducing parameters
    assert any("parameter" in s.lower() for s in suggestions)
    # Should suggest reducing nesting
    assert any("nesting" in s.lower() for s in suggestions)


def test_calculate_quality_score_perfect():
    """Test quality score with no issues"""
    score = calculate_quality_score([], {"func1": 1, "func2": 2})

    assert score == 100.0


def test_calculate_quality_score_with_issues():
    """Test quality score with issues"""
    issues = [
        {"severity": "error", "type": "syntax_error", "message": "error"},
        {"severity": "warning", "type": "long_function", "message": "warning"},
        {"severity": "info", "type": "missing_docstring", "message": "info"}
    ]

    score = calculate_quality_score(issues, {})

    # Should be less than 100
    assert score < 100.0
    # Should deduct: 20 (error) + 5 (warning) + 2 (info) = 27
    assert score == 73.0


def test_calculate_quality_score_high_complexity():
    """Test quality score with high complexity"""
    complexity = {"func1": 15, "func2": 20}  # Average = 17.5

    score = calculate_quality_score([], complexity)

    # Should deduct for high complexity
    assert score < 100.0
    # Should deduct: (17.5 - 10) * 2 = 15
    assert score == 85.0


def test_calculate_quality_score_clamping():
    """Test quality score clamping to 0-100 range"""
    # Many severe issues
    issues = [{"severity": "error", "type": "test", "message": "test"}] * 10

    score = calculate_quality_score(issues, {"func": 50})

    # Should clamp to 0
    assert score == 0.0
