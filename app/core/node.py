"""Workflow Node System

Nodes are the executable units of work in a workflow. They receive state,
perform operations, and return updated state.
"""

from abc import ABC, abstractmethod
from typing import Callable, Any, Dict, Optional
from datetime import datetime
import asyncio
import inspect
import time

from app.core.state import WorkflowState


class Node(ABC):
    """
    Abstract base class for workflow nodes.

    All nodes must implement the execute() method which takes a WorkflowState
    and returns an updated WorkflowState.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        **extra_metadata: Any
    ):
        """
        Initialize a node.

        Args:
            name: Unique node name
            func: Function to execute (can be sync or async)
            description: Human-readable description
            metadata: Optional metadata dictionary
            **extra_metadata: Additional metadata as keyword arguments
        """
        self.name = name
        self.func = func
        self.description = description or func.__doc__ or ""
        self.metadata = metadata or {}
        # Merge extra_metadata into metadata
        self.metadata.update(extra_metadata)
        self.execution_count = 0
        self.total_execution_time_ms = 0.0

    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the node logic.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state

        Raises:
            Exception: If node execution fails
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "total_execution_time_ms": self.total_execution_time_ms,
            "avg_execution_time_ms": (
                self.total_execution_time_ms / self.execution_count
                if self.execution_count > 0
                else 0
            )
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "execution_count": self.execution_count,
            "total_execution_time_ms": self.total_execution_time_ms,
            "metadata": self.metadata
        }

    def __str__(self) -> str:
        return f"Node(name={self.name}, executions={self.execution_count})"

    def __repr__(self) -> str:
        return self.__str__()


class AsyncNode(Node):
    """
    Node wrapper for async functions.

    This node type is used when the function is already async.
    """

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute async function with state.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state

        Raises:
            Exception: If function execution fails
        """
        start_time = time.time()

        try:
            # Check if function is actually async
            if not asyncio.iscoroutinefunction(self.func):
                raise TypeError(
                    f"Function {self.func.__name__} must be async for AsyncNode"
                )

            # Execute the async function
            result = await self.func(state)

            # Ensure result is a WorkflowState
            if not isinstance(result, WorkflowState):
                raise TypeError(
                    f"Node {self.name} must return WorkflowState, got {type(result)}"
                )

            return result

        except Exception as e:
            # Add error to state
            error_msg = f"Node '{self.name}' failed: {str(e)}"
            return state.add_error(error_msg)

        finally:
            # Track execution stats (even on error)
            execution_time_ms = (time.time() - start_time) * 1000
            self.execution_count += 1
            self.total_execution_time_ms += execution_time_ms


class SyncNode(Node):
    """
    Node wrapper for synchronous functions.

    The function is executed in a thread pool to avoid blocking the event loop.
    """

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute sync function in thread pool.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state

        Raises:
            Exception: If function execution fails
        """
        start_time = time.time()

        try:
            # Check if function is sync (not async)
            if asyncio.iscoroutinefunction(self.func):
                raise TypeError(
                    f"Function {self.func.__name__} cannot be async for SyncNode"
                )

            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.func, state)

            # Track execution stats
            execution_time_ms = (time.time() - start_time) * 1000
            self.execution_count += 1
            self.total_execution_time_ms += execution_time_ms

            # Ensure result is a WorkflowState
            if not isinstance(result, WorkflowState):
                raise TypeError(
                    f"Node {self.name} must return WorkflowState, got {type(result)}"
                )

            return result

        except Exception as e:
            # Add error to state
            error_msg = f"Node '{self.name}' failed: {str(e)}"
            return state.add_error(error_msg)


class LambdaNode(Node):
    """
    Simple node that applies a transformation to state.

    Useful for quick inline transformations without defining a separate function.
    """

    def __init__(
        self,
        name: str,
        transform: Callable[[WorkflowState], WorkflowState],
        description: str = ""
    ):
        """
        Initialize a lambda node.

        Args:
            name: Node name
            transform: Function that transforms state
            description: Node description
        """
        super().__init__(name, transform, description)

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the transformation"""
        start_time = time.time()

        try:
            # Apply transformation
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(state)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.func, state)

            # Track stats
            execution_time_ms = (time.time() - start_time) * 1000
            self.execution_count += 1
            self.total_execution_time_ms += execution_time_ms

            return result

        except Exception as e:
            error_msg = f"Lambda node '{self.name}' failed: {str(e)}"
            return state.add_error(error_msg)


def create_node(
    name: str,
    func: Callable,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> Node:
    """
    Factory function to create the appropriate node type.

    Automatically detects if the function is async or sync and creates
    the correct node type.

    Args:
        name: Node name
        func: Function to wrap
        description: Node description
        metadata: Optional metadata

    Returns:
        AsyncNode or SyncNode instance

    Example:
        >>> async def my_async_func(state):
        ...     return state
        >>> node = create_node("my_node", my_async_func)
        >>> isinstance(node, AsyncNode)
        True
    """
    if asyncio.iscoroutinefunction(func):
        return AsyncNode(name, func, description, metadata)
    else:
        return SyncNode(name, func, description, metadata)


class NodeExecutionResult:
    """
    Result of a node execution.

    Contains the updated state, execution metadata, and any errors.
    """

    def __init__(
        self,
        node_name: str,
        state: WorkflowState,
        success: bool,
        execution_time_ms: float,
        error: Optional[str] = None
    ):
        """
        Initialize execution result.

        Args:
            node_name: Name of the executed node
            state: Resulting workflow state
            success: Whether execution was successful
            execution_time_ms: Execution time in milliseconds
            error: Error message if failed
        """
        self.node_name = node_name
        self.state = state
        self.success = success
        self.execution_time_ms = execution_time_ms
        self.error = error
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_name": self.node_name,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state.to_dict()
        }
