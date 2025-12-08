"""Tests for Node execution system"""

import pytest
from app.core.state import WorkflowState
from app.core.node import AsyncNode, SyncNode, LambdaNode


@pytest.mark.asyncio
async def test_async_node_execution():
    """Test async node execution"""

    async def increment_count(state: WorkflowState) -> WorkflowState:
        current = state.get_data("count", 0)
        return state.set_data("count", current + 1)

    node = AsyncNode("increment", increment_count, "Increments count")

    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"count": 0}
    )

    state2 = await node.execute(state1)

    assert state2.get_data("count") == 1
    assert node.execution_count == 1
    assert node.total_execution_time_ms >= 0  # May be 0 for very fast execution


@pytest.mark.asyncio
async def test_sync_node_execution():
    """Test sync node execution"""

    def double_value(state: WorkflowState) -> WorkflowState:
        value = state.get_data("value", 1)
        return state.set_data("value", value * 2)

    node = SyncNode("double", double_value, "Doubles value")

    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 5}
    )

    state2 = await node.execute(state1)

    assert state2.get_data("value") == 10
    assert node.execution_count == 1


@pytest.mark.asyncio
async def test_lambda_node():
    """Test lambda node creation"""

    node = LambdaNode(
        "add_ten",
        lambda state: state.set_data("result", state.get_data("value", 0) + 10)
    )

    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 5}
    )

    state2 = await node.execute(state1)

    assert state2.get_data("result") == 15


@pytest.mark.asyncio
async def test_node_error_handling():
    """Test node error handling"""

    async def failing_node(state: WorkflowState) -> WorkflowState:
        raise ValueError("Something went wrong")

    node = AsyncNode("failing", failing_node)

    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1"
    )

    state2 = await node.execute(state1)

    # Should capture error in state
    assert state2.has_errors()
    assert "failing" in state2.errors[0]
    assert "Something went wrong" in state2.errors[0]


@pytest.mark.asyncio
async def test_node_statistics():
    """Test node execution statistics"""

    async def simple_node(state: WorkflowState) -> WorkflowState:
        return state

    node = AsyncNode("test", simple_node)

    state = WorkflowState(workflow_id="test", run_id="run1")

    # Execute multiple times
    for i in range(5):
        state = await node.execute(state)

    assert node.execution_count == 5
    assert node.total_execution_time_ms >= 0

    stats = node.get_stats()
    assert stats["execution_count"] == 5
    assert stats["total_execution_time_ms"] >= 0
    assert stats["avg_execution_time_ms"] >= 0


@pytest.mark.asyncio
async def test_node_metadata():
    """Test node metadata"""

    async def test_func(state: WorkflowState) -> WorkflowState:
        return state

    node = AsyncNode(
        "test",
        test_func,
        description="Test node",
        version="1.0.0",
        author="Test"
    )

    assert node.name == "test"
    assert node.description == "Test node"
    assert node.metadata.get("version") == "1.0.0"
    assert node.metadata.get("author") == "Test"

    info = node.to_dict()
    assert info["name"] == "test"
    assert info["description"] == "Test node"
    assert info["metadata"]["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_node_state_preservation():
    """Test that node doesn't modify original state"""

    async def modify_state(state: WorkflowState) -> WorkflowState:
        return state.set_data("modified", True)

    node = AsyncNode("modify", modify_state)

    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"original": True}
    )

    state2 = await node.execute(state1)

    # Original state unchanged
    assert "modified" not in state1.data
    assert state1.get_data("original") is True

    # New state has changes
    assert state2.get_data("modified") is True
    assert state2.get_data("original") is True


@pytest.mark.asyncio
async def test_multiple_nodes_chaining():
    """Test chaining multiple nodes"""

    async def add_one(state: WorkflowState) -> WorkflowState:
        value = state.get_data("count", 0)
        return state.set_data("count", value + 1)

    async def multiply_two(state: WorkflowState) -> WorkflowState:
        value = state.get_data("count", 0)
        return state.set_data("count", value * 2)

    node1 = AsyncNode("add_one", add_one)
    node2 = AsyncNode("multiply_two", multiply_two)

    state = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"count": 5}
    )

    # Chain: 5 + 1 = 6, then 6 * 2 = 12
    state = await node1.execute(state)
    assert state.get_data("count") == 6

    state = await node2.execute(state)
    assert state.get_data("count") == 12
