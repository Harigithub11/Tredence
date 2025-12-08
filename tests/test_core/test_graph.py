"""Tests for Graph definition and validation"""

import pytest
from app.core.state import WorkflowState
from app.core.node import AsyncNode
from app.core.graph import Graph, GraphBuilder, create_simple_graph


async def simple_func(state: WorkflowState) -> WorkflowState:
    """Simple test function"""
    return state


def test_graph_creation():
    """Test creating a basic graph"""
    graph = Graph("test-graph", "Test graph description")

    assert graph.name == "test-graph"
    assert graph.description == "Test graph description"
    assert len(graph.nodes) == 0
    assert graph.entry_point is None


def test_graph_add_node():
    """Test adding nodes to graph"""
    graph = Graph("test-graph")
    node = AsyncNode("node_a", simple_func)

    graph.add_node("node_a", node)

    assert graph.has_node("node_a")
    assert len(graph.nodes) == 1
    assert graph.get_node("node_a") == node


def test_graph_duplicate_node_error():
    """Test adding duplicate node raises error"""
    graph = Graph("test-graph")
    node = AsyncNode("node_a", simple_func)

    graph.add_node("node_a", node)

    with pytest.raises(ValueError, match="already exists"):
        graph.add_node("node_a", node)


def test_graph_add_edge():
    """Test adding edges"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_edge("node_a", "node_b")

    edges = graph.edge_manager.get_all_edges()
    assert len(edges) == 1
    assert edges[0].from_node == "node_a"
    assert edges[0].to_node == "node_b"


def test_graph_edge_invalid_node():
    """Test adding edge with non-existent node"""
    graph = Graph("test-graph")
    node_a = AsyncNode("node_a", simple_func)
    graph.add_node("node_a", node_a)

    with pytest.raises(ValueError, match="not found"):
        graph.add_edge("node_a", "non_existent")


def test_graph_set_entry_point():
    """Test setting entry point"""
    graph = Graph("test-graph")
    node = AsyncNode("start", simple_func)

    graph.add_node("start", node)
    graph.set_entry_point("start")

    assert graph.entry_point == "start"


def test_graph_entry_point_invalid():
    """Test setting invalid entry point"""
    graph = Graph("test-graph")

    with pytest.raises(ValueError, match="not found"):
        graph.set_entry_point("non_existent")


def test_graph_validation_no_entry_point():
    """Test validation fails without entry point"""
    graph = Graph("test-graph")
    node = AsyncNode("node_a", simple_func)
    graph.add_node("node_a", node)

    with pytest.raises(ValueError, match="Entry point not set"):
        graph.validate()


def test_graph_validation_success():
    """Test successful graph validation"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_edge("node_a", "node_b")
    graph.set_entry_point("node_a")

    # Should not raise
    assert graph.validate() is True


def test_graph_validation_unreachable_nodes():
    """Test validation fails with unreachable nodes"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)
    node_c = AsyncNode("node_c", simple_func)

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_node("node_c", node_c)  # Unreachable

    graph.add_edge("node_a", "node_b")
    graph.set_entry_point("node_a")

    with pytest.raises(ValueError, match="Unreachable nodes"):
        graph.validate()


def test_graph_validation_self_loop():
    """Test validation fails with self-loop"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func)
    graph.add_node("node_a", node_a)
    graph.add_edge("node_a", "node_a")  # Self-loop
    graph.set_entry_point("node_a")

    with pytest.raises(ValueError, match="Self-loop"):
        graph.validate()


def test_graph_find_cycles():
    """Test cycle detection"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)
    node_c = AsyncNode("node_c", simple_func)

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_node("node_c", node_c)

    # Create cycle: a -> b -> c -> a
    graph.add_edge("node_a", "node_b")
    graph.add_edge("node_b", "node_c")
    graph.add_edge("node_c", "node_a")

    cycles = graph.find_cycles()
    assert len(cycles) > 0


def test_graph_get_end_nodes():
    """Test finding end nodes"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)
    node_c = AsyncNode("node_c", simple_func)

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_node("node_c", node_c)

    graph.add_edge("node_a", "node_b")
    graph.add_edge("node_a", "node_c")

    end_nodes = graph.get_end_nodes()
    assert set(end_nodes) == {"node_b", "node_c"}


def test_graph_to_dict():
    """Test graph serialization"""
    graph = Graph("test-graph", "Test description")

    node_a = AsyncNode("node_a", simple_func, "Node A")
    node_b = AsyncNode("node_b", simple_func, "Node B")

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_edge("node_a", "node_b")
    graph.set_entry_point("node_a")

    graph_dict = graph.to_dict()

    assert graph_dict["name"] == "test-graph"
    assert graph_dict["description"] == "Test description"
    assert graph_dict["entry_point"] == "node_a"
    assert len(graph_dict["nodes"]) == 2
    assert len(graph_dict["edges"]) == 1


def test_graph_stats():
    """Test graph statistics"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_edge("node_a", "node_b")
    graph.set_entry_point("node_a")

    stats = graph.get_stats()

    assert stats["name"] == "test-graph"
    assert stats["node_count"] == 2
    assert stats["edge_count"] == 1
    assert stats["entry_point"] == "node_a"
    assert "node_b" in stats["end_nodes"]


def test_graph_builder():
    """Test fluent GraphBuilder API"""
    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)

    graph = (
        GraphBuilder("test-graph", "Builder test")
        .node("node_a", node_a)
        .node("node_b", node_b)
        .edge("node_a", "node_b")
        .entry("node_a")
        .metadata("version", "1.0")
        .build()
    )

    assert graph.name == "test-graph"
    assert graph.entry_point == "node_a"
    assert len(graph.nodes) == 2
    assert graph.metadata["version"] == "1.0"


def test_graph_builder_invalid():
    """Test GraphBuilder validation"""
    node_a = AsyncNode("node_a", simple_func)

    builder = (
        GraphBuilder("test-graph")
        .node("node_a", node_a)
        # Missing entry point
    )

    with pytest.raises(ValueError):
        builder.build()


def test_create_simple_graph_helper():
    """Test create_simple_graph helper"""
    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)

    graph = create_simple_graph(
        name="test-graph",
        nodes=[("node_a", node_a), ("node_b", node_b)],
        edges=[("node_a", "node_b")],
        entry_point="node_a"
    )

    assert graph.entry_point == "node_a"
    assert len(graph.nodes) == 2
    assert len(graph.edge_manager.get_all_edges()) == 1


def test_graph_method_chaining():
    """Test method chaining in Graph"""
    node_a = AsyncNode("node_a", simple_func)
    node_b = AsyncNode("node_b", simple_func)

    graph = (
        Graph("test-graph")
        .add_node("node_a", node_a)
        .add_node("node_b", node_b)
        .add_edge("node_a", "node_b")
        .set_entry_point("node_a")
    )

    assert isinstance(graph, Graph)
    assert graph.validate() is True


def test_graph_visualize_text():
    """Test text visualization"""
    graph = Graph("test-graph")

    node_a = AsyncNode("node_a", simple_func, "First node")
    node_b = AsyncNode("node_b", simple_func, "Second node")

    graph.add_node("node_a", node_a)
    graph.add_node("node_b", node_b)
    graph.add_edge("node_a", "node_b")
    graph.set_entry_point("node_a")

    text = graph.visualize_text()

    assert "test-graph" in text
    assert "node_a" in text
    assert "node_b" in text
    assert "→" in text  # Entry point marker
