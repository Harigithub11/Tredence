"""Tests for database repositories"""

import pytest
from datetime import datetime

from app.database.models import ExecutionStatus, NodeExecutionStatus
from app.database.repositories import (
    GraphRepository,
    RunRepository,
    ExecutionLogRepository
)


@pytest.mark.asyncio
async def test_graph_repository_create(db_session):
    """Test creating a graph"""
    repo = GraphRepository(db_session)

    graph = await repo.create(
        name="test_workflow",
        description="Test workflow",
        definition={
            "nodes": [{"name": "a"}, {"name": "b"}],
            "edges": [{"from": "a", "to": "b"}],
            "entry_point": "a"
        }
    )

    assert graph.id is not None
    assert graph.name == "test_workflow"
    assert graph.description == "Test workflow"
    assert graph.definition["entry_point"] == "a"
    assert graph.is_active == 1


@pytest.mark.asyncio
async def test_graph_repository_get_by_id(db_session):
    """Test getting graph by ID"""
    repo = GraphRepository(db_session)

    # Create graph
    created_graph = await repo.create(
        name="test_graph",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    # Get by ID
    retrieved_graph = await repo.get_by_id(created_graph.id)

    assert retrieved_graph is not None
    assert retrieved_graph.id == created_graph.id
    assert retrieved_graph.name == "test_graph"


@pytest.mark.asyncio
async def test_graph_repository_get_by_name(db_session):
    """Test getting graph by name"""
    repo = GraphRepository(db_session)

    # Create graph
    await repo.create(
        name="unique_graph",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    # Get by name
    retrieved_graph = await repo.get_by_name("unique_graph")

    assert retrieved_graph is not None
    assert retrieved_graph.name == "unique_graph"


@pytest.mark.asyncio
async def test_graph_repository_list_graphs(db_session):
    """Test listing graphs"""
    repo = GraphRepository(db_session)

    # Create multiple graphs
    await repo.create(
        name="graph1",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await repo.create(
        name="graph2",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    # List graphs
    graphs = await repo.list_graphs()

    assert len(graphs) >= 2
    graph_names = [g.name for g in graphs]
    assert "graph1" in graph_names
    assert "graph2" in graph_names


@pytest.mark.asyncio
async def test_graph_repository_update(db_session):
    """Test updating a graph"""
    repo = GraphRepository(db_session)

    # Create graph
    graph = await repo.create(
        name="update_test",
        description="Original description",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    # Update graph
    updated_graph = await repo.update(
        graph_id=graph.id,
        description="Updated description",
        version=2
    )
    await db_session.commit()

    assert updated_graph is not None
    assert updated_graph.description == "Updated description"
    assert updated_graph.version == 2


@pytest.mark.asyncio
async def test_graph_repository_delete(db_session):
    """Test soft deleting a graph"""
    repo = GraphRepository(db_session)

    # Create graph
    graph = await repo.create(
        name="delete_test",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    # Delete graph (soft delete)
    result = await repo.delete(graph.id)
    await db_session.commit()

    assert result is True

    # Check that graph is marked as inactive
    deleted_graph = await repo.get_by_id(graph.id)
    assert deleted_graph is not None
    assert deleted_graph.is_active == 0


@pytest.mark.asyncio
async def test_run_repository_create(db_session):
    """Test creating a run"""
    # First create a graph
    graph_repo = GraphRepository(db_session)
    graph = await graph_repo.create(
        name="test_graph_for_run",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    # Create run
    run_repo = RunRepository(db_session)
    run = await run_repo.create(
        run_id="run_123",
        graph_id=graph.id,
        initial_state={
            "workflow_id": "test",
            "run_id": "run_123",
            "data": {}
        }
    )

    assert run.id is not None
    assert run.run_id == "run_123"
    assert run.graph_id == graph.id
    assert run.status == ExecutionStatus.PENDING


@pytest.mark.asyncio
async def test_run_repository_get_by_run_id(db_session):
    """Test getting run by run_id"""
    # Create graph and run
    graph_repo = GraphRepository(db_session)
    graph = await graph_repo.create(
        name="test_graph_for_get",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    run_repo = RunRepository(db_session)
    created_run = await run_repo.create(
        run_id="run_456",
        graph_id=graph.id,
        initial_state={"data": {}}
    )
    await db_session.commit()

    # Get by run_id
    retrieved_run = await run_repo.get_by_run_id("run_456")

    assert retrieved_run is not None
    assert retrieved_run.run_id == "run_456"
    assert retrieved_run.graph is not None  # Verify eager loading


@pytest.mark.asyncio
async def test_run_repository_update_status(db_session):
    """Test updating run status"""
    # Create graph and run
    graph_repo = GraphRepository(db_session)
    graph = await graph_repo.create(
        name="test_graph_status",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    run_repo = RunRepository(db_session)
    run = await run_repo.create(
        run_id="run_status",
        graph_id=graph.id,
        initial_state={"data": {}}
    )
    await db_session.commit()

    # Update to RUNNING
    updated_run = await run_repo.update_status(
        run_id="run_status",
        status=ExecutionStatus.RUNNING
    )
    await db_session.commit()

    assert updated_run.status == ExecutionStatus.RUNNING
    assert updated_run.started_at is not None

    # Update to COMPLETED
    updated_run = await run_repo.update_status(
        run_id="run_status",
        status=ExecutionStatus.COMPLETED
    )
    await db_session.commit()

    assert updated_run.status == ExecutionStatus.COMPLETED
    assert updated_run.completed_at is not None


@pytest.mark.asyncio
async def test_run_repository_update_final_state(db_session):
    """Test updating run final state"""
    # Create graph and run
    graph_repo = GraphRepository(db_session)
    graph = await graph_repo.create(
        name="test_graph_final",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    run_repo = RunRepository(db_session)
    run = await run_repo.create(
        run_id="run_final",
        graph_id=graph.id,
        initial_state={"data": {}}
    )
    await db_session.commit()

    # Update final state
    updated_run = await run_repo.update_final_state(
        run_id="run_final",
        final_state={"data": {"result": 42}},
        total_iterations=5,
        total_execution_time_ms=123.45
    )
    await db_session.commit()

    assert updated_run.final_state == {"data": {"result": 42}}
    assert updated_run.total_iterations == 5
    assert updated_run.total_execution_time_ms == 123.45


@pytest.mark.asyncio
async def test_execution_log_repository_create(db_session):
    """Test creating execution log"""
    # Create graph and run
    graph_repo = GraphRepository(db_session)
    graph = await graph_repo.create(
        name="test_graph_log",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    run_repo = RunRepository(db_session)
    run = await run_repo.create(
        run_id="run_log",
        graph_id=graph.id,
        initial_state={"data": {}}
    )
    await db_session.commit()

    # Create execution log
    log_repo = ExecutionLogRepository(db_session)
    log = await log_repo.create(
        run_id=run.id,
        node_name="node_a",
        status=NodeExecutionStatus.COMPLETED,
        iteration=0,
        execution_time_ms=10.5
    )

    assert log.id is not None
    assert log.run_id == run.id
    assert log.node_name == "node_a"
    assert log.status == NodeExecutionStatus.COMPLETED
    assert log.iteration == 0
    assert log.execution_time_ms == 10.5


@pytest.mark.asyncio
async def test_execution_log_repository_get_by_run_id(db_session):
    """Test getting execution logs by run_id"""
    # Create graph and run
    graph_repo = GraphRepository(db_session)
    graph = await graph_repo.create(
        name="test_graph_logs",
        definition={"nodes": [], "edges": [], "entry_point": "start"}
    )
    await db_session.commit()

    run_repo = RunRepository(db_session)
    run = await run_repo.create(
        run_id="run_logs",
        graph_id=graph.id,
        initial_state={"data": {}}
    )
    await db_session.commit()

    # Create multiple logs
    log_repo = ExecutionLogRepository(db_session)
    await log_repo.create(
        run_id=run.id,
        node_name="node_a",
        status=NodeExecutionStatus.COMPLETED,
        iteration=0
    )
    await log_repo.create(
        run_id=run.id,
        node_name="node_b",
        status=NodeExecutionStatus.COMPLETED,
        iteration=1
    )
    await db_session.commit()

    # Get all logs for run
    logs = await log_repo.get_by_run_id(run.id)

    assert len(logs) == 2
    assert logs[0].node_name == "node_a"
    assert logs[1].node_name == "node_b"
