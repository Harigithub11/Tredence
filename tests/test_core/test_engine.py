"""Tests for WorkflowEngine"""

import pytest
from app.core.state import WorkflowState
from app.core.node import AsyncNode
from app.core.graph import Graph
from app.core.engine import WorkflowEngine, run_workflow, run_workflow_with_stats
from app.utils.exceptions import (
    MaxIterationsExceeded,
    GraphValidationError,
    NodeExecutionError
)


@pytest.mark.asyncio
async def test_simple_two_node_workflow():
    """Test executing a simple two-node workflow (from PROJECT_PHASES.md)"""

    # Define nodes
    async def increment_count(state: WorkflowState) -> WorkflowState:
        count = state.get_data("count", 0)
        return state.set_data("count", count + 1)

    async def double_count(state: WorkflowState) -> WorkflowState:
        count = state.get_data("count", 0)
        return state.set_data("count", count * 2)

    # Build graph
    graph = Graph("simple-workflow")
    graph.add_node("increment", AsyncNode("increment", increment_count))
    graph.add_node("double", AsyncNode("double", double_count))
    graph.add_edge("increment", "double")
    graph.set_entry_point("increment")

    # Create engine and execute
    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1",
        data={"count": 0}
    )

    final_state = await engine.execute(graph, initial_state)

    # Validate results (from PROJECT_PHASES.md success criteria)
    assert final_state.get_data("count") == 2  # (0 + 1) * 2 = 2
    assert not final_state.has_errors()
    assert engine.current_iteration == 2


@pytest.mark.asyncio
async def test_engine_with_branching():
    """Test workflow with conditional branching"""

    async def check_value(state: WorkflowState) -> WorkflowState:
        return state  # Just pass through

    async def high_path(state: WorkflowState) -> WorkflowState:
        return state.set_data("path", "high")

    async def low_path(state: WorkflowState) -> WorkflowState:
        return state.set_data("path", "low")

    # Build graph with conditional routing
    graph = Graph("branching-workflow")
    graph.add_node("check", AsyncNode("check", check_value))
    graph.add_node("high", AsyncNode("high", high_path))
    graph.add_node("low", AsyncNode("low", low_path))

    # Conditional edges
    graph.add_edge(
        "check",
        "high",
        condition=lambda s: s.get_data("value", 0) > 50
    )
    graph.add_edge(
        "check",
        "low",
        condition=lambda s: s.get_data("value", 0) <= 50
    )
    graph.set_entry_point("check")

    engine = WorkflowEngine()

    # Test high path
    state_high = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 75}
    )
    final_high = await engine.execute(graph, state_high)
    assert final_high.get_data("path") == "high"

    # Test low path
    engine.clear_log()
    state_low = WorkflowState(
        workflow_id="test",
        run_id="run2",
        data={"value": 25}
    )
    final_low = await engine.execute(graph, state_low)
    assert final_low.get_data("path") == "low"


@pytest.mark.asyncio
async def test_engine_with_loop():
    """Test workflow with loop (max iterations)"""

    async def increment_and_loop(state: WorkflowState) -> WorkflowState:
        count = state.get_data("count", 0)
        return state.set_data("count", count + 1)

    # Create a proper loop with two nodes (no self-loops)
    graph = Graph("loop-workflow")
    graph.add_node("node_a", AsyncNode("node_a", increment_and_loop))
    graph.add_node("node_b", AsyncNode("node_b", increment_and_loop))
    graph.add_edge("node_a", "node_b")
    graph.add_edge(
        "node_b",
        "node_a",
        condition=lambda s: s.get_data("count", 0) < 5
    )
    graph.set_entry_point("node_a")

    engine = WorkflowEngine(max_iterations=20)
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"count": 0}
    )

    final_state = await engine.execute(graph, initial_state)

    # Should loop until count reaches 5 or higher
    # Each iteration increments by 1, so after 6 nodes execute: 0->1->2->3->4->5
    assert final_state.get_data("count") >= 5


@pytest.mark.asyncio
async def test_engine_max_iterations_exceeded():
    """Test that engine raises error when max iterations exceeded"""

    async def infinite_loop(state: WorkflowState) -> WorkflowState:
        return state

    graph = Graph("infinite-loop")
    graph.add_node("node_a", AsyncNode("node_a", infinite_loop))
    graph.add_node("node_b", AsyncNode("node_b", infinite_loop))
    graph.add_edge("node_a", "node_b")
    graph.add_edge("node_b", "node_a")  # Always loop back
    graph.set_entry_point("node_a")

    engine = WorkflowEngine(max_iterations=10)
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    with pytest.raises(MaxIterationsExceeded):
        await engine.execute(graph, initial_state)


@pytest.mark.asyncio
async def test_engine_node_execution_error():
    """Test engine handles node execution errors"""

    async def failing_node(state: WorkflowState) -> WorkflowState:
        raise ValueError("Node failed!")

    graph = Graph("error-workflow")
    graph.add_node("fail", AsyncNode("fail", failing_node))
    graph.set_entry_point("fail")

    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    # Node errors are captured in state, execution stops
    final_state = await engine.execute(graph, initial_state)
    assert final_state.has_errors()
    assert "Node 'fail' failed" in final_state.errors[0]


@pytest.mark.asyncio
async def test_engine_execution_log():
    """Test engine execution logging"""

    async def node_a(state: WorkflowState) -> WorkflowState:
        return state.set_data("a", True)

    async def node_b(state: WorkflowState) -> WorkflowState:
        return state.set_data("b", True)

    graph = Graph("log-test")
    graph.add_node("node_a", AsyncNode("node_a", node_a))
    graph.add_node("node_b", AsyncNode("node_b", node_b))
    graph.add_edge("node_a", "node_b")
    graph.set_entry_point("node_a")

    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    await engine.execute(graph, initial_state)

    log = engine.get_execution_log()

    # Should have entries for both nodes (started + completed = 4 entries)
    assert len(log) >= 2
    assert any(entry["node"] == "node_a" for entry in log)
    assert any(entry["node"] == "node_b" for entry in log)


@pytest.mark.asyncio
async def test_engine_execution_summary():
    """Test engine execution summary"""

    async def fast_node(state: WorkflowState) -> WorkflowState:
        return state

    graph = Graph("summary-test")
    graph.add_node("node_a", AsyncNode("node_a", fast_node))
    graph.add_node("node_b", AsyncNode("node_b", fast_node))
    graph.add_edge("node_a", "node_b")
    graph.set_entry_point("node_a")

    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    await engine.execute(graph, initial_state)

    summary = engine.get_execution_summary()

    assert summary["total_iterations"] == 2
    assert summary["nodes_executed"] == 2
    assert summary["nodes_failed"] == 0
    assert "node_a" in summary["completed_nodes"]
    assert "node_b" in summary["completed_nodes"]
    assert summary["total_execution_time_ms"] >= 0


@pytest.mark.asyncio
async def test_engine_invalid_graph():
    """Test engine rejects invalid graph"""

    graph = Graph("invalid-graph")
    # No nodes, no entry point

    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    with pytest.raises(GraphValidationError):
        await engine.execute(graph, initial_state)


@pytest.mark.asyncio
async def test_engine_stops_on_error():
    """Test engine stops execution when node adds error to state"""

    async def add_error(state: WorkflowState) -> WorkflowState:
        return state.add_error("Something went wrong")

    async def should_not_run(state: WorkflowState) -> WorkflowState:
        return state.set_data("should_not_be_set", True)

    graph = Graph("error-stop")
    graph.add_node("error_node", AsyncNode("error_node", add_error))
    graph.add_node("next_node", AsyncNode("next_node", should_not_run))
    graph.add_edge("error_node", "next_node")
    graph.set_entry_point("error_node")

    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    final_state = await engine.execute(graph, initial_state)

    # Should have error and not have executed next node
    assert final_state.has_errors()
    assert "should_not_be_set" not in final_state.data


@pytest.mark.asyncio
async def test_run_workflow_helper():
    """Test run_workflow convenience function"""

    async def simple_node(state: WorkflowState) -> WorkflowState:
        return state.set_data("executed", True)

    graph = Graph("helper-test")
    graph.add_node("node", AsyncNode("node", simple_node))
    graph.set_entry_point("node")

    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    final_state, log = await run_workflow(graph, initial_state)

    assert final_state.get_data("executed") is True
    assert len(log) > 0


@pytest.mark.asyncio
async def test_run_workflow_with_stats_helper():
    """Test run_workflow_with_stats convenience function"""

    async def simple_node(state: WorkflowState) -> WorkflowState:
        return state.set_data("executed", True)

    graph = Graph("stats-test")
    graph.add_node("node", AsyncNode("node", simple_node))
    graph.set_entry_point("node")

    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    result = await run_workflow_with_stats(graph, initial_state)

    assert result["success"] is True
    assert result["error"] is None
    assert result["final_state"]["data"]["executed"] is True
    assert "execution_log" in result
    assert "summary" in result


@pytest.mark.asyncio
async def test_engine_timeout():
    """Test engine timeout functionality with multiple nodes"""
    import asyncio

    async def fast_node(state: WorkflowState) -> WorkflowState:
        await asyncio.sleep(0.05)  # 50ms
        return state

    # Create a workflow with multiple fast nodes that together exceed timeout
    graph = Graph("timeout-test")
    graph.add_node("node1", AsyncNode("node1", fast_node))
    graph.add_node("node2", AsyncNode("node2", fast_node))
    graph.add_node("node3", AsyncNode("node3", fast_node))
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node3")
    graph.set_entry_point("node1")

    engine = WorkflowEngine(timeout=0.1)  # 100ms timeout, but nodes take 150ms total
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    # The timeout should trigger a WorkflowException between nodes
    from app.utils.exceptions import WorkflowException
    with pytest.raises(WorkflowException, match="timeout"):
        await engine.execute(graph, initial_state)


@pytest.mark.asyncio
async def test_engine_clear_log():
    """Test clearing execution log"""

    async def simple_node(state: WorkflowState) -> WorkflowState:
        return state

    graph = Graph("clear-test")
    graph.add_node("node", AsyncNode("node", simple_node))
    graph.set_entry_point("node")

    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    await engine.execute(graph, initial_state)
    assert len(engine.get_execution_log()) > 0

    engine.clear_log()
    assert len(engine.get_execution_log()) == 0
    assert engine.current_iteration == 0
