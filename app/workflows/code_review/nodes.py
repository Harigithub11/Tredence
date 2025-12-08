"""Code Review Workflow Nodes

Nodes for the hybrid code review workflow.
Combines rule-based analysis with optional LLM enhancement.
"""

from app.core.state import WorkflowState
from app.core.registry import registry
from app.workflows.code_review.tools import (
    extract_functions,
    calculate_cyclomatic_complexity,
    detect_issues,
    generate_suggestions,
    calculate_quality_score
)
from app.llm import analyze_code


@registry.tool(name="extract_functions", description="Extract function definitions from code")
async def extract_functions_node(state: WorkflowState) -> WorkflowState:
    """
    Extract all functions from the provided code.

    Input state data:
    - code: Python source code string

    Output state data:
    - functions: List of function metadata
    - function_count: Number of functions found
    """
    code = state.data.get("code", "")

    if not code:
        state.errors.append("No code provided")
        return state

    # Extract functions
    functions = extract_functions(code)

    # Check for syntax errors
    if functions and "error" in functions[0]:
        state.errors.append(functions[0]["error"])
        state.data["functions"] = []
        state.data["function_count"] = 0
    else:
        state.data["functions"] = functions
        state.data["function_count"] = len(functions)

    return state


@registry.tool(name="calculate_complexity", description="Calculate cyclomatic complexity")
async def calculate_complexity_node(state: WorkflowState) -> WorkflowState:
    """
    Calculate complexity metrics for all functions.

    Input state data:
    - code: Python source code string

    Output state data:
    - complexity: Dictionary mapping function names to complexity scores
    - avg_complexity: Average complexity across all functions
    """
    code = state.data.get("code", "")

    # Calculate complexity
    complexity = calculate_cyclomatic_complexity(code)
    state.data["complexity"] = complexity

    # Calculate average
    if complexity:
        avg_complexity = sum(complexity.values()) / len(complexity)
        state.data["avg_complexity"] = round(avg_complexity, 2)
    else:
        state.data["avg_complexity"] = 0.0

    return state


@registry.tool(name="detect_issues", description="Detect code quality issues")
async def detect_issues_node(state: WorkflowState) -> WorkflowState:
    """
    Detect code quality issues using static analysis.

    Input state data:
    - code: Python source code string
    - functions: List of function metadata

    Output state data:
    - issues: List of detected issues
    - issue_count: Total number of issues
    - errors: Count of error-level issues
    - warnings: Count of warning-level issues
    - infos: Count of info-level issues
    """
    code = state.data.get("code", "")
    functions = state.data.get("functions", [])

    # Detect issues
    issues = detect_issues(code, functions)
    state.data["issues"] = issues
    state.data["issue_count"] = len(issues)

    # Categorize by severity
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    infos = [i for i in issues if i["severity"] == "info"]

    state.data["error_count"] = len(errors)
    state.data["warning_count"] = len(warnings)
    state.data["info_count"] = len(infos)

    return state


@registry.tool(name="suggest_improvements", description="Generate improvement suggestions")
async def suggest_improvements_node(state: WorkflowState) -> WorkflowState:
    """
    Generate improvement suggestions (hybrid: rules + LLM).

    Input state data:
    - code: Python source code string
    - issues: List of detected issues
    - complexity: Complexity metrics
    - use_llm: Whether to use LLM for analysis (default: False)

    Output state data:
    - rule_suggestions: List of rule-based suggestions
    - llm_suggestions: List of LLM-generated suggestions (if enabled)
    - llm_analysis: Raw LLM analysis text (if enabled)
    - suggestions: Combined list of all suggestions
    """
    code = state.data.get("code", "")
    issues = state.data.get("issues", [])
    complexity = state.data.get("complexity", {})
    use_llm = state.data.get("use_llm", False)

    # Rule-based suggestions (always run)
    rule_suggestions = generate_suggestions(issues, complexity)
    state.data["rule_suggestions"] = rule_suggestions

    # LLM suggestions (optional)
    if use_llm:
        llm_result = await analyze_code(code, issues, complexity)
        state.data["llm_suggestions"] = llm_result.get("llm_suggestions", [])
        state.data["llm_analysis"] = llm_result.get("raw_analysis", "")
        state.data["llm_critical_issues"] = llm_result.get("critical_issues", [])
        state.data["llm_quality_tips"] = llm_result.get("quality_tips", [])
        state.data["llm_best_practices"] = llm_result.get("best_practices", [])

        # Handle LLM errors
        if "error" in llm_result:
            state.warnings.append(f"LLM analysis error: {llm_result['error']}")

        # Combine suggestions
        all_suggestions = rule_suggestions + llm_result.get("llm_suggestions", [])
        state.data["suggestions"] = all_suggestions
    else:
        state.data["suggestions"] = rule_suggestions
        state.data["llm_suggestions"] = []

    return state


@registry.tool(name="check_quality", description="Calculate quality score and check loop condition")
async def check_quality_node(state: WorkflowState) -> WorkflowState:
    """
    Calculate quality score and determine if workflow should continue.

    Input state data:
    - issues: List of detected issues
    - complexity: Complexity metrics
    - quality_threshold: Minimum quality score (default: 70)

    Output state data:
    - quality_score: Overall quality score (0-100)
    - quality_pass: Whether code meets quality threshold
    """
    issues = state.data.get("issues", [])
    complexity = state.data.get("complexity", {})

    # Calculate quality score
    quality_score = calculate_quality_score(issues, complexity)
    state.data["quality_score"] = quality_score

    # Determine pass/fail
    threshold = state.data.get("quality_threshold", 70)
    state.data["quality_pass"] = quality_score >= threshold

    return state
