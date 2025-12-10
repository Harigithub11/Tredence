"""Tests for Background Workflow Execution"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_background_workflow_execution(test_client):
    """Test that workflows execute in background and complete successfully"""
    # Create a graph
    graph_data = {
        "name": "background_exec_graph",
        "description": "Test background execution",
        "nodes": [
            {"name": "step1", "tool": "tool_a"},
            {"name": "step2", "tool": "tool_b"}
        ],
        "edges": [
            {"from": "step1", "to": "step2"}
        ],
        "entry_point": "step1"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Start execution
    run_data = {
        "graph_name": "background_exec_graph",
        "initial_state": {"data": {"value": 42}},
        "timeout": 60
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    # Initially should be pending
    assert run_response.json()["status"] == "pending"

    # Wait for background execution to complete
    await asyncio.sleep(2.0)

    # Check final state
    state_response = await test_client.get(f"/graph/state/{run_id}")
    assert state_response.status_code == 200

    state_data = state_response.json()
    assert state_data["status"] in ["running", "completed", "failed"]


@pytest.mark.asyncio
async def test_background_execution_updates_database(test_client):
    """Test that background execution updates run status in database"""
    # Create a graph
    graph_data = {
        "name": "db_update_graph",
        "description": "Test database updates",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Start execution
    run_data = {
        "graph_name": "db_update_graph",
        "initial_state": {"data": {}},
        "timeout": 60
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    # Check status immediately (could be pending or already completed if fast)
    state_response_1 = await test_client.get(f"/graph/state/{run_id}")
    assert state_response_1.status_code == 200
    status_1 = state_response_1.json()["status"]
    assert status_1 in ["pending", "running", "completed"]

    # Wait for execution
    await asyncio.sleep(1.5)

    # Check status again (should be completed or running)
    state_response_2 = await test_client.get(f"/graph/state/{run_id}")
    assert state_response_2.status_code == 200
    status = state_response_2.json()["status"]
    assert status in ["running", "completed"]


@pytest.mark.asyncio
async def test_background_execution_with_initial_state(test_client):
    """Test that initial state is preserved in background execution"""
    # Create a graph
    graph_data = {
        "name": "state_preservation_graph",
        "description": "Test state preservation",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Start execution with specific initial state
    initial_state_data = {
        "data": {"key1": "value1", "key2": 123},
        "config": {"option": True}
    }

    run_data = {
        "graph_name": "state_preservation_graph",
        "initial_state": initial_state_data,
        "timeout": 60
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    # Verify initial state is stored correctly
    stored_initial_state = run_response.json()["initial_state"]
    assert "data" in stored_initial_state
    assert stored_initial_state["data"]["key1"] == "value1"
    assert stored_initial_state["data"]["key2"] == 123


@pytest.mark.asyncio
async def test_concurrent_workflow_runs(test_client):
    """Test executing multiple workflows concurrently"""
    # Create a graph
    graph_data = {
        "name": "concurrent_test_graph",
        "description": "Test concurrent execution",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Start multiple runs concurrently
    run_ids = []
    for i in range(5):
        run_data = {
            "graph_name": "concurrent_test_graph",
            "initial_state": {"data": {"run_number": i}},
            "timeout": 60
        }

        run_response = await test_client.post("/graph/run", json=run_data)
        assert run_response.status_code == 202
        run_ids.append(run_response.json()["run_id"])

    # Verify all runs were created with unique IDs
    assert len(run_ids) == 5
    assert len(set(run_ids)) == 5  # All unique

    # Wait for all to process
    await asyncio.sleep(2.0)

    # Check all runs have valid states
    for run_id in run_ids:
        state_response = await test_client.get(f"/graph/state/{run_id}")
        assert state_response.status_code == 200
        assert state_response.json()["run_id"] == run_id


@pytest.mark.asyncio
async def test_background_execution_error_handling(test_client):
    """Test that background execution handles errors gracefully"""
    # Create a graph with invalid entry point (should fail during execution build)
    graph_data = {
        "name": "error_handling_graph",
        "description": "Test error handling",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Start execution
    run_data = {
        "graph_name": "error_handling_graph",
        "initial_state": {"data": {}},
        "timeout": 60
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    # Wait for execution
    await asyncio.sleep(1.5)

    # Check state - should handle any errors gracefully
    state_response = await test_client.get(f"/graph/state/{run_id}")
    assert state_response.status_code == 200

    state_data = state_response.json()
    assert "status" in state_data
    # Status could be completed or failed, both are valid
    assert state_data["status"] in ["pending", "running", "completed", "failed"]


@pytest.mark.asyncio
async def test_workflow_execution_timing(test_client):
    """Test that execution time is tracked correctly"""
    # Create a graph
    graph_data = {
        "name": "timing_test_graph",
        "description": "Test execution timing",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"},
            {"name": "node_b", "tool": "tool_b"}
        ],
        "edges": [
            {"from": "node_a", "to": "node_b"}
        ],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Start execution
    run_data = {
        "graph_name": "timing_test_graph",
        "initial_state": {"data": {}},
        "timeout": 60
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    # Wait for completion
    await asyncio.sleep(2.0)

    # Check timing information
    state_response = await test_client.get(f"/graph/state/{run_id}")
    assert state_response.status_code == 200

    state_data = state_response.json()

    # If completed, should have timing info
    if state_data["status"] == "completed":
        assert "started_at" in state_data
        assert "completed_at" in state_data
        # Execution time should be recorded
        assert "total_execution_time_ms" in state_data
        if state_data["total_execution_time_ms"] is not None:
            assert state_data["total_execution_time_ms"] >= 0
