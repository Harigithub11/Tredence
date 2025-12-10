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
    calculate_quality_score,
    get_complexity_analysis
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
    - complexity_analysis: Detailed Big-O analysis per function
    """
    code = state.data.get("code", "")

    # Calculate cyclomatic complexity
    complexity = calculate_cyclomatic_complexity(code)
    state.data["complexity"] = complexity

    # Calculate average
    if complexity:
        avg_complexity = sum(complexity.values()) / len(complexity)
        state.data["avg_complexity"] = round(avg_complexity, 2)
    else:
        state.data["avg_complexity"] = 0.0

    # Get detailed Big-O complexity analysis
    complexity_analysis = get_complexity_analysis(code)
    state.data["complexity_analysis"] = complexity_analysis

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

    print(f"\n{'='*70}")
    print(f"SUGGEST NODE: use_llm = {use_llm} (type: {type(use_llm)})")
    print(f"State data keys: {list(state.data.keys())}")
    print(f"{'='*70}\n")

    # Rule-based suggestions (always run)
    rule_suggestions = generate_suggestions(issues, complexity)
    state.data["rule_suggestions"] = rule_suggestions

    # LLM suggestions and code improvements (optional)
    if use_llm:
        print("ENTERING LLM BLOCK - calling code improver")
        llm_result = await analyze_code(code, issues, complexity)
        state.data["llm_suggestions"] = llm_result.get("llm_suggestions", [])
        state.data["llm_analysis"] = llm_result.get("raw_analysis", "")
        state.data["llm_critical_issues"] = llm_result.get("critical_issues", [])
        state.data["llm_quality_tips"] = llm_result.get("quality_tips", [])
        state.data["llm_best_practices"] = llm_result.get("best_practices", [])

        # Run test validation (Option 2)
        functions = state.data.get("functions", [])
        if functions:
            from app.workflows.code_review.test_validator import (
                generate_test_cases,
                validate_with_tests,
                format_test_results
            )

            try:
                func_info = functions[0]
                func_name = func_info.get('name', '')

                # Generate test cases (hybrid: pattern + LLM fallback)
                test_cases = await generate_test_cases(func_name, code, func_info, use_llm=use_llm)

                if test_cases:
                    # Run tests
                    test_results = validate_with_tests(code, func_name, test_cases)
                    state.data["test_results"] = test_results
                    state.data["test_summary"] = format_test_results(test_results)

                    # Add critical issues for test failures
                    if test_results['failed'] > 0:
                        for failure in test_results.get('failures', []):
                            issues.append({
                                "type": "logic_error",
                                "severity": "critical",
                                "line": 1,
                                "description": f"Test '{failure['description']}' failed: input {failure['input']} returned {failure['got']}, expected {failure['expected']}"
                            })

                        for error in test_results.get('errors', []):
                            issues.append({
                                "type": "execution_error",
                                "severity": "critical",
                                "line": 1,
                                "description": f"Test '{error['description']}' error: {error['error']}"
                            })

                        # Update issue count
                        state.data["issues"] = issues
                        state.data["issue_count"] = len(issues)
                        state.data["error_count"] = len([i for i in issues if i["severity"] == "error" or i["severity"] == "critical"])
                else:
                    # No tests generated (no pattern match and LLM disabled/failed)
                    logger.info(f"No test cases generated for '{func_name}', skipping test validation")
                    state.data["test_results"] = None

            except Exception as e:
                state.warnings.append(f"Test validation error: {str(e)}")

        # Generate improved code using LLM
        from app.workflows.code_review.code_improver import generate_improved_code
        try:
            improvement_data = await generate_improved_code(
                code,
                state.data,
                use_llm=True
            )
            state.data["improved_code"] = improvement_data.get("improved_code")
            state.data["algorithm_name"] = improvement_data.get("algorithm_name")
            state.data["improvements_applied"] = improvement_data.get("improvements_applied", [])
            state.data["alternative_solutions"] = improvement_data.get("alternatives", [])

            # Extract logic check results if available
            logic_check = state.data.get("logic_check", {})
            if logic_check:
                state.data["logic_errors"] = logic_check.get("logic_errors", [])
                state.data["edge_case_failures"] = logic_check.get("edge_case_failures", [])
                state.data["is_logically_correct"] = logic_check.get("is_correct", True)
        except Exception as e:
            state.warnings.append(f"Code improvement generation error: {str(e)}")
            state.data["improved_code"] = None
            state.data["alternative_solutions"] = []

        # Handle LLM errors
        if "error" in llm_result:
            state.warnings.append(f"LLM analysis error: {llm_result['error']}")

        # Combine suggestions
        all_suggestions = rule_suggestions + llm_result.get("llm_suggestions", [])
        state.data["suggestions"] = all_suggestions
    else:
        state.data["suggestions"] = rule_suggestions
        state.data["llm_suggestions"] = []

        # Generate basic AST-based improvements when LLM is disabled
        from app.workflows.code_review.code_improver import _generate_generic_improvement
        try:
            improvement_data = _generate_generic_improvement(code, state.data)
            state.data["improved_code"] = improvement_data.get("improved_code")
            state.data["algorithm_name"] = improvement_data.get("algorithm_name")
            state.data["improvements_applied"] = improvement_data.get("improvements_applied", [])
            state.data["alternative_solutions"] = []
        except Exception as e:
            state.warnings.append(f"AST-based improvement generation error: {str(e)}")
            state.data["improved_code"] = None
            state.data["alternative_solutions"] = []

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
