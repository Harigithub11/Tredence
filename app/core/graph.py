"""Workflow Graph Definition

A graph represents the structure of a workflow - nodes and their connections.
Supports validation, serialization, and visualization.
"""

from typing import Dict, List, Optional, Set, Any
import json

from app.core.node import Node
from app.core.edge import Edge, EdgeManager
from app.core.state import WorkflowState


class Graph:
    """
    Workflow graph definition.

    A graph consists of nodes (executable units) and edges (connections).
    Provides methods for building, validating, and executing workflows.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Create a new workflow graph.

        Args:
            name: Unique graph name
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self.nodes: Dict[str, Node] = {}
        self.edge_manager = EdgeManager()
        self.entry_point: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def add_node(self, name: str, node: Node) -> "Graph":
        """
        Add a node to the graph.

        Args:
            name: Unique node name (used for edges)
            node: Node instance

        Returns:
            Self for method chaining

        Raises:
            ValueError: If node name already exists
        """
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists in graph")

        self.nodes[name] = node
        return self

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[callable] = None,
        description: str = ""
    ) -> "Graph":
        """
        Add an edge between two nodes.

        Args:
            from_node: Source node name
            to_node: Destination node name
            condition: Optional condition function
            description: Edge description

        Returns:
            Self for method chaining

        Raises:
            ValueError: If either node doesn't exist
        """
        # Validate nodes exist
        if from_node not in self.nodes:
            raise ValueError(f"Source node '{from_node}' not found in graph")
        if to_node not in self.nodes:
            raise ValueError(f"Destination node '{to_node}' not found in graph")

        # Add edge
        self.edge_manager.add_edge(from_node, to_node, condition, description)
        return self

    def set_entry_point(self, node_name: str) -> "Graph":
        """
        Set the starting node for the workflow.

        Args:
            node_name: Name of the entry node

        Returns:
            Self for method chaining

        Raises:
            ValueError: If node doesn't exist
        """
        if node_name not in self.nodes:
            raise ValueError(f"Entry point node '{node_name}' not found in graph")

        self.entry_point = node_name
        return self

    def get_node(self, name: str) -> Optional[Node]:
        """
        Get a node by name.

        Args:
            name: Node name

        Returns:
            Node instance or None if not found
        """
        return self.nodes.get(name)

    def has_node(self, name: str) -> bool:
        """Check if graph has a node"""
        return name in self.nodes

    def get_node_names(self) -> List[str]:
        """Get list of all node names"""
        return list(self.nodes.keys())

    def validate(self) -> bool:
        """
        Validate the graph structure.

        Checks:
        - Entry point is set
        - Entry point exists
        - All nodes are reachable from entry point
        - No orphaned nodes (except potential end nodes)
        - No self-loops in edges

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails with detailed error message
        """
        # Check entry point is set
        if not self.entry_point:
            raise ValueError("Entry point not set")

        # Check entry point exists
        if self.entry_point not in self.nodes:
            raise ValueError(f"Entry point '{self.entry_point}' not in nodes")

        # Check for empty graph
        if not self.nodes:
            raise ValueError("Graph has no nodes")

        # Find reachable nodes from entry point
        reachable = self._find_reachable_nodes()

        # Check all nodes are reachable
        unreachable = set(self.nodes.keys()) - reachable
        if unreachable:
            raise ValueError(
                f"Unreachable nodes from entry point: {', '.join(unreachable)}"
            )

        # Check for self-loops
        for edge in self.edge_manager.get_all_edges():
            if edge.from_node == edge.to_node:
                raise ValueError(f"Self-loop detected on node '{edge.from_node}'")

        return True

    def _find_reachable_nodes(self) -> Set[str]:
        """
        Find all nodes reachable from the entry point.

        Uses DFS to traverse the graph.

        Returns:
            Set of reachable node names
        """
        if not self.entry_point:
            return set()

        reachable = set()
        stack = [self.entry_point]

        while stack:
            current = stack.pop()

            if current in reachable:
                continue

            reachable.add(current)

            # Add all outgoing nodes
            for edge in self.edge_manager.get_outgoing_edges(current):
                if edge.to_node not in reachable:
                    stack.append(edge.to_node)

        return reachable

    def find_cycles(self) -> List[List[str]]:
        """
        Find cycles in the graph.

        Returns:
            List of cycles (each cycle is a list of node names)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check all outgoing edges
            for edge in self.edge_manager.get_outgoing_edges(node):
                next_node = edge.to_node

                if next_node not in visited:
                    dfs(next_node, path.copy())
                elif next_node in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(next_node)
                    cycle = path[cycle_start:] + [next_node]
                    cycles.append(cycle)

            rec_stack.remove(node)

        # Start DFS from each node
        for node_name in self.nodes:
            if node_name not in visited:
                dfs(node_name, [])

        return cycles

    def get_end_nodes(self) -> List[str]:
        """
        Get nodes with no outgoing edges (end nodes).

        Returns:
            List of end node names
        """
        end_nodes = []
        for node_name in self.nodes:
            if not self.edge_manager.has_outgoing_edges(node_name):
                end_nodes.append(node_name)
        return end_nodes

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert graph to dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "name": self.name,
            "description": self.description,
            "entry_point": self.entry_point,
            "nodes": [
                {
                    "name": name,
                    "description": node.description,
                    "metadata": node.metadata
                }
                for name, node in self.nodes.items()
            ],
            "edges": [
                edge.to_dict()
                for edge in self.edge_manager.get_all_edges()
            ],
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """
        Convert graph to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.

        Returns:
            Dictionary with graph statistics
        """
        cycles = self.find_cycles()

        return {
            "name": self.name,
            "node_count": len(self.nodes),
            "edge_count": len(self.edge_manager.get_all_edges()),
            "entry_point": self.entry_point,
            "end_nodes": self.get_end_nodes(),
            "has_cycles": len(cycles) > 0,
            "cycle_count": len(cycles),
            "node_names": list(self.nodes.keys())
        }

    def visualize_text(self) -> str:
        """
        Create a simple text visualization of the graph.

        Returns:
            Multi-line string showing graph structure
        """
        lines = []
        lines.append(f"Graph: {self.name}")
        lines.append(f"Entry Point: {self.entry_point}")
        lines.append(f"Nodes: {len(self.nodes)}")
        lines.append("")

        # List nodes
        lines.append("Nodes:")
        for name, node in self.nodes.items():
            marker = "→" if name == self.entry_point else " "
            lines.append(f"  {marker} {name}: {node.description[:50]}")

        lines.append("")

        # List edges
        lines.append("Edges:")
        for edge in self.edge_manager.get_all_edges():
            condition_str = " (conditional)" if edge.condition else ""
            lines.append(f"  {edge.from_node} → {edge.to_node}{condition_str}")

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation"""
        return f"Graph(name={self.name}, nodes={len(self.nodes)}, edges={len(self.edge_manager.get_all_edges())})"

    def __repr__(self) -> str:
        """Detailed representation"""
        return self.__str__()


class GraphBuilder:
    """
    Fluent builder for creating graphs.

    Provides a convenient API for constructing workflows.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize graph builder.

        Args:
            name: Graph name
            description: Graph description
        """
        self.graph = Graph(name, description)

    def node(self, name: str, node: Node) -> "GraphBuilder":
        """Add a node (fluent API)"""
        self.graph.add_node(name, node)
        return self

    def edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[callable] = None
    ) -> "GraphBuilder":
        """Add an edge (fluent API)"""
        self.graph.add_edge(from_node, to_node, condition)
        return self

    def entry(self, node_name: str) -> "GraphBuilder":
        """Set entry point (fluent API)"""
        self.graph.set_entry_point(node_name)
        return self

    def metadata(self, key: str, value: Any) -> "GraphBuilder":
        """Add metadata (fluent API)"""
        self.graph.metadata[key] = value
        return self

    def build(self) -> Graph:
        """
        Build and validate the graph.

        Returns:
            The constructed Graph

        Raises:
            ValueError: If graph validation fails
        """
        self.graph.validate()
        return self.graph

    def build_unsafe(self) -> Graph:
        """
        Build the graph without validation.

        Returns:
            The constructed Graph (may be invalid)
        """
        return self.graph


# Example usage helper
def create_simple_graph(
    name: str,
    nodes: List[tuple[str, Node]],
    edges: List[tuple[str, str]],
    entry_point: str
) -> Graph:
    """
    Create a simple linear graph.

    Args:
        name: Graph name
        nodes: List of (name, node) tuples
        edges: List of (from, to) tuples
        entry_point: Entry node name

    Returns:
        Constructed and validated Graph

    Example:
        >>> from app.core.node import AsyncNode
        >>> async def node_a(state): return state
        >>> async def node_b(state): return state
        >>> graph = create_simple_graph(
        ...     "my_workflow",
        ...     [("a", AsyncNode("a", node_a)), ("b", AsyncNode("b", node_b))],
        ...     [("a", "b")],
        ...     "a"
        ... )
    """
    graph = Graph(name)

    # Add nodes
    for node_name, node in nodes:
        graph.add_node(node_name, node)

    # Add edges
    for from_node, to_node in edges:
        graph.add_edge(from_node, to_node)

    # Set entry point
    graph.set_entry_point(entry_point)

    # Validate
    graph.validate()

    return graph
