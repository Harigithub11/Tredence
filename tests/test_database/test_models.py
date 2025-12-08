"""Tests for database models"""

import pytest
from datetime import datetime

from app.database.models import (
    GraphModel,
    RunModel,
    ExecutionLogModel,
    ExecutionStatus,
    NodeExecutionStatus
)


def test_graph_model_creation():
    """Test creating a GraphModel instance"""
    graph = GraphModel(
        name="test_graph",
        description="Test graph",
        definition={"nodes": [], "edges": [], "entry_point": "start"},
        version=1,
        is_active=1
    )

    assert graph.name == "test_graph"
    assert graph.description == "Test graph"
    assert graph.definition["entry_point"] == "start"
    assert graph.version == 1
    assert graph.is_active == 1


def test_run_model_creation():
    """Test creating a RunModel instance"""
    run = RunModel(
        run_id="run_123",
        graph_id=1,
        status=ExecutionStatus.PENDING,
        initial_state={"data": {}, "workflow_id": "w1", "run_id": "run_123"}
    )

    assert run.run_id == "run_123"
    assert run.graph_id == 1
    assert run.status == ExecutionStatus.PENDING
    assert run.initial_state["run_id"] == "run_123"


def test_execution_log_model_creation():
    """Test creating an ExecutionLogModel instance"""
    log = ExecutionLogModel(
        run_id=1,
        node_name="node_a",
        status=NodeExecutionStatus.COMPLETED,
        iteration=0,
        execution_time_ms=10.5
    )

    assert log.run_id == 1
    assert log.node_name == "node_a"
    assert log.status == NodeExecutionStatus.COMPLETED
    assert log.iteration == 0
    assert log.execution_time_ms == 10.5


def test_execution_status_enum():
    """Test ExecutionStatus enum values"""
    assert ExecutionStatus.PENDING.value == "pending"
    assert ExecutionStatus.RUNNING.value == "running"
    assert ExecutionStatus.COMPLETED.value == "completed"
    assert ExecutionStatus.FAILED.value == "failed"
    assert ExecutionStatus.CANCELLED.value == "cancelled"


def test_node_execution_status_enum():
    """Test NodeExecutionStatus enum values"""
    assert NodeExecutionStatus.STARTED.value == "started"
    assert NodeExecutionStatus.COMPLETED.value == "completed"
    assert NodeExecutionStatus.FAILED.value == "failed"


def test_graph_model_repr():
    """Test GraphModel string representation"""
    graph = GraphModel(
        id=1,
        name="test_graph",
        description="Test",
        definition={}
    )

    repr_str = repr(graph)
    assert "GraphModel" in repr_str
    assert "id=1" in repr_str
    assert "test_graph" in repr_str


def test_run_model_repr():
    """Test RunModel string representation"""
    run = RunModel(
        id=1,
        run_id="run_123",
        graph_id=1,
        status=ExecutionStatus.COMPLETED,
        initial_state={}
    )

    repr_str = repr(run)
    assert "RunModel" in repr_str
    assert "id=1" in repr_str
    assert "run_123" in repr_str
    assert "completed" in repr_str


def test_execution_log_model_repr():
    """Test ExecutionLogModel string representation"""
    log = ExecutionLogModel(
        id=1,
        run_id=1,
        node_name="node_a",
        status=NodeExecutionStatus.COMPLETED,
        iteration=0
    )

    repr_str = repr(log)
    assert "ExecutionLogModel" in repr_str
    assert "run_id=1" in repr_str
    assert "node_a" in repr_str
    assert "completed" in repr_str
