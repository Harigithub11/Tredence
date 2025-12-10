"""Test Case Generation and Validation for Code Review

Generates test cases based on function patterns and safely executes code to validate correctness.
Includes timeout enforcement, float tolerance, and signature-based function calling.

Hybrid test generation:
1. Pattern-based tests (fast, curated, accurate)
2. LLM-generated tests (fallback, works for any function)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import ast
import io
import sys
import inspect
import signal
import math
import json
import re
from contextlib import redirect_stdout, redirect_stderr
from multiprocessing import Process, Queue
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Represents a single test case with inputs and expected output."""
    input_args: List[Any]
    expected: Any
    description: str = ""

    def __init__(self, input_args: Any, expected: Any, description: str = ""):
        # Normalize input to list format
        if isinstance(input_args, list):
            self.input_args = input_args
        else:
            self.input_args = [input_args]
        self.expected = expected
        self.description = description


async def generate_test_cases_with_llm(
    func_name: str,
    code: str,
    func_info: Dict[str, Any]
) -> List[TestCase]:
    """
    Use LLM to generate test cases for any function.

    This is a fallback when pattern matching fails.
    Uses Gemini to intelligently generate test cases based on function code.

    Args:
        func_name: Name of the function
        code: Full source code
        func_info: Function metadata from AST

    Returns:
        List of TestCase objects (empty if LLM fails)
    """
    from app.llm import GeminiClient

    llm_client = GeminiClient()
    if not llm_client.enabled:
        logger.warning("LLM client not enabled, cannot generate tests")
        return []

    args = func_info.get('args', [])

    prompt = f"""Generate 5 test cases for this Python function.

FUNCTION CODE:
```python
{code}
```

FUNCTION NAME: {func_name}
PARAMETERS: {args}

Return ONLY valid JSON array with this exact format:
[
  {{"input": [arg1, arg2, ...], "expected": result, "description": "Test description"}},
  {{"input": [arg1, arg2, ...], "expected": result, "description": "Test description"}}
]

Rules:
- input must be a list of arguments matching the function signature
- For single-parameter functions expecting a list, wrap the list: input: [[1,2,3]]
- expected must be the correct output for that input
- Include edge cases (empty, negative, zero, large values, single element)
- Return ONLY the JSON array, no markdown, no explanations

Example for factorial(n):
[
  {{"input": [5], "expected": 120, "description": "Factorial of 5"}},
  {{"input": [0], "expected": 1, "description": "Edge case: 0"}},
  {{"input": [1], "expected": 1, "description": "Edge case: 1"}},
  {{"input": [10], "expected": 3628800, "description": "Larger number"}},
  {{"input": [3], "expected": 6, "description": "Small number"}}
]

Example for find_max(numbers):
[
  {{"input": [[3, 9, 2]], "expected": 9, "description": "Mixed numbers"}},
  {{"input": [[-5, -2, -10]], "expected": -2, "description": "All negative"}},
  {{"input": [[7]], "expected": 7, "description": "Single element"}},
  {{"input": [[1, 1, 1]], "expected": 1, "description": "All same"}}
]
"""

    try:
        response = await llm_client.generate_content(prompt, temperature=0.1)

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            logger.warning(f"No JSON array found in LLM response for '{func_name}'")
            return []

        test_data = json.loads(json_match.group(0))

        # Validate and convert to TestCase objects
        tests = []
        for item in test_data:
            if 'input' in item and 'expected' in item:
                tests.append(TestCase(
                    input_args=item['input'],
                    expected=item['expected'],
                    description=item.get('description', 'LLM-generated test')
                ))

        logger.info(f"Generated {len(tests)} LLM-based tests for '{func_name}'")
        return tests

    except Exception as e:
        logger.error(f"LLM test generation failed for '{func_name}': {e}")
        return []


async def generate_test_cases(
    func_name: str,
    code: str,
    func_info: Dict[str, Any],
    use_llm: bool = False
) -> List[TestCase]:
    """
    Generate test cases using hybrid approach:
    1. Try pattern matching first (fast, accurate)
    2. Fall back to LLM generation if no pattern match (smart, works for any function)
    3. Return empty list if both fail (graceful degradation)

    Args:
        func_name: Name of the function
        code: Full source code
        func_info: Function metadata from AST extraction
        use_llm: Whether to use LLM for test generation fallback

    Returns:
        List of TestCase objects (may be empty)
    """
    tests: List[TestCase] = []
    func_lower = func_name.lower()

    # Pattern: find_max, get_max, maximum, largest, biggest
    if any(keyword in func_lower for keyword in ["max", "maximum", "largest", "biggest"]):
        tests = [
            TestCase([[3, 9, 2]], 9, "Mixed positive numbers"),
            TestCase([[1, 2, 3, 4, 5]], 5, "Ascending order"),
            TestCase([[10, 5, 3, 1]], 10, "Descending order"),
            TestCase([[-10, -4, -7]], -4, "Negative numbers"),
            TestCase([[5]], 5, "Single element"),
            TestCase([[7, 7, 7]], 7, "All same values"),
        ]

    # Pattern: find_min, get_min, minimum, smallest
    elif any(keyword in func_lower for keyword in ["min", "minimum", "smallest"]):
        tests = [
            TestCase([[3, 9, 2]], 2, "Mixed positive numbers"),
            TestCase([[1, 2, 3, 4, 5]], 1, "Ascending order"),
            TestCase([[10, 5, 3, 1]], 1, "Descending order"),
            TestCase([[-10, -4, -7]], -10, "Negative numbers"),
            TestCase([[5]], 5, "Single element"),
        ]

    # Pattern: sum, total, add
    elif any(keyword in func_lower for keyword in ["sum", "total", "add"]):
        tests = [
            TestCase([[1, 2, 3]], 6, "Small positive numbers"),
            TestCase([[10, 20, 30]], 60, "Larger numbers"),
            TestCase([[-5, 5]], 0, "Canceling values"),
            TestCase([[0, 0, 0]], 0, "All zeros"),
        ]

    # Pattern: average, mean, avg
    elif any(keyword in func_lower for keyword in ["avg", "average", "mean"]):
        tests = [
            TestCase([[2, 4, 6]], 4.0, "Even numbers"),
            TestCase([[1, 2, 3, 4, 5]], 3.0, "Sequential"),
            TestCase([[10]], 10.0, "Single element"),
        ]

    # Pattern: duplicate, find_duplicates
    elif any(keyword in func_lower for keyword in ["duplicate", "dup"]):
        tests = [
            TestCase([[1, 2, 3, 2, 4]], [2], "One duplicate"),
            TestCase([[1, 1, 2, 2, 3]], [1, 2], "Multiple duplicates"),
            TestCase([[1, 2, 3]], [], "No duplicates"),
            TestCase([[5, 5, 5]], [5], "All duplicates"),
        ]

    # Pattern: sort, order, arrange
    elif any(keyword in func_lower for keyword in ["sort", "order", "arrange"]):
        tests = [
            TestCase([[3, 1, 2]], [1, 2, 3], "Unsorted"),
            TestCase([[1, 2, 3]], [1, 2, 3], "Already sorted"),
            TestCase([[3, 2, 1]], [1, 2, 3], "Reverse order"),
        ]

    # Pattern: reverse
    elif "reverse" in func_lower:
        tests = [
            TestCase([[1, 2, 3]], [3, 2, 1], "Simple reversal"),
            TestCase([[5]], [5], "Single element"),
            TestCase([[1, 2]], [2, 1], "Two elements"),
        ]

    # Pattern: search, find, contains
    elif any(keyword in func_lower for keyword in ["search", "find", "contains"]):
        tests = [
            TestCase([[1, 2, 3], 2], True, "Element exists"),
            TestCase([[1, 2, 3], 5], False, "Element not found"),
        ]

    # Pattern: count, frequency
    elif any(keyword in func_lower for keyword in ["count", "frequency"]):
        tests = [
            TestCase([[1, 2, 2, 3], 2], 2, "Count occurrences"),
            TestCase([[1, 2, 3], 5], 0, "Not found"),
        ]

    # STEP 1: If pattern matched, return immediately
    if tests:
        logger.info(f"Generated {len(tests)} pattern-based tests for '{func_name}'")
        return tests

    # STEP 2: No pattern match - try LLM if enabled
    if use_llm:
        logger.info(f"No pattern match for '{func_name}', trying LLM test generation")
        llm_tests = await generate_test_cases_with_llm(func_name, code, func_info)
        if llm_tests:
            return llm_tests

    # STEP 3: No pattern and no LLM - return empty list (graceful degradation)
    logger.warning(f"No tests generated for '{func_name}' (pattern match failed, LLM disabled or failed)")
    return []


# Legacy sync wrapper for backward compatibility (if needed)
def generate_test_cases_sync(func_name: str, code: str, func_info: Dict[str, Any]) -> List[TestCase]:
    """
    Synchronous wrapper for generate_test_cases (pattern-based only).
    Use this only if you cannot use async/await.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(generate_test_cases(func_name, code, func_info, use_llm=False))


# Keep the old logging for compatibility
def _log_test_generation_legacy(func_name: str, tests: List[TestCase]):
    logger.info(f"Generated {len(tests)} test cases for function '{func_name}'")
    return tests


def _call_function_for_tests(func: Any, test_input: List[Any]) -> Any:
    """
    Intelligently call a function based on its signature.

    Uses inspect.signature() to determine how to pass arguments:
    - Single parameter: pass as single argument (list or value)
    - Multiple parameters: unpack test_input
    - Variadic (*args): unpack test_input

    Args:
        func: The function to call
        test_input: List of arguments to pass

    Returns:
        Function result
    """
    try:
        signature = inspect.signature(func)
        params = [
            p for p in signature.parameters.values()
            if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        has_varargs = any(
            p.kind == inspect.Parameter.VAR_POSITIONAL
            for p in signature.parameters.values()
        )

        positional_count = len(params)

        # Single parameter function (e.g., def func(numbers))
        if positional_count == 1 and not has_varargs:
            # Pass first element if single arg, otherwise pass whole list
            arg = test_input[0] if len(test_input) == 1 else test_input
            return func(arg)

        # Multiple parameters or variadic function
        return func(*test_input)

    except Exception:
        # Fallback to unpacking if signature inspection fails
        return func(*test_input)


def _execute_with_timeout(code: str, func_name: str, test_input: List[Any], timeout: int, result_queue: Queue) -> None:
    """
    Execute function in a separate process with timeout.

    Args:
        code: Python source code
        func_name: Function name to call
        test_input: Arguments to pass
        timeout: Timeout in seconds
        result_queue: Queue to store result
    """
    try:
        namespace: Dict[str, Any] = {}
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, namespace)

            if func_name not in namespace:
                result_queue.put({
                    "success": False,
                    "result": None,
                    "error": f"Function '{func_name}' not found in code",
                    "stdout": "",
                    "stderr": "",
                })
                return

            func = namespace[func_name]
            result = _call_function_for_tests(func, test_input)

        result_queue.put({
            "success": True,
            "result": result,
            "error": None,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
        })

    except Exception as e:
        result_queue.put({
            "success": False,
            "result": None,
            "error": f"{type(e).__name__}: {str(e)}",
            "stdout": "",
            "stderr": "",
        })


def safe_execute(code: str, func_name: str, test_input: List[Any], timeout: int = 2) -> Dict[str, Any]:
    """
    Safely execute code with given input and return the result.

    Features:
    - Timeout enforcement using multiprocessing
    - Isolated execution environment
    - Stdout/stderr capture
    - Signature-based function calling

    Args:
        code: Python source code containing the function
        func_name: Name of the function to call
        test_input: Arguments to pass to the function
        timeout: Execution timeout in seconds (default: 2)

    Returns:
        Dict with keys: 'success', 'result', 'error', 'stdout', 'stderr'
    """
    try:
        # Use multiprocessing for timeout enforcement
        result_queue: Queue = Queue()
        process = Process(
            target=_execute_with_timeout,
            args=(code, func_name, test_input, timeout, result_queue)
        )

        process.start()
        process.join(timeout=timeout)

        if process.is_alive():
            # Timeout occurred
            process.terminate()
            process.join()
            return {
                "success": False,
                "result": None,
                "error": f"Execution timeout after {timeout} seconds (possible infinite loop)",
                "stdout": "",
                "stderr": "",
            }

        # Get result from queue
        if not result_queue.empty():
            return result_queue.get()
        else:
            return {
                "success": False,
                "result": None,
                "error": "Process ended without returning result",
                "stdout": "",
                "stderr": "",
            }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Execution error: {type(e).__name__}: {str(e)}",
            "stdout": "",
            "stderr": "",
        }


def _values_equal(result: Any, expected: Any, float_tolerance: float = 1e-9) -> bool:
    """
    Compare two values for equality with float tolerance.

    Args:
        result: Actual result
        expected: Expected result
        float_tolerance: Tolerance for float comparison

    Returns:
        True if values are equal (within tolerance for floats)
    """
    # Handle None
    if result is None and expected is None:
        return True
    if result is None or expected is None:
        return False

    # Handle floats with tolerance
    if isinstance(result, float) and isinstance(expected, float):
        return math.isclose(result, expected, rel_tol=float_tolerance, abs_tol=float_tolerance)

    # Handle float vs int (e.g., 4.0 == 4)
    if isinstance(result, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(float(result), float(expected), rel_tol=float_tolerance, abs_tol=float_tolerance)

    # Handle lists/tuples (compare element by element)
    if isinstance(result, (list, tuple)) and isinstance(expected, (list, tuple)):
        if len(result) != len(expected):
            return False
        return all(_values_equal(r, e, float_tolerance) for r, e in zip(result, expected))

    # Default equality
    return result == expected


def validate_with_tests(code: str, func_name: str, tests: List[TestCase]) -> Dict[str, Any]:
    """
    Run all test cases and return validation results.

    Args:
        code: Python source code
        func_name: Function to test
        tests: List of TestCase objects

    Returns:
        Dict containing:
        - total: Total tests run
        - passed: Number of passed tests
        - failed: Number of failed tests
        - failures: List of failure details
        - errors: List of execution errors
    """
    results: Dict[str, Any] = {
        "total": len(tests),
        "passed": 0,
        "failed": 0,
        "failures": [],
        "errors": [],
    }

    for index, test in enumerate(tests, start=1):
        execution = safe_execute(code, func_name, test.input_args)

        if not execution["success"]:
            # Execution error (timeout, exception, etc.)
            results["errors"].append({
                "test_num": index,
                "description": test.description,
                "input": test.input_args,
                "error": execution["error"],
            })
            results["failed"] += 1
        else:
            # Check if result matches expected (with float tolerance)
            if _values_equal(execution["result"], test.expected):
                results["passed"] += 1
            else:
                results["failures"].append({
                    "test_num": index,
                    "description": test.description,
                    "input": test.input_args,
                    "expected": test.expected,
                    "got": execution["result"],
                })
                results["failed"] += 1

    logger.info(f"Test validation complete: {results['passed']}/{results['total']} passed")
    return results


def format_test_results(results: Dict[str, Any]) -> str:
    """Format test results as human-readable text."""
    lines: List[str] = []
    lines.append(f"Test Results: {results['passed']}/{results['total']} passed")

    if results["failures"]:
        lines.append("\nFailed Tests:")
        for failure in results["failures"]:
            lines.append(f"  • Test {failure['test_num']}: {failure['description']}")
            lines.append(f"    Input: {failure['input']}")
            lines.append(f"    Expected: {failure['expected']}")
            lines.append(f"    Got: {failure['got']}")

    if results["errors"]:
        lines.append("\nExecution Errors:")
        for error in results["errors"]:
            lines.append(f"  • Test {error['test_num']}: {error['description']}")
            lines.append(f"    Input: {error['input']}")
            lines.append(f"    Error: {error['error']}")

    return "\n".join(lines)
