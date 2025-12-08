"""SQLAlchemy Database Models

Defines the database schema for workflow persistence:
- Graph: Workflow definitions
- Run: Workflow execution instances
- ExecutionLog: Node execution history
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Float,
    Enum as SQLEnum,
    Index,
    JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.types import TypeDecorator
import enum


class JSONType(TypeDecorator):
    """
    Cross-database JSON type that uses JSONB for PostgreSQL and JSON for other databases.

    This allows us to use JSONB's advanced features in production (PostgreSQL)
    while maintaining SQLite compatibility for testing.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class ExecutionStatus(enum.Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeExecutionStatus(enum.Enum):
    """Node execution status enumeration"""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class GraphModel(Base):
    """
    Graph model for storing workflow definitions.

    Stores the graph structure (nodes, edges, entry point) as JSON
    for flexibility and easy serialization.
    """
    __tablename__ = "graphs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Store graph structure as JSON
    definition = Column(JSONType, nullable=False)
    # definition contains: {nodes: [...], edges: [...], entry_point: "...", metadata: {...}}

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Integer, nullable=False, default=1)  # Using Integer as boolean for SQLite compatibility

    # Relationships
    runs = relationship("RunModel", back_populates="graph", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GraphModel(id={self.id}, name='{self.name}')>"


class RunModel(Base):
    """
    Run model for storing workflow execution instances.

    Each run represents one execution of a workflow graph with
    its initial state, final state, and execution status.
    """
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(255), nullable=False, unique=True, index=True)

    # Foreign key to graph
    graph_id = Column(Integer, ForeignKey("graphs.id"), nullable=False, index=True)

    # Execution status
    status = Column(
        SQLEnum(ExecutionStatus),
        nullable=False,
        default=ExecutionStatus.PENDING,
        index=True
    )

    # State storage (JSONB for flexibility)
    initial_state = Column(JSONType, nullable=False)
    final_state = Column(JSONType, nullable=True)
    current_state = Column(JSONType, nullable=True)  # For resumable workflows

    # Execution metadata
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Performance metrics
    total_execution_time_ms = Column(Float, nullable=True)
    total_iterations = Column(Integer, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    graph = relationship("GraphModel", back_populates="runs")
    execution_logs = relationship("ExecutionLogModel", back_populates="run", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_run_status_created', 'status', 'created_at'),
        Index('idx_run_graph_status', 'graph_id', 'status'),
    )

    def __repr__(self) -> str:
        return f"<RunModel(id={self.id}, run_id='{self.run_id}', status='{self.status.value}')>"


class ExecutionLogModel(Base):
    """
    Execution log model for storing node execution history.

    Tracks each node execution with status, timing, and error information.
    Enables workflow replay, debugging, and performance analysis.
    """
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to run
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)

    # Node information
    node_name = Column(String(255), nullable=False, index=True)
    status = Column(
        SQLEnum(NodeExecutionStatus),
        nullable=False,
        index=True
    )

    # Execution details
    iteration = Column(Integer, nullable=False, default=0)
    execution_time_ms = Column(Float, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Optional: Store state snapshot at this point (can be large)
    state_snapshot = Column(JSONType, nullable=True)

    # Relationships
    run = relationship("RunModel", back_populates="execution_logs")

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_log_run_timestamp', 'run_id', 'timestamp'),
        Index('idx_log_run_node', 'run_id', 'node_name'),
    )

    def __repr__(self) -> str:
        return f"<ExecutionLogModel(id={self.id}, run_id={self.run_id}, node='{self.node_name}', status='{self.status.value}')>"
