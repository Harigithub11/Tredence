"""
Phase 2 Success Criteria Test from PROJECT_PHASES.md

This is the exact test specified in Phase 2 success criteria.
"""

import asyncio
from datetime import datetime
from app.core.state import WorkflowState
from app.core.node import AsyncNode
from app.core.graph import Graph
from app.core.engine import WorkflowEngine


async def test_simple_workflow():
    """Test from PROJECT_PHASES.md Phase 2 success criteria"""
    # Define nodes
    async def node_a(state: WorkflowState) -> WorkflowState:
        state.data["count"] = 1
        return state

    async def node_b(state: WorkflowState) -> WorkflowState:
        state.data["count"] += 1
        return state

    # Build graph
    graph = Graph("test_workflow")
    graph.add_node("a", AsyncNode("a", node_a))
    graph.add_node("b", AsyncNode("b", node_b))
    graph.add_edge("a", "b")
    graph.set_entry_point("a")

    # Execute
    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run_1",
        timestamp=datetime.utcnow()
    )

    final_state = await engine.execute(graph, initial_state)

    # Validate
    assert final_state.data["count"] == 2, f"Expected count=2, got {final_state.data['count']}"
    assert len(engine.execution_log) >= 2, f"Expected at least 2 log entries, got {len(engine.execution_log)}"

    print("Core engine test passed")
    print(f"  - Final state count: {final_state.data['count']}")
    print(f"  - Execution log entries: {len(engine.execution_log)}")
    print(f"  - Iterations: {engine.current_iteration}")

    return True


if __name__ == "__main__":
    # Run test
    result = asyncio.run(test_simple_workflow())
    if result:
        print("\nPhase 2 Success Criteria: PASSED")
    else:
        print("\nPhase 2 Success Criteria: FAILED")
