"""Workflow Execution Engine

The engine orchestrates workflow execution by traversing the graph,
executing nodes, managing state, and handling errors.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import time

from app.core.graph import Graph
from app.core.state import WorkflowState
from app.core.node import Node
from app.utils.exceptions import (
    WorkflowException,
    MaxIterationsExceeded,
    NodeExecutionError,
    GraphValidationError
)


class ExecutionLog:
    """
    Log entry for a single node execution.
    """

    def __init__(
        self,
        node_name: str,
        status: str,
        timestamp: datetime,
        iteration: int,
        execution_time_ms: float = 0.0,
        error: Optional[str] = None
    ):
        """
        Create an execution log entry.

        Args:
            node_name: Name of the executed node
            status: Execution status ("started", "completed", "failed")
            timestamp: When the execution occurred
            iteration: Iteration number
            execution_time_ms: Execution time in milliseconds
            error: Error message if failed
        """
        self.node_name = node_name
        self.status = status
        self.timestamp = timestamp
        self.iteration = iteration
        self.execution_time_ms = execution_time_ms
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node": self.node_name,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "iteration": self.iteration,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error
        }


class WorkflowEngine:
    """
    Core workflow execution engine.

    Executes workflow graphs by traversing nodes, managing state,
    and handling branching and loops.
    """

    def __init__(
        self,
        max_iterations: int = 100,
        timeout: Optional[float] = None
    ):
        """
        Initialize the workflow engine.

        Args:
            max_iterations: Maximum number of iterations before stopping
            timeout: Optional timeout in seconds for entire workflow
        """
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.execution_log: List[ExecutionLog] = []
        self.current_iteration = 0

    async def execute(
        self,
        graph: Graph,
        initial_state: WorkflowState
    ) -> WorkflowState:
        """
        Execute a workflow graph.

        Args:
            graph: The workflow graph to execute
            initial_state: Starting state

        Returns:
            Final workflow state after execution

        Raises:
            GraphValidationError: If graph is invalid
            MaxIterationsExceeded: If max iterations reached
            WorkflowException: If execution fails
        """
        # Clear previous execution log
        self.execution_log.clear()
        self.current_iteration = 0

        # Validate graph
        try:
            graph.validate()
        except ValueError as e:
            raise GraphValidationError(f"Invalid graph: {e}")

        # Initialize state
        state = initial_state
        current_node_name = graph.entry_point
        start_time = time.time()

        # Main execution loop
        while current_node_name and self.current_iteration < self.max_iterations:
            # Check timeout
            if self.timeout:
                elapsed = time.time() - start_time
                if elapsed > self.timeout:
                    raise WorkflowException(
                        f"Workflow timeout exceeded: {elapsed:.2f}s > {self.timeout}s"
                    )

            # Get node
            node = graph.get_node(current_node_name)
            if not node:
                raise WorkflowException(f"Node '{current_node_name}' not found in graph")

            # Execute node
            state = await self._execute_node(node, state)

            # Check for errors
            if state.has_errors():
                self._log_execution(
                    current_node_name,
                    "failed",
                    state,
                    error="; ".join(state.errors)
                )
                # Stop execution on error
                break

            # Determine next node
            current_node_name = await graph.edge_manager.get_next_node(
                current_node_name,
                state
            )

            # Increment iteration
            self.current_iteration += 1
            state = state.increment_iteration()

        # Check if max iterations exceeded
        if self.current_iteration >= self.max_iterations:
            raise MaxIterationsExceeded(
                f"Max iterations ({self.max_iterations}) exceeded"
            )

        return state

    async def _execute_node(
        self,
        node: Node,
        state: WorkflowState
    ) -> WorkflowState:
        """
        Execute a single node.

        Args:
            node: Node to execute
            state: Current state

        Returns:
            Updated state

        Raises:
            NodeExecutionError: If node execution fails
        """
        node_name = node.name
        start_time = time.time()

        # Log start
        self._log_execution(node_name, "started", state)

        try:
            # Execute node
            result_state = await node.execute(state)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Log completion
            self._log_execution(
                node_name,
                "completed",
                result_state,
                execution_time_ms=execution_time_ms
            )

            return result_state

        except Exception as e:
            # Log failure
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Node execution failed: {str(e)}"

            self._log_execution(
                node_name,
                "failed",
                state,
                execution_time_ms=execution_time_ms,
                error=error_msg
            )

            raise NodeExecutionError(node_name, str(e))

    def _log_execution(
        self,
        node_name: str,
        status: str,
        state: WorkflowState,
        execution_time_ms: float = 0.0,
        error: Optional[str] = None
    ) -> None:
        """
        Log a node execution.

        Args:
            node_name: Node name
            status: Execution status
            state: Current state
            execution_time_ms: Execution time
            error: Error message if failed
        """
        log_entry = ExecutionLog(
            node_name=node_name,
            status=status,
            timestamp=datetime.utcnow(),
            iteration=self.current_iteration,
            execution_time_ms=execution_time_ms,
            error=error
        )
        self.execution_log.append(log_entry)

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """
        Get the execution log as a list of dictionaries.

        Returns:
            List of log entries
        """
        return [entry.to_dict() for entry in self.execution_log]

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the execution.

        Returns:
            Dictionary with execution summary
        """
        total_time = sum(
            entry.execution_time_ms
            for entry in self.execution_log
            if entry.status == "completed"
        )

        failed_nodes = [
            entry.node_name
            for entry in self.execution_log
            if entry.status == "failed"
        ]

        completed_nodes = [
            entry.node_name
            for entry in self.execution_log
            if entry.status == "completed"
        ]

        return {
            "total_iterations": self.current_iteration,
            "total_execution_time_ms": total_time,
            "nodes_executed": len(completed_nodes),
            "nodes_failed": len(failed_nodes),
            "failed_nodes": failed_nodes,
            "completed_nodes": completed_nodes
        }

    def clear_log(self) -> None:
        """Clear the execution log"""
        self.execution_log.clear()
        self.current_iteration = 0


class ParallelWorkflowEngine(WorkflowEngine):
    """
    Extended engine that supports parallel node execution.

    When multiple nodes have no dependencies between them, they can be
    executed in parallel for better performance.

    NOTE: This is a future enhancement - not implemented in Phase 2.
    """

    async def execute_parallel(
        self,
        graph: Graph,
        initial_state: WorkflowState
    ) -> WorkflowState:
        """
        Execute workflow with parallel node execution where possible.

        Args:
            graph: Workflow graph
            initial_state: Starting state

        Returns:
            Final state

        Note:
            This is a placeholder for future parallel execution support.
            Currently delegates to regular execute().
        """
        # TODO: Implement parallel execution
        # For now, fall back to sequential execution
        return await self.execute(graph, initial_state)


# Utility functions

async def run_workflow(
    graph: Graph,
    initial_state: WorkflowState,
    max_iterations: int = 100,
    timeout: Optional[float] = None
) -> tuple[WorkflowState, List[Dict[str, Any]]]:
    """
    Convenience function to run a workflow and get results.

    Args:
        graph: Workflow graph to execute
        initial_state: Starting state
        max_iterations: Maximum iterations
        timeout: Optional timeout in seconds

    Returns:
        Tuple of (final_state, execution_log)

    Example:
        >>> graph = create_simple_graph(...)
        >>> state = WorkflowState(workflow_id="w1", run_id="r1")
        >>> final_state, log = await run_workflow(graph, state)
    """
    engine = WorkflowEngine(max_iterations=max_iterations, timeout=timeout)
    final_state = await engine.execute(graph, initial_state)
    execution_log = engine.get_execution_log()

    return final_state, execution_log


async def run_workflow_with_stats(
    graph: Graph,
    initial_state: WorkflowState,
    max_iterations: int = 100,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Run workflow and return detailed statistics.

    Args:
        graph: Workflow graph
        initial_state: Starting state
        max_iterations: Maximum iterations
        timeout: Optional timeout

    Returns:
        Dictionary with final_state, execution_log, and summary

    Example:
        >>> result = await run_workflow_with_stats(graph, state)
        >>> print(result["summary"]["total_execution_time_ms"])
    """
    engine = WorkflowEngine(max_iterations=max_iterations, timeout=timeout)

    try:
        final_state = await engine.execute(graph, initial_state)
        success = True
        error = None
    except Exception as e:
        final_state = initial_state.add_error(str(e))
        success = False
        error = str(e)

    return {
        "success": success,
        "error": error,
        "final_state": final_state.to_dict(),
        "execution_log": engine.get_execution_log(),
        "summary": engine.get_execution_summary()
    }
