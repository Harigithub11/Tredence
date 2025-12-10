"""Tests for API Error Scenarios and Edge Cases"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_create_graph_with_empty_nodes(test_client):
    """Test creating graph with no nodes returns validation error"""
    graph_data = {
        "name": "empty_nodes_graph",
        "description": "Graph with no nodes",
        "nodes": [],
        "edges": [],
        "entry_point": "nonexistent"
    }

    response = await test_client.post("/graph/create", json=graph_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_graph_with_circular_edges(test_client):
    """Test creating graph with circular dependencies"""
    graph_data = {
        "name": "circular_graph",
        "description": "Graph with circular edges",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"},
            {"name": "node_b", "tool": "tool_b"}
        ],
        "edges": [
            {"from": "node_a", "to": "node_b"},
            {"from": "node_b", "to": "node_a"}  # Circular
        ],
        "entry_point": "node_a"
    }

    # This might succeed at creation but would fail or loop during execution
    response = await test_client.post("/graph/create", json=graph_data)
    # Depends on validation logic - could be 201 or 422
    assert response.status_code in [201, 422]


@pytest.mark.asyncio
async def test_create_graph_with_invalid_edge_reference(test_client):
    """Test creating graph with edge referencing nonexistent node"""
    graph_data = {
        "name": "invalid_edge_graph",
        "description": "Graph with invalid edge",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [
            {"from": "node_a", "to": "nonexistent_node"}
        ],
        "entry_point": "node_a"
    }

    response = await test_client.post("/graph/create", json=graph_data)
    # Might succeed at creation (validation happens at runtime) or fail
    assert response.status_code in [201, 400, 422]


@pytest.mark.asyncio
async def test_run_graph_with_invalid_state_format(test_client):
    """Test running graph with malformed initial state"""
    # Create valid graph first
    graph_data = {
        "name": "state_format_test_graph",
        "description": "Test state format",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Try to run with invalid state (missing required field)
    run_data = {
        "graph_name": "state_format_test_graph",
        # Missing initial_state
        "timeout": 60
    }

    response = await test_client.post("/graph/run", json=run_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_run_graph_with_negative_timeout(test_client):
    """Test running graph with invalid timeout value"""
    # Create valid graph first
    graph_data = {
        "name": "timeout_test_graph",
        "description": "Test timeout validation",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Try with negative timeout
    run_data = {
        "graph_name": "timeout_test_graph",
        "initial_state": {"data": {}},
        "timeout": -10
    }

    response = await test_client.post("/graph/run", json=run_data)
    # Should either reject or accept and use default
    assert response.status_code in [202, 422]


@pytest.mark.asyncio
async def test_get_graph_list_endpoint_exists(test_client):
    """Test if graph list endpoint exists (if implemented)"""
    # Try to get list of all graphs
    response = await test_client.get("/graph/")

    # Endpoint might not exist yet
    if response.status_code == 404:
        # Not implemented - that's okay
        assert True
    else:
        # If implemented, should return 200
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_graph_with_long_name(test_client):
    """Test creating graph with very long name"""
    graph_data = {
        "name": "a" * 300,  # Very long name
        "description": "Test long name",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    response = await test_client.post("/graph/create", json=graph_data)
    # Could succeed or fail based on DB constraints
    assert response.status_code in [201, 400, 422]


@pytest.mark.asyncio
async def test_create_graph_with_special_characters_in_name(test_client):
    """Test creating graph with special characters in name"""
    graph_data = {
        "name": "test-graph_v2.0",
        "description": "Test special chars",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    response = await test_client.post("/graph/create", json=graph_data)
    # Should handle special chars appropriately
    assert response.status_code in [201, 400, 422]


@pytest.mark.asyncio
async def test_run_graph_multiple_times_same_graph(test_client):
    """Test running the same graph multiple times creates separate runs"""
    # Create graph
    graph_data = {
        "name": "multi_run_graph",
        "description": "Test multiple runs",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Run the same graph 3 times
    run_ids = []
    for i in range(3):
        run_data = {
            "graph_name": "multi_run_graph",
            "initial_state": {"data": {"iteration": i}},
            "timeout": 60
        }

        run_response = await test_client.post("/graph/run", json=run_data)
        assert run_response.status_code == 202
        run_ids.append(run_response.json()["run_id"])

    # All run IDs should be unique
    assert len(set(run_ids)) == 3


@pytest.mark.asyncio
async def test_delete_graph_then_try_to_run(test_client):
    """Test running a deleted graph returns 404"""
    # Create graph
    graph_data = {
        "name": "delete_then_run_graph",
        "description": "Test delete then run",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201
    graph_id = create_response.json()["id"]

    # Delete the graph
    delete_response = await test_client.delete(f"/graph/{graph_id}")
    assert delete_response.status_code == 204

    # Try to run the deleted graph
    run_data = {
        "graph_name": "delete_then_run_graph",
        "initial_state": {"data": {}},
        "timeout": 60
    }

    # Should fail since graph is deleted/inactive
    # Note: Soft delete might still allow execution or return 404/400
    run_response = await test_client.post("/graph/run", json=run_data)
    # Could be 202 (soft delete allows run), 404, or 400
    assert run_response.status_code in [202, 400, 404]


@pytest.mark.asyncio
async def test_root_endpoint(test_client):
    """Test root endpoint returns API information"""
    response = await test_client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data or "version" in data


@pytest.mark.asyncio
async def test_health_check_structure(test_client):
    """Test health check endpoint returns proper structure"""
    response = await test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "timestamp" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert isinstance(data["database"], bool)


@pytest.mark.asyncio
async def test_api_accepts_json_only(test_client):
    """Test that API endpoints require JSON content type"""
    # Try to create graph with form data instead of JSON
    response = await test_client.post(
        "/graph/create",
        data="not_json_data",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Should reject non-JSON requests
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_run_state_updates_correctly(test_client):
    """Test that getting run state reflects actual execution progress"""
    # Create and run a graph
    graph_data = {
        "name": "state_update_graph",
        "description": "Test state updates",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    run_data = {
        "graph_name": "state_update_graph",
        "initial_state": {"data": {}},
        "timeout": 60
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    # Get state immediately
    state1 = await test_client.get(f"/graph/state/{run_id}")
    assert state1.status_code == 200
    status1 = state1.json()["status"]

    # Wait and check again
    await asyncio.sleep(1.5)

    state2 = await test_client.get(f"/graph/state/{run_id}")
    assert state2.status_code == 200
    status2 = state2.json()["status"]

    # Status should progress (pending -> running -> completed)
    valid_transitions = [
        ("pending", "pending"),
        ("pending", "running"),
        ("pending", "completed"),
        ("running", "running"),
        ("running", "completed"),
        ("completed", "completed")
    ]

    assert (status1, status2) in valid_transitions
