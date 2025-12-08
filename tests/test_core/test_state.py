"""Tests for WorkflowState"""

import pytest
from datetime import datetime
from app.core.state import WorkflowState


def test_state_creation():
    """Test creating a basic workflow state"""
    state = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1"
    )

    assert state.workflow_id == "test-workflow"
    assert state.run_id == "test-run-1"
    assert state.iteration == 0
    assert state.data == {}
    assert state.errors == []
    assert state.warnings == []


def test_state_with_data():
    """Test creating state with initial data"""
    state = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1",
        data={"user_id": 123, "action": "process"}
    )

    assert state.get_data("user_id") == 123
    assert state.get_data("action") == "process"
    assert state.get_data("missing", "default") == "default"


def test_state_immutable_update():
    """Test immutable state updates"""
    state1 = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1",
        data={"count": 0}
    )

    # Update state
    state2 = state1.set_data("count", 1)

    # Original state unchanged
    assert state1.get_data("count") == 0
    # New state has update
    assert state2.get_data("count") == 1
    # Different instances
    assert state1 is not state2


def test_state_merge_data():
    """Test merging data into state"""
    state1 = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1",
        data={"a": 1, "b": 2}
    )

    state2 = state1.merge_data({"b": 20, "c": 3})

    assert state2.get_data("a") == 1
    assert state2.get_data("b") == 20  # Updated
    assert state2.get_data("c") == 3   # New
    # Original unchanged
    assert state1.get_data("b") == 2


def test_state_errors():
    """Test error tracking"""
    state1 = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1"
    )

    assert not state1.has_errors()

    state2 = state1.add_error("Something went wrong")
    assert state2.has_errors()
    assert len(state2.errors) == 1
    assert "Something went wrong" in state2.errors


def test_state_warnings():
    """Test warning tracking"""
    state1 = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1"
    )

    state2 = state1.add_warning("This might be an issue")
    assert len(state2.warnings) == 1
    assert "This might be an issue" in state2.warnings


def test_state_iteration():
    """Test iteration tracking"""
    state1 = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1"
    )

    assert state1.iteration == 0

    state2 = state1.increment_iteration()
    assert state2.iteration == 1
    assert state1.iteration == 0  # Original unchanged


def test_state_serialization():
    """Test state to_dict and JSON serialization"""
    state = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1",
        data={"count": 5},
        errors=["error1"],
        warnings=["warning1"],
        config={"max_iterations": 100}
    )

    state_dict = state.to_dict()

    assert state_dict["workflow_id"] == "test-workflow"
    assert state_dict["run_id"] == "test-run-1"
    assert state_dict["data"]["count"] == 5
    assert "error1" in state_dict["errors"]
    assert "warning1" in state_dict["warnings"]
    assert state_dict["config"]["max_iterations"] == 100

    # Test JSON serialization
    json_str = state.to_json()
    assert isinstance(json_str, str)
    assert "test-workflow" in json_str


def test_state_from_dict():
    """Test creating state from dictionary"""
    state_dict = {
        "workflow_id": "test-workflow",
        "run_id": "test-run-1",
        "timestamp": datetime.utcnow().isoformat(),
        "iteration": 5,
        "data": {"count": 10},
        "errors": [],
        "warnings": [],
        "config": {}
    }

    state = WorkflowState.from_dict(state_dict)

    assert state.workflow_id == "test-workflow"
    assert state.iteration == 5
    assert state.get_data("count") == 10


def test_state_copy_with_updates():
    """Test copy_with_updates method"""
    state1 = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1",
        data={"a": 1}
    )

    state2 = state1.copy_with_updates(
        iteration=5,
        data={"b": 2}
    )

    assert state2.iteration == 5
    assert state2.get_data("a") == 1  # Merged from original
    assert state2.get_data("b") == 2  # New data
    assert state1.iteration == 0      # Original unchanged


def test_state_clear_errors():
    """Test clearing errors"""
    state1 = WorkflowState(
        workflow_id="test-workflow",
        run_id="test-run-1",
        errors=["error1", "error2"]
    )

    assert state1.has_errors()

    state2 = state1.clear_errors()
    assert not state2.has_errors()
    assert len(state2.errors) == 0
    # Original unchanged
    assert len(state1.errors) == 2
