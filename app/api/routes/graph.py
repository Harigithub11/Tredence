"""Graph API Routes

Endpoints for creating and managing workflow graphs and executions.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from datetime import datetime

from app.database.connection import get_session
from app.database.repositories import GraphRepository, RunRepository, ExecutionLogRepository
from app.database.models import ExecutionStatus, NodeExecutionStatus
from app.api.models import (
    CreateGraphRequest,
    RunGraphRequest,
    GraphResponse,
    RunResponse,
    RunWithLogsResponse,
    StateResponse,
    ExecutionLogEntry
)
from app.core.engine import WorkflowEngine
from app.core.graph import GraphBuilder
from app.core.state import WorkflowState

router = APIRouter(prefix="/graph", tags=["graphs"])


@router.post("/create", response_model=GraphResponse, status_code=status.HTTP_201_CREATED)
async def create_graph(
    request: CreateGraphRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new workflow graph.

    **Parameters:**
    - name: Unique workflow name
    - description: Optional description
    - nodes: List of node definitions (name, tool)
    - edges: List of edge connections (from, to, condition)
    - entry_point: Starting node name

    **Returns:**
    - Graph details with ID and metadata

    **Raises:**
    - 400: Graph with name already exists
    - 422: Validation error
    """
    graph_repo = GraphRepository(session)

    # Check if name already exists
    existing = await graph_repo.get_by_name(request.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph with name '{request.name}' already exists"
        )

    # Prepare graph definition
    definition = {
        "nodes": [node.model_dump() for node in request.nodes],
        "edges": [edge.model_dump(by_alias=True) for edge in request.edges],
        "entry_point": request.entry_point
    }

    # Create graph in database
    graph = await graph_repo.create(
        name=request.name,
        description=request.description,
        definition=definition
    )

    await session.commit()

    return GraphResponse.model_validate(graph)


async def execute_workflow_background(
    run_id: str,
    graph_id: int,
    initial_state_dict: dict
):
    """
    Background task to execute workflow.

    This runs asynchronously and updates the database as it progresses.
    """
    from app.database.connection import get_session_context

    async with get_session_context() as session:
        graph_repo = GraphRepository(session)
        run_repo = RunRepository(session)
        log_repo = ExecutionLogRepository(session)

        try:
            # Get graph
            graph = await graph_repo.get_by_id(graph_id)
            if not graph:
                raise Exception(f"Graph {graph_id} not found")

            # Get run record
            run = await run_repo.get_by_run_id(run_id)
            if not run:
                raise Exception(f"Run {run_id} not found")

            # Update status to running
            await run_repo.update_status(run_id, ExecutionStatus.RUNNING)
            await session.commit()

            # Build graph from definition
            builder = GraphBuilder(name=graph.name)

            # Extract definition
            definition = graph.definition
            nodes_def = definition.get("nodes", [])
            edges_def = definition.get("edges", [])
            entry_point = definition.get("entry_point")

            # For now, we'll use lambda nodes as placeholders
            # In real implementation, these would map to actual registered tools
            from app.core.node import LambdaNode

            for node_def in nodes_def:
                node_name = node_def["name"]
                # Placeholder: just pass state through
                builder.node(node_name, LambdaNode(
                    name=node_name,
                    transform=lambda state: state  # Identity function
                ))

            for edge_def in edges_def:
                from_node = edge_def["from"]
                to_node = edge_def["to"]
                builder.edge(from_node, to_node)

            builder.entry(entry_point)
            workflow_graph = builder.build()

            # Create initial state
            initial_state = WorkflowState(
                workflow_id=graph.name,
                run_id=run_id,
                **initial_state_dict
            )

            # Execute workflow
            engine = WorkflowEngine()

            # Execute
            start_time = datetime.utcnow()
            final_state = await engine.execute(workflow_graph, initial_state)
            end_time = datetime.utcnow()

            execution_time_ms = (end_time - start_time).total_seconds() * 1000

            # Update run with final state
            await run_repo.update_final_state(
                run_id=run_id,
                final_state=final_state.model_dump(mode='json'),
                total_iterations=final_state.iteration + 1,
                total_execution_time_ms=execution_time_ms
            )

            # Update status to completed
            await run_repo.update_status(run_id, ExecutionStatus.COMPLETED)
            await session.commit()

        except Exception as e:
            # Update status to failed
            await run_repo.update_status(
                run_id=run_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e)
            )
            await session.commit()
            raise


@router.post("/run", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_graph(
    request: RunGraphRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    Execute a workflow graph.

    **Parameters:**
    - graph_name: Name of the graph to execute
    - initial_state: Starting state for the workflow
    - timeout: Maximum execution time in seconds (optional)
    - use_llm: Enable LLM features (optional)

    **Returns:**
    - Run details with status and execution info

    **Raises:**
    - 404: Graph not found
    - 422: Validation error

    **Note:**
    Execution runs in the background. Use GET /graph/state/{run_id} to poll status.
    """
    graph_repo = GraphRepository(session)
    run_repo = RunRepository(session)

    # Get graph by name
    graph = await graph_repo.get_by_name(request.graph_name)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{request.graph_name}' not found"
        )

    # Generate unique run ID
    run_id = f"run_{uuid.uuid4().hex[:12]}"

    # Prepare initial state
    initial_state = {
        "workflow_id": graph.name,
        "run_id": run_id,
        **request.initial_state
    }

    # Create run record
    run = await run_repo.create(
        run_id=run_id,
        graph_id=graph.id,
        initial_state=initial_state
    )

    await session.commit()

    # Start execution in background
    background_tasks.add_task(
        execute_workflow_background,
        run_id=run_id,
        graph_id=graph.id,
        initial_state_dict=request.initial_state
    )

    return RunResponse.model_validate(run)


@router.get("/state/{run_id}", response_model=RunWithLogsResponse)
async def get_run_state(
    run_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get the current state of a workflow execution.

    **Parameters:**
    - run_id: Run identifier

    **Returns:**
    - Run details including current state, status, and execution logs

    **Raises:**
    - 404: Run not found
    """
    run_repo = RunRepository(session)
    log_repo = ExecutionLogRepository(session)

    # Get run
    run = await run_repo.get_by_run_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found"
        )

    # Get execution logs
    logs = await log_repo.get_by_run_id(run.id)

    # Build response manually to avoid lazy-loading issues
    response_data = RunWithLogsResponse(
        id=run.id,
        run_id=run.run_id,
        graph_id=run.graph_id,
        status=run.status.value,
        started_at=run.started_at,
        completed_at=run.completed_at,
        initial_state=run.initial_state,
        final_state=run.final_state,
        total_iterations=run.total_iterations,
        total_execution_time_ms=run.total_execution_time_ms,
        error_message=run.error_message,
        execution_logs=[ExecutionLogEntry.model_validate(log) for log in logs]
    )

    return response_data


@router.get("/{graph_id}", response_model=GraphResponse)
async def get_graph(
    graph_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Get graph details by ID.

    **Parameters:**
    - graph_id: Graph database ID

    **Returns:**
    - Graph details

    **Raises:**
    - 404: Graph not found
    """
    graph_repo = GraphRepository(session)

    graph = await graph_repo.get_by_id(graph_id)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph {graph_id} not found"
        )

    return GraphResponse.model_validate(graph)


@router.get("/name/{graph_name}", response_model=GraphResponse)
async def get_graph_by_name(
    graph_name: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get graph details by name.

    **Parameters:**
    - graph_name: Graph name

    **Returns:**
    - Graph details

    **Raises:**
    - 404: Graph not found
    """
    graph_repo = GraphRepository(session)

    graph = await graph_repo.get_by_name(graph_name)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_name}' not found"
        )

    return GraphResponse.model_validate(graph)


@router.delete("/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_graph(
    graph_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a graph (soft delete - marks as inactive).

    **Parameters:**
    - graph_id: Graph database ID

    **Raises:**
    - 404: Graph not found
    """
    graph_repo = GraphRepository(session)

    success = await graph_repo.delete(graph_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph {graph_id} not found"
        )

    await session.commit()
