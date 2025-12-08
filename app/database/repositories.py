"""Database Repositories

Provides CRUD operations for database models.
Uses async SQLAlchemy for all database operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    GraphModel,
    RunModel,
    ExecutionLogModel,
    ExecutionStatus,
    NodeExecutionStatus
)


class GraphRepository:
    """
    Repository for Graph model operations.

    Handles CRUD operations for workflow graph definitions.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        name: str,
        definition: Dict[str, Any],
        description: Optional[str] = None
    ) -> GraphModel:
        """
        Create a new graph.

        Args:
            name: Unique graph name
            definition: Graph structure as dict (nodes, edges, entry_point)
            description: Optional description

        Returns:
            Created GraphModel instance
        """
        graph = GraphModel(
            name=name,
            description=description,
            definition=definition,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.session.add(graph)
        await self.session.flush()
        await self.session.refresh(graph)

        return graph

    async def get_by_id(self, graph_id: int) -> Optional[GraphModel]:
        """
        Get graph by ID.

        Args:
            graph_id: Graph ID

        Returns:
            GraphModel instance or None
        """
        result = await self.session.execute(
            select(GraphModel).where(GraphModel.id == graph_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[GraphModel]:
        """
        Get graph by name.

        Args:
            name: Graph name

        Returns:
            GraphModel instance or None
        """
        result = await self.session.execute(
            select(GraphModel).where(GraphModel.name == name)
        )
        return result.scalar_one_or_none()

    async def list_graphs(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[GraphModel]:
        """
        List all graphs with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Only return active graphs

        Returns:
            List of GraphModel instances
        """
        query = select(GraphModel)

        if active_only:
            query = query.where(GraphModel.is_active == 1)

        query = query.order_by(desc(GraphModel.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        graph_id: int,
        definition: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        version: Optional[int] = None
    ) -> Optional[GraphModel]:
        """
        Update graph.

        Args:
            graph_id: Graph ID
            definition: New graph definition
            description: New description
            version: New version number

        Returns:
            Updated GraphModel instance or None
        """
        graph = await self.get_by_id(graph_id)
        if not graph:
            return None

        if definition is not None:
            graph.definition = definition
        if description is not None:
            graph.description = description
        if version is not None:
            graph.version = version

        graph.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(graph)

        return graph

    async def delete(self, graph_id: int) -> bool:
        """
        Soft delete graph by marking as inactive.

        Args:
            graph_id: Graph ID

        Returns:
            True if deleted, False if not found
        """
        graph = await self.get_by_id(graph_id)
        if not graph:
            return False

        graph.is_active = 0
        graph.updated_at = datetime.utcnow()

        await self.session.flush()
        return True

    async def hard_delete(self, graph_id: int) -> bool:
        """
        Permanently delete graph from database.

        Args:
            graph_id: Graph ID

        Returns:
            True if deleted, False if not found

        Warning:
            This will cascade delete all related runs and execution logs.
        """
        result = await self.session.execute(
            delete(GraphModel).where(GraphModel.id == graph_id)
        )
        return result.rowcount > 0


class RunRepository:
    """
    Repository for Run model operations.

    Handles CRUD operations for workflow execution runs.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        run_id: str,
        graph_id: int,
        initial_state: Dict[str, Any]
    ) -> RunModel:
        """
        Create a new run.

        Args:
            run_id: Unique run identifier
            graph_id: ID of graph being executed
            initial_state: Initial workflow state

        Returns:
            Created RunModel instance
        """
        run = RunModel(
            run_id=run_id,
            graph_id=graph_id,
            status=ExecutionStatus.PENDING,
            initial_state=initial_state,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)

        return run

    async def get_by_id(self, run_id: int) -> Optional[RunModel]:
        """
        Get run by database ID.

        Args:
            run_id: Database ID

        Returns:
            RunModel instance or None
        """
        result = await self.session.execute(
            select(RunModel).where(RunModel.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_by_run_id(self, run_id: str) -> Optional[RunModel]:
        """
        Get run by run_id string.

        Args:
            run_id: Run identifier string

        Returns:
            RunModel instance or None
        """
        result = await self.session.execute(
            select(RunModel)
            .where(RunModel.run_id == run_id)
            .options(selectinload(RunModel.graph))
        )
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        graph_id: Optional[int] = None,
        status: Optional[ExecutionStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RunModel]:
        """
        List runs with optional filtering.

        Args:
            graph_id: Filter by graph ID
            status: Filter by execution status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of RunModel instances
        """
        query = select(RunModel)

        filters = []
        if graph_id is not None:
            filters.append(RunModel.graph_id == graph_id)
        if status is not None:
            filters.append(RunModel.status == status)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(RunModel.created_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        run_id: str,
        status: ExecutionStatus,
        error_message: Optional[str] = None
    ) -> Optional[RunModel]:
        """
        Update run status.

        Args:
            run_id: Run identifier
            status: New execution status
            error_message: Optional error message

        Returns:
            Updated RunModel instance or None
        """
        run = await self.get_by_run_id(run_id)
        if not run:
            return None

        run.status = status

        if status == ExecutionStatus.RUNNING and not run.started_at:
            run.started_at = datetime.utcnow()
        elif status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
            run.completed_at = datetime.utcnow()

        if error_message:
            run.error_message = error_message

        run.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(run)

        return run

    async def update_final_state(
        self,
        run_id: str,
        final_state: Dict[str, Any],
        total_iterations: int,
        total_execution_time_ms: float
    ) -> Optional[RunModel]:
        """
        Update run with final state and metrics.

        Args:
            run_id: Run identifier
            final_state: Final workflow state
            total_iterations: Total iteration count
            total_execution_time_ms: Total execution time

        Returns:
            Updated RunModel instance or None
        """
        run = await self.get_by_run_id(run_id)
        if not run:
            return None

        run.final_state = final_state
        run.total_iterations = total_iterations
        run.total_execution_time_ms = total_execution_time_ms
        run.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(run)

        return run

    async def delete(self, run_id: str) -> bool:
        """
        Delete run from database.

        Args:
            run_id: Run identifier

        Returns:
            True if deleted, False if not found

        Note:
            This will cascade delete all execution logs.
        """
        result = await self.session.execute(
            delete(RunModel).where(RunModel.run_id == run_id)
        )
        return result.rowcount > 0


class ExecutionLogRepository:
    """
    Repository for ExecutionLog model operations.

    Handles CRUD operations for node execution history.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(
        self,
        run_id: int,
        node_name: str,
        status: NodeExecutionStatus,
        iteration: int,
        execution_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> ExecutionLogModel:
        """
        Create execution log entry.

        Args:
            run_id: Database ID of run
            node_name: Name of executed node
            status: Execution status
            iteration: Iteration number
            execution_time_ms: Execution time in milliseconds
            error_message: Optional error message
            state_snapshot: Optional state snapshot

        Returns:
            Created ExecutionLogModel instance
        """
        log = ExecutionLogModel(
            run_id=run_id,
            node_name=node_name,
            status=status,
            iteration=iteration,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            state_snapshot=state_snapshot,
            timestamp=datetime.utcnow()
        )

        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)

        return log

    async def get_by_run_id(
        self,
        run_id: int,
        skip: int = 0,
        limit: int = 1000
    ) -> List[ExecutionLogModel]:
        """
        Get all execution logs for a run.

        Args:
            run_id: Database ID of run
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ExecutionLogModel instances ordered by timestamp
        """
        query = (
            select(ExecutionLogModel)
            .where(ExecutionLogModel.run_id == run_id)
            .order_by(ExecutionLogModel.timestamp)
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_run_and_node(
        self,
        run_id: int,
        node_name: str
    ) -> List[ExecutionLogModel]:
        """
        Get execution logs for specific node in a run.

        Args:
            run_id: Database ID of run
            node_name: Name of node

        Returns:
            List of ExecutionLogModel instances ordered by iteration
        """
        query = (
            select(ExecutionLogModel)
            .where(
                and_(
                    ExecutionLogModel.run_id == run_id,
                    ExecutionLogModel.node_name == node_name
                )
            )
            .order_by(ExecutionLogModel.iteration)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_by_run(self, run_id: int) -> int:
        """
        Delete all execution logs for a run.

        Args:
            run_id: Database ID of run

        Returns:
            Number of deleted records
        """
        result = await self.session.execute(
            delete(ExecutionLogModel).where(ExecutionLogModel.run_id == run_id)
        )
        return result.rowcount
