"""Workflow State Management

This module provides type-safe state management for workflows using Pydantic models.
State flows through workflow nodes and can be serialized for database storage.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


class WorkflowState(BaseModel):
    """
    Base state model that flows through workflow nodes.

    The state is immutable - each node creates a new copy with updates.
    This ensures thread safety and makes debugging easier.

    Attributes:
        workflow_id: Unique identifier for the workflow definition
        run_id: Unique identifier for this specific execution
        timestamp: When this state snapshot was created
        iteration: Current iteration number (for loops)
        data: Flexible dictionary for workflow-specific data
        errors: List of error messages encountered
        warnings: List of warning messages
        config: Optional configuration parameters
    """

    # Core identifiers
    workflow_id: str = Field(..., description="Workflow definition ID")
    run_id: str = Field(..., description="Execution run ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    iteration: int = Field(default=0, ge=0, description="Current iteration number")

    # User data (flexible schema for workflow-specific fields)
    data: Dict[str, Any] = Field(default_factory=dict, description="Workflow data")

    # Execution tracking
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")

    # Optional configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters")

    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def copy_with_updates(self, **updates: Any) -> "WorkflowState":
        """
        Create a new state with updates applied.

        This is the primary way to update state in workflows - creates a new
        instance rather than mutating the existing one.

        Args:
            **updates: Fields to update (can include nested data updates)

        Returns:
            New WorkflowState instance with updates applied

        Example:
            >>> state = WorkflowState(workflow_id="w1", run_id="r1")
            >>> new_state = state.copy_with_updates(
            ...     data={"count": 1},
            ...     iteration=1
            ... )
        """
        # Handle nested data updates
        if "data" in updates:
            merged_data = {**self.data, **updates["data"]}
            updates["data"] = merged_data

        return self.model_copy(update=updates)

    def add_error(self, error: str) -> "WorkflowState":
        """
        Add an error message to the state.

        Args:
            error: Error message to add

        Returns:
            New state with error added
        """
        new_errors = self.errors + [error]
        return self.model_copy(update={"errors": new_errors})

    def add_warning(self, warning: str) -> "WorkflowState":
        """
        Add a warning message to the state.

        Args:
            warning: Warning message to add

        Returns:
            New state with warning added
        """
        new_warnings = self.warnings + [warning]
        return self.model_copy(update={"warnings": new_warnings})

    def increment_iteration(self) -> "WorkflowState":
        """
        Increment the iteration counter.

        Returns:
            New state with iteration incremented
        """
        return self.model_copy(update={"iteration": self.iteration + 1})

    def to_json(self) -> str:
        """
        Serialize state to JSON string.

        Returns:
            JSON string representation
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowState":
        """
        Deserialize state from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            WorkflowState instance
        """
        return cls.model_validate_json(json_str)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert state to dictionary.

        Returns:
            Dictionary representation
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """
        Create state from dictionary.

        Args:
            data: Dictionary with state data

        Returns:
            WorkflowState instance
        """
        return cls.model_validate(data)

    def has_errors(self) -> bool:
        """Check if state has any errors"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if state has any warnings"""
        return len(self.warnings) > 0

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Safely get a value from the data dictionary.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Value or default
        """
        return self.data.get(key, default)

    def set_data(self, key: str, value: Any) -> "WorkflowState":
        """
        Set a value in the data dictionary.

        Args:
            key: Key to set
            value: Value to set

        Returns:
            New state with value set
        """
        new_data = {**self.data, key: value}
        return self.model_copy(update={"data": new_data})

    def merge_data(self, data: Dict[str, Any]) -> "WorkflowState":
        """
        Merge multiple key-value pairs into the data dictionary.

        Args:
            data: Dictionary of data to merge

        Returns:
            New state with data merged
        """
        new_data = {**self.data, **data}
        return self.model_copy(update={"data": new_data})

    def clear_errors(self) -> "WorkflowState":
        """
        Clear all errors from the state.

        Returns:
            New state with errors cleared
        """
        return self.model_copy(update={"errors": []})

    def __str__(self) -> str:
        """String representation of state"""
        return (
            f"WorkflowState(workflow_id={self.workflow_id}, "
            f"run_id={self.run_id}, iteration={self.iteration}, "
            f"errors={len(self.errors)}, warnings={len(self.warnings)})"
        )

    def __repr__(self) -> str:
        """Detailed representation"""
        return self.__str__()


class StateSnapshot:
    """
    Utility class for creating and managing state snapshots.

    Useful for debugging, time-travel debugging, and state history tracking.
    """

    def __init__(self, state: WorkflowState, node_name: str, status: str):
        """
        Create a state snapshot.

        Args:
            state: The workflow state to snapshot
            node_name: Name of the node that created this snapshot
            status: Status (e.g., "started", "completed", "failed")
        """
        self.state = state
        self.node_name = node_name
        self.status = status
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary"""
        return {
            "node_name": self.node_name,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state.to_dict()
        }

    def to_json(self) -> str:
        """Convert snapshot to JSON"""
        return json.dumps(self.to_dict())
