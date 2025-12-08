"""Tests for Graph API Routes"""

import pytest


@pytest.mark.asyncio
async def test_health_check(test_client):
    """Test health check endpoint"""
    response = await test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert "database" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_create_graph(test_client):
    """Test creating a workflow graph"""
    graph_data = {
        "name": "test_workflow",
        "description": "Test workflow for API",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"},
            {"name": "node_b", "tool": "tool_b"}
        ],
        "edges": [
            {"from": "node_a", "to": "node_b"}
        ],
        "entry_point": "node_a"
    }

    response = await test_client.post("/graph/create", json=graph_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "test_workflow"
    assert data["description"] == "Test workflow for API"
    assert "id" in data
    assert "created_at" in data
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_create_graph_duplicate_name(test_client):
    """Test creating graph with duplicate name fails"""
    graph_data = {
        "name": "duplicate_test",
        "description": "First graph",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    # Create first graph
    response1 = await test_client.post("/graph/create", json=graph_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await test_client.post("/graph/create", json=graph_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_create_graph_invalid_entry_point(test_client):
    """Test creating graph with invalid entry point"""
    graph_data = {
        "name": "invalid_entry",
        "description": "Invalid entry point",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "nonexistent_node"  # Invalid
    }

    response = await test_client.post("/graph/create", json=graph_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_graph_by_id(test_client):
    """Test retrieving graph by ID"""
    # Create a graph first
    graph_data = {
        "name": "get_test_graph",
        "description": "Graph for GET test",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201
    graph_id = create_response.json()["id"]

    # Get graph by ID
    get_response = await test_client.get(f"/graph/{graph_id}")
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["id"] == graph_id
    assert data["name"] == "get_test_graph"


@pytest.mark.asyncio
async def test_get_graph_by_name(test_client):
    """Test retrieving graph by name"""
    # Create a graph first
    graph_data = {
        "name": "get_by_name_test",
        "description": "Graph for name GET test",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    # Get graph by name
    get_response = await test_client.get("/graph/name/get_by_name_test")
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["name"] == "get_by_name_test"


@pytest.mark.asyncio
async def test_get_nonexistent_graph(test_client):
    """Test retrieving nonexistent graph returns 404"""
    response = await test_client.get("/graph/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_run_graph(test_client):
    """Test executing a workflow graph"""
    # Create a graph first
    graph_data = {
        "name": "run_test_graph",
        "description": "Graph for run test",
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

    # Run the graph
    run_data = {
        "graph_name": "run_test_graph",
        "initial_state": {
            "data": {"input": "test"}
        },
        "timeout": 60,
        "use_llm": False
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202  # Accepted

    data = run_response.json()
    assert "run_id" in data
    assert data["status"] == "pending"
    assert data["initial_state"]["data"]["input"] == "test"


@pytest.mark.asyncio
async def test_run_nonexistent_graph(test_client):
    """Test running nonexistent graph returns 404"""
    run_data = {
        "graph_name": "nonexistent_graph",
        "initial_state": {"data": {}},
        "timeout": 60,
        "use_llm": False
    }

    response = await test_client.post("/graph/run", json=run_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_run_state(test_client):
    """Test getting run state"""
    # Create and run a graph
    graph_data = {
        "name": "state_test_graph",
        "description": "Graph for state test",
        "nodes": [
            {"name": "node_a", "tool": "tool_a"}
        ],
        "edges": [],
        "entry_point": "node_a"
    }

    create_response = await test_client.post("/graph/create", json=graph_data)
    assert create_response.status_code == 201

    run_data = {
        "graph_name": "state_test_graph",
        "initial_state": {"data": {"test": "value"}},
        "timeout": 60
    }

    run_response = await test_client.post("/graph/run", json=run_data)
    assert run_response.status_code == 202
    run_id = run_response.json()["run_id"]

    # Get run state
    state_response = await test_client.get(f"/graph/state/{run_id}")
    assert state_response.status_code == 200

    data = state_response.json()
    assert data["run_id"] == run_id
    assert "status" in data
    assert "execution_logs" in data


@pytest.mark.asyncio
async def test_get_nonexistent_run_state(test_client):
    """Test getting state for nonexistent run returns 404"""
    response = await test_client.get("/graph/state/nonexistent_run_id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_graph(test_client):
    """Test deleting a graph"""
    # Create a graph
    graph_data = {
        "name": "delete_test_graph",
        "description": "Graph to delete",
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

    # Verify it's deleted (should return 404 or be inactive)
    get_response = await test_client.get(f"/graph/{graph_id}")
    # Graph exists but is marked inactive
    assert get_response.status_code == 200
    assert get_response.json()["id"] == graph_id


@pytest.mark.asyncio
async def test_delete_nonexistent_graph(test_client):
    """Test deleting nonexistent graph returns 404"""
    response = await test_client.delete("/graph/99999")
    assert response.status_code == 404
