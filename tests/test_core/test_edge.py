"""Tests for Edge and routing system"""

import pytest
from app.core.state import WorkflowState
from app.core.edge import (
    Edge,
    EdgeManager,
    ConditionalRouter,
    has_data_key,
    data_value_equals,
    data_value_greater_than,
    has_no_errors
)


@pytest.mark.asyncio
async def test_unconditional_edge():
    """Test edge without condition always traverses"""
    edge = Edge("node_a", "node_b")

    state = WorkflowState(workflow_id="test", run_id="run1")

    should_traverse = await edge.should_traverse(state)
    assert should_traverse is True


@pytest.mark.asyncio
async def test_conditional_edge_true():
    """Test conditional edge that should traverse"""

    def condition(state: WorkflowState) -> bool:
        return state.get_data("ready", False) is True

    edge = Edge("node_a", "node_b", condition=condition)

    state = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"ready": True}
    )

    should_traverse = await edge.should_traverse(state)
    assert should_traverse is True


@pytest.mark.asyncio
async def test_conditional_edge_false():
    """Test conditional edge that should not traverse"""

    def condition(state: WorkflowState) -> bool:
        return state.get_data("ready", False) is True

    edge = Edge("node_a", "node_b", condition=condition)

    state = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"ready": False}
    )

    should_traverse = await edge.should_traverse(state)
    assert should_traverse is False


@pytest.mark.asyncio
async def test_async_condition():
    """Test edge with async condition function"""

    async def async_condition(state: WorkflowState) -> bool:
        # Simulate async operation
        return state.get_data("value", 0) > 10

    edge = Edge("node_a", "node_b", condition=async_condition)

    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 15}
    )
    assert await edge.should_traverse(state1) is True

    state2 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 5}
    )
    assert await edge.should_traverse(state2) is False


@pytest.mark.asyncio
async def test_edge_traversal_count():
    """Test edge traversal counting"""
    edge = Edge("node_a", "node_b")

    state = WorkflowState(workflow_id="test", run_id="run1")

    assert edge.traversal_count == 0

    await edge.should_traverse(state)
    # Unconditional edges don't increment count
    # Only conditional edges that pass increment count


def test_edge_manager_add_edge():
    """Test adding edges to manager"""
    manager = EdgeManager()

    edge1 = manager.add_edge("node_a", "node_b")
    edge2 = manager.add_edge("node_b", "node_c")

    assert len(manager.get_all_edges()) == 2
    assert edge1.from_node == "node_a"
    assert edge2.to_node == "node_c"


def test_edge_manager_outgoing_edges():
    """Test getting outgoing edges"""
    manager = EdgeManager()

    manager.add_edge("node_a", "node_b")
    manager.add_edge("node_a", "node_c")
    manager.add_edge("node_b", "node_d")

    outgoing_a = manager.get_outgoing_edges("node_a")
    assert len(outgoing_a) == 2

    outgoing_b = manager.get_outgoing_edges("node_b")
    assert len(outgoing_b) == 1

    outgoing_c = manager.get_outgoing_edges("node_c")
    assert len(outgoing_c) == 0  # End node


@pytest.mark.asyncio
async def test_edge_manager_get_next_node():
    """Test determining next node"""
    manager = EdgeManager()

    # Simple linear path
    manager.add_edge("node_a", "node_b")

    state = WorkflowState(workflow_id="test", run_id="run1")

    next_node = await manager.get_next_node("node_a", state)
    assert next_node == "node_b"

    # End node returns None
    next_node = await manager.get_next_node("node_b", state)
    assert next_node is None


@pytest.mark.asyncio
async def test_edge_manager_conditional_routing():
    """Test conditional routing with multiple edges"""
    manager = EdgeManager()

    # Add conditional edges
    manager.add_edge(
        "start",
        "path_a",
        condition=lambda s: s.get_data("choice") == "a"
    )
    manager.add_edge(
        "start",
        "path_b",
        condition=lambda s: s.get_data("choice") == "b"
    )

    state_a = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"choice": "a"}
    )
    next_node = await manager.get_next_node("start", state_a)
    assert next_node == "path_a"

    state_b = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"choice": "b"}
    )
    next_node = await manager.get_next_node("start", state_b)
    assert next_node == "path_b"


@pytest.mark.asyncio
async def test_conditional_router():
    """Test ConditionalRouter"""
    router = ConditionalRouter("start")

    router.add_route(
        lambda s: s.get_data("value", 0) > 100,
        "high_value"
    )
    router.add_route(
        lambda s: s.get_data("value", 0) > 50,
        "medium_value"
    )
    router.set_default("low_value")

    # Test high value
    state_high = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 150}
    )
    next_node = await router.route(state_high)
    assert next_node == "high_value"

    # Test medium value
    state_med = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 75}
    )
    next_node = await router.route(state_med)
    assert next_node == "medium_value"

    # Test default
    state_low = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 25}
    )
    next_node = await router.route(state_low)
    assert next_node == "low_value"


@pytest.mark.asyncio
async def test_conditional_router_to_edges():
    """Test converting router to edges"""
    router = ConditionalRouter("start")

    router.add_route(lambda s: True, "node_a")
    router.add_route(lambda s: False, "node_b")
    router.set_default("node_c")

    edges = router.to_edges()

    assert len(edges) == 3
    assert all(e.from_node == "start" for e in edges)


def test_helper_conditions():
    """Test helper condition functions"""
    state = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"user_id": 123, "score": 85}
    )

    # has_data_key
    assert has_data_key("user_id")(state) is True
    assert has_data_key("missing")(state) is False

    # data_value_equals
    assert data_value_equals("user_id", 123)(state) is True
    assert data_value_equals("user_id", 999)(state) is False

    # data_value_greater_than
    assert data_value_greater_than("score", 80)(state) is True
    assert data_value_greater_than("score", 90)(state) is False

    # has_no_errors
    assert has_no_errors(state) is True

    state_with_error = state.add_error("Test error")
    assert has_no_errors(state_with_error) is False
