"""Code Analysis Tools

AST-based static analysis tools for Python code review.
Provides function extraction, complexity calculation, and issue detection.
"""

import ast
from typing import List, Dict, Any, Optional
from app.workflows.code_review.complexity_analyzer import analyze_code_complexity


def extract_functions(code: str) -> List[Dict[str, Any]]:
    """
    Extract all function definitions from Python code.

    Args:
        code: Python source code

    Returns:
        List of dictionaries containing:
        - name: function name
        - lineno: line number
        - args: list of argument names
        - docstring: function docstring (if any)
        - body_lines: number of lines in function body
        - decorators: list of decorator names
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [{
            "error": f"Syntax error: {e}",
            "line": getattr(e, 'lineno', 0)
        }]

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Extract function info
            func_info = {
                "name": node.name,
                "lineno": node.lineno,
                "args": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node),
                "body_lines": len(node.body),
                "decorators": [
                    d.id for d in node.decorator_list
                    if isinstance(d, ast.Name)
                ]
            }
            functions.append(func_info)

    return functions


def calculate_cyclomatic_complexity(code: str) -> Dict[str, int]:
    """
    Calculate cyclomatic complexity for each function.

    Complexity = 1 + number of decision points (if, for, while, and, or, except)

    Args:
        code: Python source code

    Returns:
        Dictionary mapping function names to complexity scores
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}

    complexity_map = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            complexity = 1  # Base complexity

            # Count decision points
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    # Each 'and'/'or' adds complexity
                    complexity += len(child.values) - 1

            complexity_map[node.name] = complexity

    return complexity_map


def calculate_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """
    Calculate maximum nesting depth in AST node.

    Args:
        node: AST node to analyze
        current_depth: Current depth level

    Returns:
        Maximum nesting depth
    """
    max_depth = current_depth

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            child_depth = calculate_nesting_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = calculate_nesting_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)

    return max_depth


def detect_issues(code: str, functions: List[Dict]) -> List[Dict[str, Any]]:
    """
    Detect code quality issues using static analysis.

    Checks for:
    - Long functions (> 50 lines)
    - Missing docstrings
    - Deep nesting (> 4 levels)
    - Too many arguments (> 5)
    - Complex functions (complexity > 10)

    Args:
        code: Python source code
        functions: List of function metadata from extract_functions()

    Returns:
        List of issues with severity, type, message, function, and line number
    """
    issues = []

    # Parse code
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        issues.append({
            "severity": "error",
            "type": "syntax_error",
            "message": str(e),
            "line": getattr(e, 'lineno', 0),
            "function": None
        })
        return issues

    # Check for error entries in functions
    for func in functions:
        if "error" in func:
            continue

        # Check function length
        if func["body_lines"] > 50:
            issues.append({
                "severity": "warning",
                "type": "long_function",
                "function": func["name"],
                "line": func["lineno"],
                "message": f"Function '{func['name']}' is too long ({func['body_lines']} lines)"
            })

        # Check for docstring
        if not func["docstring"]:
            issues.append({
                "severity": "info",
                "type": "missing_docstring",
                "function": func["name"],
                "line": func["lineno"],
                "message": f"Function '{func['name']}' lacks docstring"
            })

        # Check argument count
        if len(func["args"]) > 5:
            issues.append({
                "severity": "warning",
                "type": "too_many_args",
                "function": func["name"],
                "line": func["lineno"],
                "message": f"Function '{func['name']}' has {len(func['args'])} arguments"
            })

    # Check nesting depth
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            max_depth = calculate_nesting_depth(node)
            if max_depth > 4:
                issues.append({
                    "severity": "warning",
                    "type": "deep_nesting",
                    "function": node.name,
                    "line": node.lineno,
                    "message": f"Function '{node.name}' has deep nesting (depth {max_depth})"
                })

    # Check complexity (requires recalculating)
    complexity_map = calculate_cyclomatic_complexity(code)
    for func_name, complexity in complexity_map.items():
        if complexity > 10:
            issues.append({
                "severity": "warning",
                "type": "high_complexity",
                "function": func_name,
                "line": next(
                    (f["lineno"] for f in functions if f.get("name") == func_name),
                    0
                ),
                "message": f"Function '{func_name}' has high complexity ({complexity})"
            })

    return issues


def generate_suggestions(issues: List[Dict], complexity: Dict[str, int]) -> List[str]:
    """
    Generate improvement suggestions based on detected issues.

    Args:
        issues: List of detected issues
        complexity: Complexity metrics by function

    Returns:
        List of actionable suggestion strings
    """
    suggestions = []

    # Group issues by type
    issue_types = {}
    for issue in issues:
        issue_type = issue["type"]
        if issue_type not in issue_types:
            issue_types[issue_type] = []
        issue_types[issue_type].append(issue)

    # Generate suggestions based on issue types
    if "long_function" in issue_types:
        funcs = [i["function"] for i in issue_types["long_function"]]
        suggestions.append(
            f"Break down long functions: {', '.join(funcs)}. "
            "Consider splitting into smaller, focused functions."
        )

    if "missing_docstring" in issue_types:
        count = len(issue_types["missing_docstring"])
        suggestions.append(
            f"Add docstrings to {count} function(s). "
            "Document parameters, return values, and purpose."
        )

    if "deep_nesting" in issue_types:
        funcs = [i["function"] for i in issue_types["deep_nesting"]]
        suggestions.append(
            f"Reduce nesting in: {', '.join(funcs)}. "
            "Consider early returns, guard clauses, or extracting methods."
        )

    if "too_many_args" in issue_types:
        funcs = [i["function"] for i in issue_types["too_many_args"]]
        suggestions.append(
            f"Reduce parameters in: {', '.join(funcs)}. "
            "Consider using dataclasses, **kwargs, or configuration objects."
        )

    if "high_complexity" in issue_types:
        funcs = [i["function"] for i in issue_types["high_complexity"]]
        suggestions.append(
            f"Simplify complex functions: {', '.join(funcs)}. "
            "Extract conditions, use lookup tables, or split logic."
        )

    # Complexity-based suggestions
    complex_funcs = [name for name, comp in complexity.items() if comp > 10]
    if complex_funcs and "high_complexity" not in issue_types:
        suggestions.append(
            f"High complexity in: {', '.join(complex_funcs)}. "
            "Simplify logic, extract conditions, or split into smaller functions."
        )

    return suggestions


def calculate_quality_score(issues: List[Dict], complexity: Dict[str, int]) -> float:
    """
    Calculate overall quality score (0-100).

    Scoring:
    - Start at 100
    - Deduct points for each issue based on severity
    - Deduct points for high complexity

    Args:
        issues: List of detected issues
        complexity: Complexity metrics by function

    Returns:
        Quality score from 0.0 to 100.0
    """
    score = 100.0

    # Deduct for issues
    severity_weights = {
        "error": 20,
        "warning": 5,
        "info": 2
    }

    for issue in issues:
        severity = issue.get("severity", "info")
        score -= severity_weights.get(severity, 2)

    # Deduct for complexity
    if complexity:
        avg_complexity = sum(complexity.values()) / len(complexity)
        if avg_complexity > 10:
            score -= (avg_complexity - 10) * 2

    # Clamp to 0-100
    return max(0.0, min(100.0, score))


def get_complexity_analysis(code: str) -> Dict[str, Dict]:
    """
    Get detailed complexity analysis for all functions.

    Args:
        code: Python source code

    Returns:
        Dictionary mapping function names to analysis with:
        - time_complexity: Big O notation for time
        - space_complexity: Big O notation for space
        - explanation: Human-readable explanation of approach
    """
    return analyze_code_complexity(code)
