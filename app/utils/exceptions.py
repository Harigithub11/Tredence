"""Custom Exceptions for Workflow Engine

Defines all custom exceptions used throughout the application.
"""


class WorkflowException(Exception):
    """Base exception for all workflow-related errors"""
    pass


class GraphValidationError(WorkflowException):
    """Raised when graph structure is invalid"""
    pass


class NodeExecutionError(WorkflowException):
    """Raised when node execution fails"""

    def __init__(self, node_name: str, message: str):
        """
        Initialize node execution error.

        Args:
            node_name: Name of the node that failed
            message: Error message
        """
        self.node_name = node_name
        super().__init__(f"Node '{node_name}' failed: {message}")


class MaxIterationsExceeded(WorkflowException):
    """Raised when workflow exceeds maximum iterations"""
    pass


class ToolNotFoundError(WorkflowException):
    """Raised when requested tool doesn't exist in registry"""
    pass


class StateValidationError(WorkflowException):
    """Raised when workflow state is invalid"""
    pass


class EdgeConditionError(WorkflowException):
    """Raised when edge condition evaluation fails"""
    pass


class DatabaseError(WorkflowException):
    """Base exception for database-related errors"""
    pass


class RunNotFoundError(DatabaseError):
    """Raised when workflow run is not found in database"""
    pass


class GraphNotFoundError(DatabaseError):
    """Raised when graph is not found in database"""
    pass
