"""Code Review Workflow Definition

Defines the hybrid code review workflow graph with conditional routing.
"""

from datetime import datetime
import uuid

from app.core.graph import GraphBuilder
from app.core.node import LambdaNode
from app.core.state import WorkflowState
from app.core.engine import WorkflowEngine
from app.workflows.code_review.nodes import (
    extract_functions_node,
    calculate_complexity_node,
    detect_issues_node,
    suggest_improvements_node,
    check_quality_node
)


def create_code_review_workflow() -> GraphBuilder:
    """
    Create Code Review workflow graph.

    Workflow:
    1. Extract functions from code
    2. Calculate cyclomatic complexity
    3. Detect code quality issues
    4. Suggest improvements (hybrid: rules + optional LLM)
    5. Check quality score
    6. Loop back to suggest if quality fails (max 3 iterations)

    Returns:
        Built workflow graph ready for execution
    """
    builder = GraphBuilder(name="code_review")

    # Register nodes
    builder.node("extract", LambdaNode("extract", transform=extract_functions_node))
    builder.node("complexity", LambdaNode("complexity", transform=calculate_complexity_node))
    builder.node("detect", LambdaNode("detect", transform=detect_issues_node))
    builder.node("suggest", LambdaNode("suggest", transform=suggest_improvements_node))
    builder.node("check", LambdaNode("check", transform=check_quality_node))

    # Define linear edges
    builder.edge("extract", "complexity")
    builder.edge("complexity", "detect")
    builder.edge("detect", "suggest")
    builder.edge("suggest", "check")

    # Conditional edge: loop if quality fails and iteration < 3
    def should_loop(state: WorkflowState) -> bool:
        """Check if we should loop for another iteration"""
        quality_pass = state.data.get("quality_pass", False)
        iteration = state.iteration
        max_iterations = 3

        # Loop if quality failed and haven't exceeded max iterations
        return not quality_pass and iteration < max_iterations

    # Add conditional routing from check node back to suggest
    builder.edge("check", "suggest", condition=should_loop)

    # Set entry point
    builder.entry("extract")

    return builder.build()


async def run_code_review(
    code: str,
    use_llm: bool = False,
    quality_threshold: float = 70.0
) -> WorkflowState:
    """
    Helper function to run code review workflow.

    Args:
        code: Python code to review
        use_llm: Whether to use LLM for enhanced analysis
        quality_threshold: Minimum quality score (0-100)

    Returns:
        Final workflow state with analysis results

    Usage:
        >>> code = '''
        ... def hello(name):
        ...     print(f"Hello {name}")
        ... '''
        >>> result = await run_code_review(code)
        >>> print(result.data["quality_score"])
        85.0
    """
    # Create workflow graph
    graph = create_code_review_workflow()

    # Create initial state
    initial_state = WorkflowState(
        workflow_id="code_review",
        run_id=f"review_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.utcnow(),
        data={
            "code": code,
            "use_llm": use_llm,
            "quality_threshold": quality_threshold
        }
    )

    # Execute workflow
    engine = WorkflowEngine()
    final_state = await engine.execute(graph, initial_state)

    return final_state
