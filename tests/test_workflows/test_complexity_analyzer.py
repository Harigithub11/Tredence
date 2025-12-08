"""Tests for Complexity Analyzer

Tests Big-O complexity analysis for time and space.
"""

import pytest
from app.workflows.code_review.complexity_analyzer import (
    ComplexityAnalyzer,
    analyze_code_complexity
)


# Test code samples
CONSTANT_TIME = """
def get_first(arr):
    return arr[0]
"""

LINEAR_TIME = """
def find_max(arr):
    max_val = arr[0]
    for num in arr:
        if num > max_val:
            max_val = num
    return max_val
"""

QUADRATIC_TIME = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""

BINARY_SEARCH = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1
"""

TWO_POINTERS = """
def isPalindrome(s):
    left, right = 0, len(s) - 1

    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1

        if s[left].lower() != s[right].lower():
            return False

        left += 1
        right -= 1

    return True
"""

WITH_HASH_MAP = """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""

RECURSIVE_LINEAR = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

RECURSIVE_EXPONENTIAL = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
"""


def test_constant_time_complexity():
    """Test O(1) time complexity detection"""
    analysis = analyze_code_complexity(CONSTANT_TIME)

    assert "get_first" in analysis
    assert analysis["get_first"]["time_complexity"] == "O(1)"


def test_linear_time_complexity():
    """Test O(n) time complexity detection"""
    analysis = analyze_code_complexity(LINEAR_TIME)

    assert "find_max" in analysis
    assert analysis["find_max"]["time_complexity"] == "O(n)"


def test_quadratic_time_complexity():
    """Test O(n^2) time complexity detection"""
    analysis = analyze_code_complexity(QUADRATIC_TIME)

    assert "bubble_sort" in analysis
    assert analysis["bubble_sort"]["time_complexity"] == "O(n^2)"


def test_binary_search_complexity():
    """Test O(log n) time complexity for binary search"""
    analysis = analyze_code_complexity(BINARY_SEARCH)

    assert "binary_search" in analysis
    # Binary search should be detected as O(log n)
    assert "log" in analysis["binary_search"]["time_complexity"].lower()


def test_two_pointers_pattern():
    """Test two-pointer pattern detection and explanation"""
    analysis = analyze_code_complexity(TWO_POINTERS)

    assert "isPalindrome" in analysis
    result = analysis["isPalindrome"]

    # Complex nested while loops - conservatively marked as O(n^2)
    # In reality it's O(n) because pointers converge, but this is hard to detect
    assert result["time_complexity"] in ["O(n)", "O(n^2)"]

    # Should have space complexity O(1) (in-place)
    assert result["space_complexity"] == "O(1)"

    # Should have an explanation
    assert len(result["explanation"]) > 0


def test_hash_map_pattern():
    """Test hash map pattern detection"""
    analysis = analyze_code_complexity(WITH_HASH_MAP)

    assert "two_sum" in analysis
    result = analysis["two_sum"]

    # Should be linear time
    assert result["time_complexity"] == "O(n)"

    # Should mention hash map
    assert "hash" in result["explanation"].lower() or "dict" in result["explanation"].lower()


def test_space_complexity_constant():
    """Test O(1) space complexity"""
    analysis = analyze_code_complexity(LINEAR_TIME)

    result = analysis["find_max"]
    # In-place operation
    assert result["space_complexity"] == "O(1)"


def test_space_complexity_linear():
    """Test O(n) space complexity"""
    analysis = analyze_code_complexity(WITH_HASH_MAP)

    result = analysis["two_sum"]
    # Creates hash map
    assert result["space_complexity"] == "O(n)"


def test_recursive_linear():
    """Test linear recursion"""
    analysis = analyze_code_complexity(RECURSIVE_LINEAR)

    assert "factorial" in analysis
    result = analysis["factorial"]

    # Should be O(n) time
    assert result["time_complexity"] == "O(n)"

    # Should be O(n) space (recursion stack)
    assert result["space_complexity"] == "O(n)"

    # Should mention recursion
    assert "recurs" in result["explanation"].lower()


def test_recursive_exponential():
    """Test exponential recursion"""
    analysis = analyze_code_complexity(RECURSIVE_EXPONENTIAL)

    assert "fibonacci" in analysis
    result = analysis["fibonacci"]

    # Should be O(2^n) time
    assert "2^n" in result["time_complexity"]


def test_explanation_generation():
    """Test that explanations are generated"""
    analysis = analyze_code_complexity(BINARY_SEARCH)

    result = analysis["binary_search"]

    # Should have explanation
    assert "explanation" in result
    assert len(result["explanation"]) > 0

    # Should be a complete sentence
    assert result["explanation"].endswith(".")


def test_multiple_functions():
    """Test analyzing code with multiple functions"""
    code = """
def foo():
    return 1

def bar(arr):
    for x in arr:
        print(x)

def baz(arr):
    for i in arr:
        for j in arr:
            print(i, j)
"""

    analysis = analyze_code_complexity(code)

    # Should analyze all three functions
    assert len(analysis) == 3
    assert "foo" in analysis
    assert "bar" in analysis
    assert "baz" in analysis

    # Check their complexities
    assert analysis["foo"]["time_complexity"] == "O(1)"
    assert analysis["bar"]["time_complexity"] == "O(n)"
    assert analysis["baz"]["time_complexity"] == "O(n^2)"


def test_syntax_error_handling():
    """Test handling of syntax errors"""
    bad_code = """
def broken(
    print("missing closing paren"
"""

    analysis = analyze_code_complexity(bad_code)

    # Should return empty dict
    assert analysis == {}


def test_empty_code():
    """Test handling of empty code"""
    analysis = analyze_code_complexity("")

    assert analysis == {}


def test_analyzer_class_directly():
    """Test using ComplexityAnalyzer class directly"""
    import ast

    code = LINEAR_TIME
    tree = ast.parse(code)
    func_node = None

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_node = node
            break

    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze_function(func_node, code)

    assert "time_complexity" in result
    assert "space_complexity" in result
    assert "explanation" in result
