"""Workflow Edge and Routing System

Edges define connections between nodes and how state flows through the workflow.
Supports simple edges, conditional edges, and dynamic routing.
"""

from typing import Callable, Optional, List, Dict, Any
import asyncio

from app.core.state import WorkflowState


class Edge:
    """
    Edge connecting two nodes in a workflow.

    An edge can be simple (always traverse) or conditional (traverse based on state).
    """

    def __init__(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable[[WorkflowState], bool]] = None,
        description: str = ""
    ):
        """
        Create an edge between two nodes.

        Args:
            from_node: Source node name
            to_node: Destination node name
            condition: Optional condition function (returns True to traverse)
            description: Human-readable description
        """
        self.from_node = from_node
        self.to_node = to_node
        self.condition = condition
        self.description = description
        self.traversal_count = 0

    async def should_traverse(self, state: WorkflowState) -> bool:
        """
        Check if this edge should be traversed given the current state.

        Args:
            state: Current workflow state

        Returns:
            True if edge should be traversed, False otherwise
        """
        # No condition means always traverse
        if self.condition is None:
            return True

        try:
            # Execute condition (sync or async)
            if asyncio.iscoroutinefunction(self.condition):
                result = await self.condition(state)
            else:
                result = self.condition(state)

            # Increment traversal count if condition passes
            if result:
                self.traversal_count += 1

            return bool(result)

        except Exception as e:
            # If condition fails, log warning and don't traverse
            print(f"Warning: Edge condition failed: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary"""
        return {
            "from": self.from_node,
            "to": self.to_node,
            "has_condition": self.condition is not None,
            "description": self.description,
            "traversal_count": self.traversal_count
        }

    def __str__(self) -> str:
        condition_str = " (conditional)" if self.condition else ""
        return f"{self.from_node} -> {self.to_node}{condition_str}"

    def __repr__(self) -> str:
        return f"Edge({self.from_node} -> {self.to_node})"


class ConditionalRouter:
    """
    Router that selects the next node based on state conditions.

    This is useful for complex branching logic where multiple conditions
    need to be evaluated in order.
    """

    def __init__(self, from_node: str):
        """
        Create a conditional router.

        Args:
            from_node: Source node name
        """
        self.from_node = from_node
        self.routes: List[tuple[Callable[[WorkflowState], bool], str]] = []
        self.default_route: Optional[str] = None

    def add_route(
        self,
        condition: Callable[[WorkflowState], bool],
        to_node: str
    ) -> "ConditionalRouter":
        """
        Add a conditional route.

        Routes are evaluated in the order they are added.

        Args:
            condition: Function that returns True if this route should be taken
            to_node: Destination node if condition is True

        Returns:
            Self for chaining
        """
        self.routes.append((condition, to_node))
        return self

    def set_default(self, to_node: str) -> "ConditionalRouter":
        """
        Set default route if no conditions match.

        Args:
            to_node: Default destination node

        Returns:
            Self for chaining
        """
        self.default_route = to_node
        return self

    async def route(self, state: WorkflowState) -> Optional[str]:
        """
        Determine the next node based on state.

        Args:
            state: Current workflow state

        Returns:
            Name of next node, or None if no route matches

        Raises:
            RuntimeError: If no route matches and no default is set
        """
        # Evaluate each condition in order
        for condition, to_node in self.routes:
            try:
                # Execute condition (sync or async)
                if asyncio.iscoroutinefunction(condition):
                    result = await condition(state)
                else:
                    result = condition(state)

                if result:
                    return to_node

            except Exception as e:
                print(f"Warning: Route condition failed: {e}")
                continue

        # Return default if set
        if self.default_route:
            return self.default_route

        # No matching route
        raise RuntimeError(
            f"No matching route from node '{self.from_node}' "
            f"and no default route set"
        )

    def to_edges(self) -> List[Edge]:
        """
        Convert router to list of edges.

        Returns:
            List of Edge objects
        """
        edges = []
        for condition, to_node in self.routes:
            edge = Edge(self.from_node, to_node, condition)
            edges.append(edge)

        if self.default_route:
            # Default route has no condition
            edge = Edge(self.from_node, self.default_route, None)
            edges.append(edge)

        return edges


class EdgeManager:
    """
    Manages all edges for a workflow graph.

    Provides efficient lookups of outgoing edges from nodes.
    """

    def __init__(self):
        """Initialize edge manager"""
        self.edges: List[Edge] = []
        self._outgoing_edges: Dict[str, List[Edge]] = {}

    def add_edge(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable[[WorkflowState], bool]] = None,
        description: str = ""
    ) -> Edge:
        """
        Add an edge to the graph.

        Args:
            from_node: Source node name
            to_node: Destination node name
            condition: Optional condition function
            description: Edge description

        Returns:
            The created Edge object
        """
        edge = Edge(from_node, to_node, condition, description)
        self.edges.append(edge)

        # Update outgoing edges index
        if from_node not in self._outgoing_edges:
            self._outgoing_edges[from_node] = []
        self._outgoing_edges[from_node].append(edge)

        return edge

    def get_outgoing_edges(self, node_name: str) -> List[Edge]:
        """
        Get all outgoing edges from a node.

        Args:
            node_name: Node name

        Returns:
            List of outgoing edges
        """
        return self._outgoing_edges.get(node_name, [])

    async def get_next_node(
        self,
        current_node: str,
        state: WorkflowState
    ) -> Optional[str]:
        """
        Determine the next node to execute.

        Evaluates all outgoing edges and returns the first one whose
        condition passes (or the first unconditional edge).

        Args:
            current_node: Current node name
            state: Current workflow state

        Returns:
            Name of next node, or None if no edge should be traversed
        """
        outgoing_edges = self.get_outgoing_edges(current_node)

        if not outgoing_edges:
            # No outgoing edges means this is an end node
            return None

        # Evaluate edges in order
        for edge in outgoing_edges:
            if await edge.should_traverse(state):
                return edge.to_node

        # No edge condition passed
        return None

    def has_outgoing_edges(self, node_name: str) -> bool:
        """Check if node has any outgoing edges"""
        return len(self.get_outgoing_edges(node_name)) > 0

    def get_all_edges(self) -> List[Edge]:
        """Get all edges in the graph"""
        return self.edges.copy()

    def clear(self):
        """Remove all edges"""
        self.edges.clear()
        self._outgoing_edges.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_edges": len(self.edges),
            "edges": [edge.to_dict() for edge in self.edges]
        }


# Common condition functions

def always_true(state: WorkflowState) -> bool:
    """Always return True (unconditional edge)"""
    return True


def always_false(state: WorkflowState) -> bool:
    """Always return False (disabled edge)"""
    return False


def has_data_key(key: str) -> Callable[[WorkflowState], bool]:
    """Create condition that checks if state.data has a key"""
    def condition(state: WorkflowState) -> bool:
        return key in state.data
    return condition


def data_value_equals(key: str, value: Any) -> Callable[[WorkflowState], bool]:
    """Create condition that checks if state.data[key] equals value"""
    def condition(state: WorkflowState) -> bool:
        return state.get_data(key) == value
    return condition


def data_value_greater_than(key: str, threshold: float) -> Callable[[WorkflowState], bool]:
    """Create condition that checks if state.data[key] > threshold"""
    def condition(state: WorkflowState) -> bool:
        value = state.get_data(key, 0)
        return float(value) > threshold
    return condition


def data_value_less_than(key: str, threshold: float) -> Callable[[WorkflowState], bool]:
    """Create condition that checks if state.data[key] < threshold"""
    def condition(state: WorkflowState) -> bool:
        value = state.get_data(key, float('inf'))
        return float(value) < threshold
    return condition


def has_no_errors(state: WorkflowState) -> bool:
    """Check if state has no errors"""
    return not state.has_errors()


def has_errors(state: WorkflowState) -> bool:
    """Check if state has errors"""
    return state.has_errors()
