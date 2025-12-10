# Agent Workflow Engine - Implementation Phases

**Project**: Mini-LangGraph Workflow Engine with Code Review Demo
**Deadline**: December 11th, 2025
**Goal**: Production-ready backend assignment demonstrating Python, API design, and async programming

---

## 📊 Project Overview

This document breaks down the implementation into 7 phases, each with clear tasks, subtasks, and validation criteria.

**Total Estimated Time**: 7 days
**Submission Date**: December 11th, 2025

---

## Phase 1: Project Setup & Core Infrastructure (Day 1)

**Duration**: 4-6 hours
**Goal**: Set up project structure, dependencies, and basic configuration

### Tasks

#### 1.1 Project Initialization
**Subtasks:**
- [ ] Create project directory structure
- [ ] Initialize Git repository
- [ ] Create `.gitignore` for Python projects
- [ ] Set up virtual environment

**Commands:**
```bash
mkdir agent-workflow-engine
cd agent-workflow-engine
git init
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 1.2 Dependency Management
**Subtasks:**
- [ ] Create `requirements.txt` with core dependencies
- [ ] Create `requirements-dev.txt` for development tools
- [ ] Install all dependencies

**requirements.txt:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.0
python-dotenv==1.0.0
python-multipart==0.0.6
websockets==12.0
google-generativeai==0.3.2
```

**requirements-dev.txt:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.12.0
flake8==6.1.0
mypy==1.7.1
httpx==0.25.2
```

#### 1.3 Environment Configuration
**Subtasks:**
- [ ] Create `.env.example` file
- [ ] Create `app/config.py` for Pydantic settings
- [ ] Document all environment variables

**.env.example:**
```
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/workflow_engine

# Application
APP_NAME=Agent Workflow Engine
DEBUG=True
LOG_LEVEL=INFO

# LLM (Optional - for future enhancements)
ENABLE_LLM=False
GEMINI_API_KEY=your_api_key_here

# API
API_V1_PREFIX=/api/v1
MAX_CONCURRENT_RUNS=10
```

#### 1.4 Database Setup
**Subtasks:**
- [ ] Create `docker-compose.yml` for PostgreSQL
- [ ] Start PostgreSQL container
- [ ] Verify database connection

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: workflow_engine_db
    environment:
      POSTGRES_USER: workflow_user
      POSTGRES_PASSWORD: workflow_pass
      POSTGRES_DB: workflow_engine
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Validation Checklist

- [ ] Project structure matches architecture document
- [ ] All dependencies install without errors
- [ ] PostgreSQL container starts and accepts connections
- [ ] `.env` file created from `.env.example`
- [ ] Virtual environment activated
- [ ] Git repository initialized with first commit

**Success Criteria:**
```bash
# These commands should work:
pip list  # Shows all installed packages
docker-compose ps  # Shows postgres running
python -c "from app.config import settings; print(settings.APP_NAME)"  # Prints app name
```

---

## Phase 2: Core Workflow Engine (Day 1-2)

**Duration**: 8-10 hours
**Goal**: Build the core graph execution engine with nodes, edges, state management

### Tasks

#### 2.1 State Management (`app/core/state.py`)
**Subtasks:**
- [ ] Create `WorkflowState` base class (Pydantic)
- [ ] Implement state serialization/deserialization
- [ ] Add state validation
- [ ] Create state snapshot functionality

**Key Features:**
- Pydantic model for type safety
- JSON serialization for PostgreSQL storage
- Immutable state updates (copy-on-write)
- State history tracking

**Code Structure:**
```python
from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime

class WorkflowState(BaseModel):
    """Base state model that flows through workflow nodes"""
    # Core fields
    workflow_id: str
    run_id: str
    timestamp: datetime
    iteration: int = 0

    # User data (flexible schema)
    data: Dict[str, Any] = {}

    # Execution metadata
    errors: list[str] = []
    warnings: list[str] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}
```

#### 2.2 Node Implementation (`app/core/node.py`)
**Subtasks:**
- [ ] Create `Node` base class
- [ ] Implement `SyncNode` for synchronous functions
- [ ] Implement `AsyncNode` for async functions
- [ ] Add node execution logging
- [ ] Implement error handling in nodes

**Key Features:**
- Support both sync and async functions
- Automatic state passing
- Error capture and propagation
- Execution timing
- Node metadata (name, description, version)

**Code Structure:**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Callable
import asyncio
from datetime import datetime

class Node(ABC):
    """Base node class"""
    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func
        self.execution_count = 0

    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute node and return updated state"""
        pass

class AsyncNode(Node):
    """Async node wrapper"""
    async def execute(self, state: WorkflowState) -> WorkflowState:
        # Execute async function
        # Log execution
        # Handle errors
        pass

class SyncNode(Node):
    """Sync node wrapper (runs in thread pool)"""
    async def execute(self, state: WorkflowState) -> WorkflowState:
        # Run sync function in executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.func, state)
        return result
```

#### 2.3 Edge & Routing (`app/core/edge.py`)
**Subtasks:**
- [ ] Create `Edge` class for node connections
- [ ] Implement conditional routing
- [ ] Add edge validation
- [ ] Support branching logic

**Key Features:**
- Simple edges: `{"node_a": "node_b"}`
- Conditional edges: `{"node_a": condition_func -> "node_b" or "node_c"}`
- Special edges: `START`, `END`
- Edge validation (no cycles, all nodes exist)

**Code Structure:**
```python
from typing import Callable, Optional, Union

class Edge:
    """Edge connecting two nodes"""
    def __init__(
        self,
        from_node: str,
        to_node: str,
        condition: Optional[Callable] = None
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.condition = condition

    async def should_traverse(self, state: WorkflowState) -> bool:
        """Check if this edge should be traversed"""
        if self.condition is None:
            return True
        return await self.condition(state)

class ConditionalRouter:
    """Routes to different nodes based on state"""
    def __init__(self, routes: Dict[str, Callable]):
        self.routes = routes  # {"node_name": condition_func}

    async def route(self, state: WorkflowState) -> str:
        """Determine next node based on state"""
        for node_name, condition in self.routes.items():
            if await condition(state):
                return node_name
        raise ValueError("No matching route found")
```

#### 2.4 Graph Definition (`app/core/graph.py`)
**Subtasks:**
- [ ] Create `Graph` class
- [ ] Implement graph validation
- [ ] Add node registration
- [ ] Support edge definition
- [ ] Implement graph serialization

**Key Features:**
- Programmatic graph construction
- Graph validation (DAG check, reachability)
- JSON serialization for storage
- Graph visualization support (optional)

**Code Structure:**
```python
from typing import Dict, List, Optional
import json

class Graph:
    """Workflow graph definition"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, node: Node):
        """Register a node"""
        self.nodes[name] = node

    def add_edge(self, from_node: str, to_node: str, condition=None):
        """Add edge between nodes"""
        edge = Edge(from_node, to_node, condition)
        self.edges.append(edge)

    def set_entry_point(self, node_name: str):
        """Set starting node"""
        self.entry_point = node_name

    def validate(self) -> bool:
        """Validate graph structure"""
        # Check all nodes referenced in edges exist
        # Check for unreachable nodes
        # Check entry point is set
        pass

    def to_dict(self) -> Dict:
        """Serialize to JSON-compatible dict"""
        return {
            "name": self.name,
            "description": self.description,
            "nodes": [name for name in self.nodes.keys()],
            "edges": [
                {
                    "from": edge.from_node,
                    "to": edge.to_node,
                    "has_condition": edge.condition is not None
                }
                for edge in self.edges
            ],
            "entry_point": self.entry_point
        }
```

#### 2.5 Workflow Engine (`app/core/engine.py`)
**Subtasks:**
- [ ] Create `WorkflowEngine` class
- [ ] Implement graph execution
- [ ] Add loop detection and max iterations
- [ ] Support conditional branching
- [ ] Implement execution logging
- [ ] Add error recovery

**Key Features:**
- Execute graphs with state management
- Support loops with max iteration limits
- Conditional branching
- Execution logging at each step
- Graceful error handling
- Timeout support

**Code Structure:**
```python
from typing import Optional
import asyncio
from datetime import datetime

class WorkflowEngine:
    """Core workflow execution engine"""
    def __init__(self, max_iterations: int = 100):
        self.max_iterations = max_iterations
        self.execution_log: List[Dict] = []

    async def execute(
        self,
        graph: Graph,
        initial_state: WorkflowState,
        timeout: Optional[float] = None
    ) -> WorkflowState:
        """Execute workflow graph"""

        # Validate graph
        if not graph.validate():
            raise ValueError("Invalid graph")

        # Initialize state
        state = initial_state
        current_node_name = graph.entry_point
        iterations = 0

        # Execution loop
        while current_node_name and iterations < self.max_iterations:
            # Get node
            node = graph.nodes.get(current_node_name)
            if not node:
                raise ValueError(f"Node not found: {current_node_name}")

            # Log execution start
            self._log_execution(current_node_name, "started", state)

            try:
                # Execute node
                state = await node.execute(state)
                state.iteration = iterations

                # Log execution complete
                self._log_execution(current_node_name, "completed", state)

            except Exception as e:
                # Log error
                self._log_execution(current_node_name, "failed", state, error=str(e))
                raise

            # Determine next node
            current_node_name = await self._get_next_node(
                graph, current_node_name, state
            )

            iterations += 1

        if iterations >= self.max_iterations:
            raise RuntimeError("Max iterations exceeded")

        return state

    async def _get_next_node(
        self, graph: Graph, current_node: str, state: WorkflowState
    ) -> Optional[str]:
        """Determine next node to execute"""

        # Find outgoing edges
        outgoing_edges = [
            edge for edge in graph.edges
            if edge.from_node == current_node
        ]

        if not outgoing_edges:
            return None  # End of workflow

        # Check conditional edges
        for edge in outgoing_edges:
            if await edge.should_traverse(state):
                return edge.to_node

        return None  # No matching edge

    def _log_execution(
        self, node_name: str, status: str, state: WorkflowState, error: str = None
    ):
        """Log node execution"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "node": node_name,
            "status": status,
            "iteration": state.iteration,
            "error": error
        }
        self.execution_log.append(log_entry)
```

#### 2.6 Tool Registry (`app/core/registry.py`)
**Subtasks:**
- [ ] Create `ToolRegistry` class
- [ ] Implement decorator for tool registration
- [ ] Add tool discovery
- [ ] Support tool metadata

**Key Features:**
- Decorator-based registration: `@registry.tool()`
- Tool metadata (name, description, parameters)
- Dynamic tool discovery
- Tool versioning support

**Code Structure:**
```python
from typing import Callable, Dict, Any
from functools import wraps

class ToolRegistry:
    """Registry for workflow tools/functions"""
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict] = {}

    def tool(self, name: str = None, description: str = ""):
        """Decorator to register a tool"""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            self.metadata[tool_name] = {
                "description": description,
                "function": func.__name__,
                "is_async": asyncio.iscoroutinefunction(func)
            }

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def get_tool(self, name: str) -> Callable:
        """Retrieve a registered tool"""
        if name not in self.tools:
            raise KeyError(f"Tool not found: {name}")
        return self.tools[name]

    def list_tools(self) -> Dict[str, Dict]:
        """List all registered tools with metadata"""
        return self.metadata

# Global registry instance
registry = ToolRegistry()
```

### Validation Checklist

- [ ] Can create a `WorkflowState` and serialize it to JSON
- [ ] Can create sync and async nodes
- [ ] Can define edges with and without conditions
- [ ] Can build a simple graph programmatically
- [ ] Can execute a simple 2-node workflow
- [ ] Engine stops at max iterations
- [ ] Execution log captures all node executions
- [ ] Tool registry can register and retrieve tools
- [ ] Error in node execution is caught and logged

**Success Criteria:**

Create and run this test:
```python
# test_core_engine.py
import asyncio
from app.core.state import WorkflowState
from app.core.node import AsyncNode
from app.core.graph import Graph
from app.core.engine import WorkflowEngine

async def test_simple_workflow():
    # Define nodes
    async def node_a(state: WorkflowState) -> WorkflowState:
        state.data["count"] = 1
        return state

    async def node_b(state: WorkflowState) -> WorkflowState:
        state.data["count"] += 1
        return state

    # Build graph
    graph = Graph("test_workflow")
    graph.add_node("a", AsyncNode("a", node_a))
    graph.add_node("b", AsyncNode("b", node_b))
    graph.add_edge("a", "b")
    graph.set_entry_point("a")

    # Execute
    engine = WorkflowEngine()
    initial_state = WorkflowState(
        workflow_id="test",
        run_id="run_1",
        timestamp=datetime.utcnow()
    )

    final_state = await engine.execute(graph, initial_state)

    # Validate
    assert final_state.data["count"] == 2
    assert len(engine.execution_log) == 2
    print("✓ Core engine test passed")

# Run test
asyncio.run(test_simple_workflow())
```

---

## Phase 3: Database Layer (Day 2)

**Duration**: 4-5 hours
**Goal**: Set up PostgreSQL models, migrations, and repositories

### Tasks

#### 3.1 SQLAlchemy Models (`app/database/models.py`)
**Subtasks:**
- [ ] Create `Base` declarative base
- [ ] Define `Graph` model
- [ ] Define `Run` model
- [ ] Define `ExecutionLog` model
- [ ] Add relationships and indexes

**Models:**

**Graph Model:**
```python
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Graph(Base):
    __tablename__ = "graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

    # Graph structure (JSON)
    nodes = Column(JSON, nullable=False)  # List of node names
    edges = Column(JSON, nullable=False)  # List of edge definitions
    entry_point = Column(String(255), nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    runs = relationship("Run", back_populates="graph", cascade="all, delete-orphan")
```

**Run Model:**
```python
class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("graphs.id"), nullable=False)

    # Execution state
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    initial_state = Column(JSON, nullable=False)
    current_state = Column(JSON)
    final_state = Column(JSON)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Error tracking
    error = Column(Text)

    # Relationships
    graph = relationship("Graph", back_populates="runs")
    logs = relationship("ExecutionLog", back_populates="run", cascade="all, delete-orphan")
```

**ExecutionLog Model:**
```python
class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False)

    # Log details
    node_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # started, completed, failed
    timestamp = Column(DateTime, default=datetime.utcnow)

    # State snapshots
    input_state = Column(JSON)
    output_state = Column(JSON)

    # Error details
    error = Column(Text)

    # Relationships
    run = relationship("Run", back_populates="logs")

    # Index for fast queries
    __table_args__ = (
        Index("idx_run_timestamp", "run_id", "timestamp"),
    )
```

#### 3.2 Database Connection (`app/database/connection.py`)
**Subtasks:**
- [ ] Create async engine factory
- [ ] Implement session management
- [ ] Add connection pooling
- [ ] Create database initialization function

**Code Structure:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    """Dependency for FastAPI"""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

#### 3.3 Repository Layer (`app/database/repositories.py`)
**Subtasks:**
- [ ] Create `GraphRepository`
- [ ] Create `RunRepository`
- [ ] Create `ExecutionLogRepository`
- [ ] Implement CRUD operations
- [ ] Add query helpers

**GraphRepository:**
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

class GraphRepository:
    """Repository for graph operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, graph_data: dict) -> Graph:
        """Create new graph"""
        graph = Graph(**graph_data)
        self.session.add(graph)
        await self.session.commit()
        await self.session.refresh(graph)
        return graph

    async def get_by_id(self, graph_id: uuid.UUID) -> Optional[Graph]:
        """Get graph by ID"""
        result = await self.session.execute(
            select(Graph).where(Graph.id == graph_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Graph]:
        """Get graph by name"""
        result = await self.session.execute(
            select(Graph).where(Graph.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Graph]:
        """List all graphs"""
        result = await self.session.execute(select(Graph))
        return result.scalars().all()

    async def delete(self, graph_id: uuid.UUID) -> bool:
        """Delete graph"""
        graph = await self.get_by_id(graph_id)
        if graph:
            await self.session.delete(graph)
            await self.session.commit()
            return True
        return False
```

**RunRepository:**
```python
class RunRepository:
    """Repository for run operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, run_data: dict) -> Run:
        """Create new run"""
        run = Run(**run_data)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_by_id(self, run_id: uuid.UUID) -> Optional[Run]:
        """Get run by ID with logs"""
        result = await self.session.execute(
            select(Run)
            .where(Run.id == run_id)
            .options(selectinload(Run.logs))
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, run_id: uuid.UUID, status: str, **kwargs
    ) -> Optional[Run]:
        """Update run status"""
        run = await self.get_by_id(run_id)
        if run:
            run.status = status
            for key, value in kwargs.items():
                setattr(run, key, value)
            await self.session.commit()
            await self.session.refresh(run)
        return run

    async def update_state(
        self, run_id: uuid.UUID, current_state: dict
    ) -> Optional[Run]:
        """Update current state"""
        run = await self.get_by_id(run_id)
        if run:
            run.current_state = current_state
            await self.session.commit()
            await self.session.refresh(run)
        return run
```

#### 3.4 Alembic Migrations
**Subtasks:**
- [ ] Initialize Alembic
- [ ] Create initial migration
- [ ] Test migration up/down
- [ ] Document migration process

**Commands:**
```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Validation Checklist

- [ ] Database tables created successfully
- [ ] Can create and retrieve a Graph
- [ ] Can create and retrieve a Run
- [ ] Can create ExecutionLog entries
- [ ] Foreign key relationships work correctly
- [ ] Alembic migrations run without errors
- [ ] Can rollback and re-apply migrations
- [ ] Connection pooling works (multiple concurrent connections)
- [ ] Session management doesn't leak connections

**Success Criteria:**

Run these tests:
```python
# test_database.py
import asyncio
from app.database.connection import AsyncSessionLocal, init_db
from app.database.repositories import GraphRepository, RunRepository

async def test_database():
    # Initialize DB
    await init_db()

    # Test graph creation
    async with AsyncSessionLocal() as session:
        graph_repo = GraphRepository(session)

        graph = await graph_repo.create({
            "name": "test_graph",
            "description": "Test workflow",
            "nodes": ["node_a", "node_b"],
            "edges": [{"from": "node_a", "to": "node_b"}],
            "entry_point": "node_a"
        })

        print(f"✓ Created graph: {graph.id}")

        # Test run creation
        run_repo = RunRepository(session)
        run = await run_repo.create({
            "graph_id": graph.id,
            "initial_state": {"data": {}}
        })

        print(f"✓ Created run: {run.id}")

        # Test retrieval
        fetched_graph = await graph_repo.get_by_id(graph.id)
        assert fetched_graph.name == "test_graph"
        print("✓ Database layer test passed")

asyncio.run(test_database())
```

---

## Phase 4: FastAPI Layer (Day 3)

**Duration**: 6-8 hours
**Goal**: Implement REST API endpoints and WebSocket streaming

### Tasks

#### 4.1 API Models (`app/api/models.py`)
**Subtasks:**
- [ ] Create request models (Pydantic)
- [ ] Create response models (Pydantic)
- [ ] Add validation rules
- [ ] Document models with examples

**Request Models:**
```python
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional

class NodeDefinition(BaseModel):
    """Node definition in graph creation"""
    name: str = Field(..., description="Unique node name")
    tool: str = Field(..., description="Tool/function to execute")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "extract_functions",
                "tool": "extract_code_functions"
            }
        }

class EdgeDefinition(BaseModel):
    """Edge definition connecting nodes"""
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    condition: Optional[str] = Field(None, description="Conditional routing function")

    class Config:
        json_schema_extra = {
            "example": {
                "from": "node_a",
                "to": "node_b",
                "condition": None
            }
        }

class CreateGraphRequest(BaseModel):
    """Request to create a new workflow graph"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field("", max_length=1000)
    nodes: List[NodeDefinition] = Field(..., min_items=1)
    edges: List[EdgeDefinition] = Field(..., min_items=0)
    entry_point: str = Field(..., description="Starting node name")

    @validator("entry_point")
    def validate_entry_point(cls, v, values):
        """Ensure entry_point exists in nodes"""
        if "nodes" in values:
            node_names = [node.name for node in values["nodes"]]
            if v not in node_names:
                raise ValueError(f"Entry point '{v}' not found in nodes")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "code_review_workflow",
                "description": "Analyzes code quality",
                "nodes": [
                    {"name": "extract", "tool": "extract_functions"},
                    {"name": "analyze", "tool": "calculate_complexity"}
                ],
                "edges": [
                    {"from": "extract", "to": "analyze"}
                ],
                "entry_point": "extract"
            }
        }

class RunGraphRequest(BaseModel):
    """Request to execute a workflow"""
    graph_id: str = Field(..., description="Graph UUID")
    initial_state: Dict[str, Any] = Field(..., description="Initial workflow state")
    timeout: Optional[int] = Field(None, ge=1, le=3600, description="Timeout in seconds")
    use_llm: bool = Field(False, description="Enable LLM features")

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "550e8400-e29b-41d4-a716-446655440000",
                "initial_state": {
                    "code": "def hello(): pass"
                },
                "timeout": 300,
                "use_llm": False
            }
        }
```

**Response Models:**
```python
from datetime import datetime
from typing import List, Optional

class GraphResponse(BaseModel):
    """Response after graph creation"""
    graph_id: str
    name: str
    description: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "code_review_workflow",
                "description": "Analyzes code quality",
                "created_at": "2025-12-08T10:30:00Z"
            }
        }

class ExecutionLogEntry(BaseModel):
    """Single execution log entry"""
    timestamp: datetime
    node: str
    status: str  # started, completed, failed
    iteration: int
    error: Optional[str] = None

class RunResponse(BaseModel):
    """Response after workflow execution"""
    run_id: str
    graph_id: str
    status: str  # pending, running, completed, failed
    started_at: datetime
    completed_at: Optional[datetime]
    initial_state: Dict[str, Any]
    final_state: Optional[Dict[str, Any]]
    execution_log: List[ExecutionLogEntry]
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "660e8400-e29b-41d4-a716-446655440000",
                "graph_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "started_at": "2025-12-08T10:35:00Z",
                "completed_at": "2025-12-08T10:35:05Z",
                "initial_state": {"code": "def hello(): pass"},
                "final_state": {"code": "def hello(): pass", "quality_score": 85},
                "execution_log": [
                    {
                        "timestamp": "2025-12-08T10:35:01Z",
                        "node": "extract",
                        "status": "completed",
                        "iteration": 0,
                        "error": None
                    }
                ],
                "error": None
            }
        }

class StateResponse(BaseModel):
    """Response for state query"""
    run_id: str
    status: str
    current_state: Optional[Dict[str, Any]]
    last_updated: datetime
```

#### 4.2 Graph Routes (`app/api/routes/graph.py`)
**Subtasks:**
- [ ] Implement `POST /graph/create`
- [ ] Implement `POST /graph/run`
- [ ] Implement `GET /graph/state/{run_id}`
- [ ] Implement `GET /graph/{graph_id}`
- [ ] Implement `DELETE /graph/{graph_id}`
- [ ] Add proper error handling

**Endpoints:**
```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db_session
from app.database.repositories import GraphRepository, RunRepository
from app.api.models import *
from app.core.engine import WorkflowEngine
import uuid

router = APIRouter(prefix="/graph", tags=["graphs"])

@router.post("/create", response_model=GraphResponse, status_code=201)
async def create_graph(
    request: CreateGraphRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new workflow graph.

    **Parameters:**
    - name: Unique workflow name
    - nodes: List of node definitions
    - edges: List of edge connections
    - entry_point: Starting node

    **Returns:**
    - graph_id: UUID for the created graph
    - created_at: Timestamp
    """
    graph_repo = GraphRepository(session)

    # Check if name already exists
    existing = await graph_repo.get_by_name(request.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Graph with name '{request.name}' already exists"
        )

    # Create graph
    graph = await graph_repo.create({
        "name": request.name,
        "description": request.description,
        "nodes": [node.dict() for node in request.nodes],
        "edges": [edge.dict(by_alias=True) for edge in request.edges],
        "entry_point": request.entry_point
    })

    return GraphResponse(
        graph_id=str(graph.id),
        name=graph.name,
        description=graph.description,
        created_at=graph.created_at
    )

@router.post("/run", response_model=RunResponse, status_code=202)
async def run_graph(
    request: RunGraphRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Execute a workflow graph.

    **Parameters:**
    - graph_id: UUID of the graph to execute
    - initial_state: Starting state for the workflow
    - timeout: Maximum execution time in seconds

    **Returns:**
    - run_id: UUID for this execution
    - status: Current execution status
    """
    graph_repo = GraphRepository(session)
    run_repo = RunRepository(session)

    # Validate graph exists
    graph_id = uuid.UUID(request.graph_id)
    graph = await graph_repo.get_by_id(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    # Create run record
    run = await run_repo.create({
        "graph_id": graph_id,
        "initial_state": request.initial_state,
        "status": "pending"
    })

    # Execute workflow in background
    background_tasks.add_task(
        execute_workflow_background,
        run.id,
        graph,
        request.initial_state,
        request.timeout
    )

    return RunResponse(
        run_id=str(run.id),
        graph_id=str(graph.id),
        status="pending",
        started_at=run.started_at or datetime.utcnow(),
        completed_at=None,
        initial_state=request.initial_state,
        final_state=None,
        execution_log=[],
        error=None
    )

@router.get("/state/{run_id}", response_model=StateResponse)
async def get_run_state(
    run_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get current state of a running or completed workflow.

    **Parameters:**
    - run_id: UUID of the workflow run

    **Returns:**
    - Current state and execution status
    """
    run_repo = RunRepository(session)

    run_uuid = uuid.UUID(run_id)
    run = await run_repo.get_by_id(run_uuid)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return StateResponse(
        run_id=str(run.id),
        status=run.status,
        current_state=run.current_state or run.final_state,
        last_updated=run.updated_at or run.created_at
    )

@router.get("/{graph_id}", response_model=GraphResponse)
async def get_graph(
    graph_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get graph details by ID"""
    graph_repo = GraphRepository(session)

    graph_uuid = uuid.UUID(graph_id)
    graph = await graph_repo.get_by_id(graph_uuid)

    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    return GraphResponse(
        graph_id=str(graph.id),
        name=graph.name,
        description=graph.description,
        created_at=graph.created_at
    )
```

#### 4.3 WebSocket Streaming (`app/api/websocket.py`)
**Subtasks:**
- [ ] Create WebSocket endpoint
- [ ] Implement real-time log streaming
- [ ] Add connection management
- [ ] Handle disconnections gracefully

**WebSocket Implementation:**
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, run_id: str, websocket: WebSocket):
        """Accept new connection"""
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = set()
        self.active_connections[run_id].add(websocket)

    def disconnect(self, run_id: str, websocket: WebSocket):
        """Remove connection"""
        if run_id in self.active_connections:
            self.active_connections[run_id].discard(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]

    async def broadcast(self, run_id: str, message: dict):
        """Broadcast message to all clients watching this run"""
        if run_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)

            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(run_id, connection)

manager = ConnectionManager()

@router.websocket("/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for real-time execution logs.

    **Usage:**
    ```javascript
    const ws = new WebSocket(`ws://localhost:8000/api/v1/graph/ws/${run_id}`);
    ws.onmessage = (event) => {
        const log = JSON.parse(event.data);
        console.log(log);
    };
    ```
    """
    await manager.connect(run_id, websocket)

    try:
        # Keep connection alive and send periodic updates
        while True:
            # Wait for new log entries from database
            async with AsyncSessionLocal() as session:
                run_repo = RunRepository(session)
                run = await run_repo.get_by_id(uuid.UUID(run_id))

                if run and run.logs:
                    latest_log = run.logs[-1]
                    await websocket.send_json({
                        "type": "log",
                        "timestamp": latest_log.timestamp.isoformat(),
                        "node": latest_log.node_name,
                        "status": latest_log.status,
                        "error": latest_log.error
                    })

                # Send completion message
                if run and run.status in ["completed", "failed"]:
                    await websocket.send_json({
                        "type": "complete",
                        "status": run.status,
                        "final_state": run.final_state
                    })
                    break

            await asyncio.sleep(0.5)  # Poll every 500ms

    except WebSocketDisconnect:
        manager.disconnect(run_id, websocket)
```

#### 4.4 Background Task Executor
**Subtasks:**
- [ ] Implement async workflow execution
- [ ] Update run status in database
- [ ] Save execution logs
- [ ] Handle errors gracefully

**Background Executor:**
```python
from app.core.engine import WorkflowEngine
from app.core.graph import Graph
from app.workflows.loader import WorkflowLoader

async def execute_workflow_background(
    run_id: uuid.UUID,
    graph_db: Graph,
    initial_state: dict,
    timeout: Optional[int]
):
    """Execute workflow in background task"""
    async with AsyncSessionLocal() as session:
        run_repo = RunRepository(session)

        try:
            # Update status to running
            await run_repo.update_status(
                run_id,
                "running",
                started_at=datetime.utcnow()
            )

            # Load workflow definition
            loader = WorkflowLoader()
            graph = await loader.build_graph(graph_db)

            # Create initial state
            from app.core.state import WorkflowState
            state = WorkflowState(
                workflow_id=str(graph_db.id),
                run_id=str(run_id),
                timestamp=datetime.utcnow(),
                data=initial_state
            )

            # Execute workflow
            engine = WorkflowEngine()
            final_state = await asyncio.wait_for(
                engine.execute(graph, state),
                timeout=timeout
            )

            # Save logs to database
            for log_entry in engine.execution_log:
                log_repo = ExecutionLogRepository(session)
                await log_repo.create({
                    "run_id": run_id,
                    "node_name": log_entry["node"],
                    "status": log_entry["status"],
                    "timestamp": datetime.fromisoformat(log_entry["timestamp"]),
                    "error": log_entry.get("error")
                })

            # Update to completed
            await run_repo.update_status(
                run_id,
                "completed",
                final_state=final_state.dict(),
                completed_at=datetime.utcnow()
            )

        except asyncio.TimeoutError:
            await run_repo.update_status(
                run_id,
                "failed",
                error="Execution timeout",
                completed_at=datetime.utcnow()
            )
        except Exception as e:
            await run_repo.update_status(
                run_id,
                "failed",
                error=str(e),
                completed_at=datetime.utcnow()
            )
```

#### 4.5 Main FastAPI App (`app/main.py`)
**Subtasks:**
- [ ] Initialize FastAPI app
- [ ] Add middleware (CORS, logging)
- [ ] Register routers
- [ ] Add startup/shutdown events
- [ ] Configure OpenAPI docs

**Main App:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import graph
from app.database.connection import init_db, engine
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A minimal workflow engine for agent orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(graph.router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logging.info("Initializing database...")
    await init_db()
    logging.info("Database initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logging.info("Shutting down...")
    await engine.dispose()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agent Workflow Engine API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

### Validation Checklist

- [ ] Can create a graph via POST /graph/create
- [ ] Can execute a graph via POST /graph/run
- [ ] Can query run state via GET /graph/state/{run_id}
- [ ] WebSocket connects and receives messages
- [ ] Background tasks execute workflows
- [ ] Execution logs saved to database
- [ ] API documentation accessible at /docs
- [ ] CORS headers present in responses
- [ ] Error responses follow consistent format
- [ ] All endpoints return proper status codes

**Success Criteria:**

Test with curl:
```bash
# 1. Create graph
curl -X POST http://localhost:8000/api/v1/graph/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_workflow",
    "description": "Test",
    "nodes": [{"name": "node_a", "tool": "test_tool"}],
    "edges": [],
    "entry_point": "node_a"
  }'

# Should return: {"graph_id": "...", "name": "test_workflow", ...}

# 2. Run graph (use graph_id from above)
curl -X POST http://localhost:8000/api/v1/graph/run \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "<graph_id>",
    "initial_state": {"data": {}}
  }'

# Should return: {"run_id": "...", "status": "pending", ...}

# 3. Check state (use run_id from above)
curl http://localhost:8000/api/v1/graph/state/<run_id>

# Should return: {"run_id": "...", "status": "running" or "completed", ...}

# 4. Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

---

## Phase 5: Code Review Workflow (Day 4-5)

**Duration**: 10-12 hours
**Goal**: Implement hybrid code review workflow with rule-based and LLM components

### Tasks

#### 5.1 Code Analysis Tools (`app/workflows/code_review/tools.py`)
**Subtasks:**
- [ ] Implement function extraction (AST-based)
- [ ] Calculate cyclomatic complexity
- [ ] Detect code issues (rule-based)
- [ ] Generate improvement suggestions (rules)
- [ ] Calculate quality score

**Function Extraction:**
```python
import ast
from typing import List, Dict, Any

def extract_functions(code: str) -> List[Dict[str, Any]]:
    """
    Extract all function definitions from Python code.

    Returns list of:
    - name: function name
    - lineno: line number
    - args: argument list
    - docstring: function docstring (if any)
    - body_lines: number of lines in function body
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Extract function info
            func_info = {
                "name": node.name,
                "lineno": node.lineno,
                "args": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node),
                "body_lines": len(node.body),
                "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
            }
            functions.append(func_info)

    return functions

def calculate_cyclomatic_complexity(code: str) -> Dict[str, int]:
    """
    Calculate cyclomatic complexity for each function.

    Complexity = 1 + number of decision points (if, for, while, and, or, except)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}

    complexity_map = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            complexity = 1  # Base complexity

            # Count decision points
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    # Each 'and'/'or' adds complexity
                    complexity += len(child.values) - 1

            complexity_map[node.name] = complexity

    return complexity_map

def detect_issues(code: str, functions: List[Dict]) -> List[Dict[str, Any]]:
    """
    Detect code quality issues using static analysis.

    Checks for:
    - Long functions (> 50 lines)
    - Missing docstrings
    - Deep nesting (> 4 levels)
    - Too many arguments (> 5)
    - Complex functions (complexity > 10)
    """
    issues = []

    # Parse code
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        issues.append({
            "severity": "error",
            "type": "syntax_error",
            "message": str(e),
            "line": e.lineno if hasattr(e, 'lineno') else 0
        })
        return issues

    for func in functions:
        # Check function length
        if func["body_lines"] > 50:
            issues.append({
                "severity": "warning",
                "type": "long_function",
                "function": func["name"],
                "line": func["lineno"],
                "message": f"Function '{func['name']}' is too long ({func['body_lines']} lines)"
            })

        # Check for docstring
        if not func["docstring"]:
            issues.append({
                "severity": "info",
                "type": "missing_docstring",
                "function": func["name"],
                "line": func["lineno"],
                "message": f"Function '{func['name']}' lacks docstring"
            })

        # Check argument count
        if len(func["args"]) > 5:
            issues.append({
                "severity": "warning",
                "type": "too_many_args",
                "function": func["name"],
                "line": func["lineno"],
                "message": f"Function '{func['name']}' has {len(func['args'])} arguments"
            })

    # Check nesting depth
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            max_depth = calculate_nesting_depth(node)
            if max_depth > 4:
                issues.append({
                    "severity": "warning",
                    "type": "deep_nesting",
                    "function": node.name,
                    "line": node.lineno,
                    "message": f"Function '{node.name}' has deep nesting (depth {max_depth})"
                })

    return issues

def calculate_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Calculate maximum nesting depth in AST node"""
    max_depth = current_depth

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
            child_depth = calculate_nesting_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = calculate_nesting_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)

    return max_depth

def generate_suggestions(issues: List[Dict], complexity: Dict[str, int]) -> List[str]:
    """
    Generate improvement suggestions based on detected issues.
    """
    suggestions = []

    # Group issues by type
    issue_types = {}
    for issue in issues:
        issue_type = issue["type"]
        if issue_type not in issue_types:
            issue_types[issue_type] = []
        issue_types[issue_type].append(issue)

    # Generate suggestions
    if "long_function" in issue_types:
        funcs = [i["function"] for i in issue_types["long_function"]]
        suggestions.append(
            f"Break down long functions: {', '.join(funcs)}. "
            "Consider splitting into smaller, focused functions."
        )

    if "missing_docstring" in issue_types:
        count = len(issue_types["missing_docstring"])
        suggestions.append(
            f"Add docstrings to {count} function(s). "
            "Document parameters, return values, and purpose."
        )

    if "deep_nesting" in issue_types:
        funcs = [i["function"] for i in issue_types["deep_nesting"]]
        suggestions.append(
            f"Reduce nesting in: {', '.join(funcs)}. "
            "Consider early returns, guard clauses, or extracting methods."
        )

    if "too_many_args" in issue_types:
        funcs = [i["function"] for i in issue_types["too_many_args"]]
        suggestions.append(
            f"Reduce parameters in: {', '.join(funcs)}. "
            "Consider using dataclasses, **kwargs, or configuration objects."
        )

    # Complexity-based suggestions
    complex_funcs = [name for name, comp in complexity.items() if comp > 10]
    if complex_funcs:
        suggestions.append(
            f"High complexity in: {', '.join(complex_funcs)}. "
            "Simplify logic, extract conditions, or split into smaller functions."
        )

    return suggestions

def calculate_quality_score(issues: List[Dict], complexity: Dict[str, int]) -> float:
    """
    Calculate overall quality score (0-100).

    Scoring:
    - Start at 100
    - Deduct points for each issue based on severity
    - Deduct points for high complexity
    """
    score = 100.0

    # Deduct for issues
    severity_weights = {
        "error": 20,
        "warning": 5,
        "info": 2
    }

    for issue in issues:
        severity = issue.get("severity", "info")
        score -= severity_weights.get(severity, 2)

    # Deduct for complexity
    avg_complexity = sum(complexity.values()) / len(complexity) if complexity else 0
    if avg_complexity > 10:
        score -= (avg_complexity - 10) * 2

    # Clamp to 0-100
    return max(0.0, min(100.0, score))
```

#### 5.2 LLM Tools (Optional) (`app/workflows/code_review/llm_tools.py`)
**Subtasks:**
- [ ] Implement Gemini client wrapper
- [ ] Create code analysis prompt
- [ ] Parse LLM suggestions
- [ ] Add error handling

**LLM Integration:**
```python
from typing import List, Dict, Optional
import google.generativeai as genai
from app.config import settings

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

CODE_REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following Python code and provide specific, actionable improvement suggestions.

**Code:**
```python
{code}
```

**Detected Issues:**
{issues}

**Complexity Metrics:**
{complexity}

Please provide:
1. **Critical Issues**: Security, bugs, or logical errors
2. **Code Quality**: Readability, maintainability improvements
3. **Best Practices**: Pythonic patterns, design principles
4. **Refactoring Ideas**: Structural improvements

Keep suggestions concise and actionable. Focus on the most impactful changes.
"""

async def analyze_with_llm(
    code: str,
    issues: List[Dict],
    complexity: Dict[str, int]
) -> Dict[str, Any]:
    """
    Use Gemini to generate advanced code suggestions.
    """
    if not settings.ENABLE_LLM or not settings.GEMINI_API_KEY:
        return {
            "llm_suggestions": [],
            "analysis": "LLM analysis disabled"
        }

    try:
        # Format prompt
        issues_str = "\n".join([
            f"- [{i['severity'].upper()}] {i['message']}"
            for i in issues[:10]  # Limit to top 10
        ])

        complexity_str = "\n".join([
            f"- {func}: complexity {comp}"
            for func, comp in sorted(
                complexity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]  # Top 5 most complex
        ])

        prompt = CODE_REVIEW_PROMPT.format(
            code=code[:2000],  # Limit code length
            issues=issues_str or "No issues detected",
            complexity=complexity_str or "No complexity data"
        )

        # Call Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for consistent analysis
                max_output_tokens=1000
            )
        )

        # Parse response
        analysis_text = response.text

        # Extract sections
        sections = {}
        current_section = None

        for line in analysis_text.split('\n'):
            if line.startswith('**') and line.endswith('**'):
                current_section = line.strip('*').strip(':').lower()
                sections[current_section] = []
            elif current_section and line.strip():
                sections[current_section].append(line.strip())

        return {
            "llm_suggestions": sections.get("refactoring ideas", []),
            "critical_issues": sections.get("critical issues", []),
            "quality_tips": sections.get("code quality", []),
            "best_practices": sections.get("best practices", []),
            "raw_analysis": analysis_text
        }

    except Exception as e:
        return {
            "llm_suggestions": [],
            "error": str(e)
        }
```

#### 5.3 Workflow Nodes (`app/workflows/code_review/nodes.py`)
**Subtasks:**
- [ ] Create `extract_functions_node`
- [ ] Create `calculate_complexity_node`
- [ ] Create `detect_issues_node`
- [ ] Create `suggest_improvements_node` (hybrid)
- [ ] Create `check_quality_node`

**Node Implementations:**
```python
from app.core.state import WorkflowState
from app.core.registry import registry
from app.workflows.code_review.tools import *
from app.workflows.code_review.llm_tools import analyze_with_llm

@registry.tool(name="extract_functions", description="Extract function definitions from code")
async def extract_functions_node(state: WorkflowState) -> WorkflowState:
    """Extract all functions from the provided code"""
    code = state.data.get("code", "")

    if not code:
        state.errors.append("No code provided")
        return state

    # Extract functions
    functions = extract_functions(code)
    state.data["functions"] = functions
    state.data["function_count"] = len(functions)

    return state

@registry.tool(name="calculate_complexity", description="Calculate cyclomatic complexity")
async def calculate_complexity_node(state: WorkflowState) -> WorkflowState:
    """Calculate complexity metrics for all functions"""
    code = state.data.get("code", "")

    # Calculate complexity
    complexity = calculate_cyclomatic_complexity(code)
    state.data["complexity"] = complexity

    # Calculate average
    if complexity:
        avg_complexity = sum(complexity.values()) / len(complexity)
        state.data["avg_complexity"] = round(avg_complexity, 2)

    return state

@registry.tool(name="detect_issues", description="Detect code quality issues")
async def detect_issues_node(state: WorkflowState) -> WorkflowState:
    """Detect code quality issues using static analysis"""
    code = state.data.get("code", "")
    functions = state.data.get("functions", [])

    # Detect issues
    issues = detect_issues(code, functions)
    state.data["issues"] = issues
    state.data["issue_count"] = len(issues)

    # Categorize by severity
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    infos = [i for i in issues if i["severity"] == "info"]

    state.data["errors"] = len(errors)
    state.data["warnings"] = len(warnings)
    state.data["infos"] = len(infos)

    return state

@registry.tool(name="suggest_improvements", description="Generate improvement suggestions")
async def suggest_improvements_node(state: WorkflowState) -> WorkflowState:
    """Generate improvement suggestions (hybrid: rules + LLM)"""
    code = state.data.get("code", "")
    issues = state.data.get("issues", [])
    complexity = state.data.get("complexity", {})
    use_llm = state.data.get("use_llm", False)

    # Rule-based suggestions (always run)
    rule_suggestions = generate_suggestions(issues, complexity)
    state.data["rule_suggestions"] = rule_suggestions

    # LLM suggestions (optional)
    if use_llm:
        llm_result = await analyze_with_llm(code, issues, complexity)
        state.data["llm_suggestions"] = llm_result.get("llm_suggestions", [])
        state.data["llm_analysis"] = llm_result.get("raw_analysis", "")

        # Combine suggestions
        all_suggestions = rule_suggestions + llm_result.get("llm_suggestions", [])
        state.data["suggestions"] = all_suggestions
    else:
        state.data["suggestions"] = rule_suggestions

    return state

@registry.tool(name="check_quality", description="Calculate quality score and determine if loop should continue")
async def check_quality_node(state: WorkflowState) -> WorkflowState:
    """Calculate quality score and check loop condition"""
    issues = state.data.get("issues", [])
    complexity = state.data.get("complexity", {})

    # Calculate quality score
    quality_score = calculate_quality_score(issues, complexity)
    state.data["quality_score"] = quality_score

    # Determine pass/fail
    threshold = state.data.get("quality_threshold", 70)
    state.data["quality_pass"] = quality_score >= threshold

    return state
```

#### 5.4 Workflow Definition (`app/workflows/code_review/workflow.py`)
**Subtasks:**
- [ ] Define workflow graph
- [ ] Add conditional routing
- [ ] Implement loop logic
- [ ] Register workflow

**Workflow Graph:**
```python
from app.core.graph import Graph
from app.core.node import AsyncNode
from app.core.edge import Edge
from app.workflows.code_review.nodes import *

def create_code_review_workflow() -> Graph:
    """
    Create Code Review workflow graph.

    Workflow:
    1. Extract functions
    2. Calculate complexity
    3. Detect issues
    4. Suggest improvements (hybrid: rules + optional LLM)
    5. Check quality
    6. Loop if quality < threshold (max 3 iterations)
    """
    graph = Graph(
        name="code_review",
        description="Hybrid code review workflow with optional LLM enhancement"
    )

    # Register nodes
    graph.add_node("extract", AsyncNode("extract", extract_functions_node))
    graph.add_node("complexity", AsyncNode("complexity", calculate_complexity_node))
    graph.add_node("detect", AsyncNode("detect", detect_issues_node))
    graph.add_node("suggest", AsyncNode("suggest", suggest_improvements_node))
    graph.add_node("check", AsyncNode("check", check_quality_node))

    # Define edges
    graph.add_edge("extract", "complexity")
    graph.add_edge("complexity", "detect")
    graph.add_edge("detect", "suggest")
    graph.add_edge("suggest", "check")

    # Conditional edge: loop if quality fails and iteration < 3
    async def should_loop(state: WorkflowState) -> bool:
        """Check if we should loop for another iteration"""
        quality_pass = state.data.get("quality_pass", False)
        iteration = state.iteration
        max_iterations = 3

        # Loop if quality failed and haven't exceeded max iterations
        return not quality_pass and iteration < max_iterations

    # Add conditional routing from check node
    graph.add_edge("check", "suggest", condition=should_loop)

    # Set entry point
    graph.set_entry_point("extract")

    return graph

# Example usage
async def run_code_review(code: str, use_llm: bool = False) -> WorkflowState:
    """Helper function to run code review workflow"""
    from app.core.engine import WorkflowEngine
    from datetime import datetime

    # Create workflow
    graph = create_code_review_workflow()

    # Create initial state
    state = WorkflowState(
        workflow_id="code_review",
        run_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        data={
            "code": code,
            "use_llm": use_llm,
            "quality_threshold": 70
        }
    )

    # Execute
    engine = WorkflowEngine(max_iterations=5)
    final_state = await engine.execute(graph, state)

    return final_state
```

#### 5.5 Workflow Loader (`app/workflows/loader.py`)
**Subtasks:**
- [ ] Create workflow loader from database
- [ ] Map tools to registered functions
- [ ] Build graph dynamically
- [ ] Validate workflow

**Loader Implementation:**
```python
from app.core.graph import Graph
from app.core.node import AsyncNode
from app.core.registry import registry
from app.database.models import Graph as GraphModel

class WorkflowLoader:
    """Load workflows from database definitions"""

    async def build_graph(self, graph_model: GraphModel) -> Graph:
        """Build executable graph from database model"""
        graph = Graph(
            name=graph_model.name,
            description=graph_model.description
        )

        # Add nodes
        for node_def in graph_model.nodes:
            node_name = node_def["name"]
            tool_name = node_def["tool"]

            # Get tool function from registry
            tool_func = registry.get_tool(tool_name)

            # Create node
            node = AsyncNode(node_name, tool_func)
            graph.add_node(node_name, node)

        # Add edges
        for edge_def in graph_model.edges:
            from_node = edge_def["from"]
            to_node = edge_def["to"]
            condition = edge_def.get("condition")

            # TODO: Handle conditional edges
            # For now, simple edges only
            graph.add_edge(from_node, to_node)

        # Set entry point
        graph.set_entry_point(graph_model.entry_point)

        return graph
```

### Validation Checklist

- [ ] Can extract functions from sample Python code
- [ ] Cyclomatic complexity calculated correctly
- [ ] Issues detected for problematic code
- [ ] Rule-based suggestions generated
- [ ] LLM suggestions work (if enabled)
- [ ] Quality score calculated properly
- [ ] Loop executes when quality < threshold
- [ ] Loop stops at max iterations
- [ ] Workflow completes for good code (1 iteration)
- [ ] Workflow completes for bad code (3 iterations)
- [ ] All nodes registered in tool registry
- [ ] Workflow can be created via API
- [ ] Workflow can be executed via API

**Success Criteria:**

Test with sample code:
```python
# test_code_review.py
import asyncio
from app.workflows.code_review.workflow import run_code_review

# Bad code example (should loop)
bad_code = """
def very_long_function_without_docstring(a, b, c, d, e, f, g):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return f + g
    for i in range(100):
        for j in range(100):
            if i == j:
                print(i)
    return None
"""

# Good code example (should pass)
good_code = """
def calculate_sum(numbers: List[int]) -> int:
    \"\"\"Calculate sum of a list of numbers.

    Args:
        numbers: List of integers

    Returns:
        Sum of all numbers
    \"\"\"
    return sum(numbers)
"""

async def test_workflows():
    # Test bad code
    print("Testing bad code...")
    result = await run_code_review(bad_code, use_llm=False)
    print(f"Quality Score: {result.data['quality_score']}")
    print(f"Iterations: {result.iteration}")
    print(f"Suggestions: {len(result.data['suggestions'])}")
    assert result.data['quality_score'] < 70

    # Test good code
    print("\nTesting good code...")
    result = await run_code_review(good_code, use_llm=False)
    print(f"Quality Score: {result.data['quality_score']}")
    print(f"Iterations: {result.iteration}")
    assert result.data['quality_score'] >= 70
    assert result.iteration == 0  # Should pass in first iteration

    print("\n✓ Code review workflow tests passed")

asyncio.run(test_workflows())
```

---

## Phase 6: Testing & Error Handling (Day 6)

**Duration**: 6-8 hours
**Goal**: Comprehensive testing and production-grade error handling

### Tasks

#### 6.1 Unit Tests
**Subtasks:**
- [ ] Test core engine components
- [ ] Test database operations
- [ ] Test API endpoints
- [ ] Test code review tools
- [ ] Achieve >80% code coverage

**Test Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_core/
│   ├── test_state.py
│   ├── test_node.py
│   ├── test_graph.py
│   ├── test_engine.py
│   └── test_registry.py
├── test_database/
│   ├── test_models.py
│   └── test_repositories.py
├── test_api/
│   ├── test_graph_routes.py
│   └── test_websocket.py
└── test_workflows/
    └── test_code_review.py
```

**Example Tests:**
```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.models import Base

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()

# tests/test_core/test_engine.py
import pytest
from app.core.engine import WorkflowEngine
from app.core.graph import Graph
from app.core.node import AsyncNode
from app.core.state import WorkflowState
from datetime import datetime

@pytest.mark.asyncio
async def test_simple_workflow_execution():
    """Test basic workflow execution"""
    # Define nodes
    async def node_a(state: WorkflowState) -> WorkflowState:
        state.data["step"] = "a"
        return state

    async def node_b(state: WorkflowState) -> WorkflowState:
        state.data["step"] = "b"
        return state

    # Build graph
    graph = Graph("test")
    graph.add_node("a", AsyncNode("a", node_a))
    graph.add_node("b", AsyncNode("b", node_b))
    graph.add_edge("a", "b")
    graph.set_entry_point("a")

    # Execute
    engine = WorkflowEngine()
    state = WorkflowState(
        workflow_id="test",
        run_id="1",
        timestamp=datetime.utcnow()
    )

    result = await engine.execute(graph, state)

    assert result.data["step"] == "b"
    assert len(engine.execution_log) == 2

@pytest.mark.asyncio
async def test_conditional_branching():
    """Test conditional edge routing"""
    async def node_a(state: WorkflowState) -> WorkflowState:
        state.data["value"] = 10
        return state

    async def node_b(state: WorkflowState) -> WorkflowState:
        state.data["path"] = "high"
        return state

    async def node_c(state: WorkflowState) -> WorkflowState:
        state.data["path"] = "low"
        return state

    async def condition_high(state: WorkflowState) -> bool:
        return state.data.get("value", 0) > 5

    # Build graph
    graph = Graph("conditional")
    graph.add_node("a", AsyncNode("a", node_a))
    graph.add_node("b", AsyncNode("b", node_b))
    graph.add_node("c", AsyncNode("c", node_c))
    graph.add_edge("a", "b", condition=condition_high)
    graph.add_edge("a", "c", condition=lambda s: s.data.get("value", 0) <= 5)
    graph.set_entry_point("a")

    # Execute
    engine = WorkflowEngine()
    state = WorkflowState(
        workflow_id="test",
        run_id="1",
        timestamp=datetime.utcnow()
    )

    result = await engine.execute(graph, state)

    assert result.data["path"] == "high"

@pytest.mark.asyncio
async def test_loop_execution():
    """Test loop with max iterations"""
    async def increment_node(state: WorkflowState) -> WorkflowState:
        state.data["count"] = state.data.get("count", 0) + 1
        return state

    async def check_node(state: WorkflowState) -> WorkflowState:
        return state

    async def should_loop(state: WorkflowState) -> bool:
        return state.data.get("count", 0) < 3

    # Build graph with loop
    graph = Graph("loop")
    graph.add_node("increment", AsyncNode("increment", increment_node))
    graph.add_node("check", AsyncNode("check", check_node))
    graph.add_edge("increment", "check")
    graph.add_edge("check", "increment", condition=should_loop)
    graph.set_entry_point("increment")

    # Execute
    engine = WorkflowEngine(max_iterations=10)
    state = WorkflowState(
        workflow_id="test",
        run_id="1",
        timestamp=datetime.utcnow()
    )

    result = await engine.execute(graph, state)

    assert result.data["count"] == 3

@pytest.mark.asyncio
async def test_max_iterations_exceeded():
    """Test that workflow stops at max iterations"""
    async def infinite_node(state: WorkflowState) -> WorkflowState:
        return state

    # Build infinite loop
    graph = Graph("infinite")
    graph.add_node("loop", AsyncNode("loop", infinite_node))
    graph.add_edge("loop", "loop")  # Loop to itself
    graph.set_entry_point("loop")

    # Execute with low max iterations
    engine = WorkflowEngine(max_iterations=5)
    state = WorkflowState(
        workflow_id="test",
        run_id="1",
        timestamp=datetime.utcnow()
    )

    with pytest.raises(RuntimeError, match="Max iterations exceeded"):
        await engine.execute(graph, state)

# tests/test_api/test_graph_routes.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_graph():
    """Test graph creation endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/graph/create", json={
            "name": "test_workflow",
            "description": "Test",
            "nodes": [
                {"name": "node_a", "tool": "test_tool"}
            ],
            "edges": [],
            "entry_point": "node_a"
        })

    assert response.status_code == 201
    data = response.json()
    assert "graph_id" in data
    assert data["name"] == "test_workflow"

@pytest.mark.asyncio
async def test_create_duplicate_graph():
    """Test that duplicate graph names are rejected"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create first graph
        await client.post("/api/v1/graph/create", json={
            "name": "duplicate",
            "nodes": [{"name": "a", "tool": "test"}],
            "edges": [],
            "entry_point": "a"
        })

        # Try to create duplicate
        response = await client.post("/api/v1/graph/create", json={
            "name": "duplicate",
            "nodes": [{"name": "b", "tool": "test"}],
            "edges": [],
            "entry_point": "b"
        })

    assert response.status_code == 400
```

#### 6.2 Integration Tests
**Subtasks:**
- [ ] Test end-to-end workflows
- [ ] Test API → Database → Engine flow
- [ ] Test WebSocket streaming
- [ ] Test error scenarios

#### 6.3 Error Handling & Logging
**Subtasks:**
- [ ] Add custom exception classes
- [ ] Implement error middleware
- [ ] Add structured logging
- [ ] Log all workflow executions

**Custom Exceptions (`app/utils/exceptions.py`):**
```python
class WorkflowException(Exception):
    """Base exception for workflow errors"""
    pass

class NodeExecutionError(WorkflowException):
    """Raised when node execution fails"""
    def __init__(self, node_name: str, message: str):
        self.node_name = node_name
        super().__init__(f"Node '{node_name}' failed: {message}")

class GraphValidationError(WorkflowException):
    """Raised when graph structure is invalid"""
    pass

class ToolNotFoundError(WorkflowException):
    """Raised when requested tool doesn't exist"""
    pass
```

**Logging Setup (`app/utils/logging.py`):**
```python
import logging
import sys
from datetime import datetime

def setup_logging(level: str = "INFO"):
    """Configure structured logging"""

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)

    return root_logger

# Workflow execution logger
class WorkflowLogger:
    """Structured logging for workflow execution"""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.logger = logging.getLogger(f"workflow.{run_id}")

    def log_node_start(self, node_name: str):
        self.logger.info(f"[{self.run_id}] Starting node: {node_name}")

    def log_node_complete(self, node_name: str, duration_ms: float):
        self.logger.info(
            f"[{self.run_id}] Completed node: {node_name} "
            f"(duration: {duration_ms:.2f}ms)"
        )

    def log_node_error(self, node_name: str, error: str):
        self.logger.error(
            f"[{self.run_id}] Error in node: {node_name} - {error}"
        )
```

### Validation Checklist

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Test coverage >80%
- [ ] All endpoints have error handling
- [ ] Custom exceptions used throughout
- [ ] Structured logging implemented
- [ ] Error responses consistent
- [ ] All async operations have timeouts
- [ ] Database transactions rolled back on error
- [ ] WebSocket errors handled gracefully

**Success Criteria:**
```bash
# Run all tests
pytest tests/ -v --cov=app --cov-report=html

# Should see:
# - All tests passing
# - Coverage >80%
# - Coverage report in htmlcov/index.html
```

---

## Phase 7: Documentation & Polish (Day 7)

**Duration**: 4-6 hours
**Goal**: Production-ready documentation and final polish

### Tasks

#### 7.1 README.md
**Subtasks:**
- [ ] Project overview
- [ ] Features list
- [ ] Installation instructions
- [ ] API documentation
- [ ] Usage examples
- [ ] Architecture overview
- [ ] Future enhancements

**README Structure:**
```markdown
# Agent Workflow Engine

A production-ready workflow orchestration engine for building multi-agent systems.

## Features

- **Graph-based Workflows**: Define workflows as directed graphs
- **Async Execution**: Fully async/await support
- **State Management**: Type-safe state with Pydantic
- **Conditional Branching**: Route based on state conditions
- **Looping**: Built-in loop support with max iterations
- **Tool Registry**: Decorator-based tool registration
- **REST API**: FastAPI endpoints for graph management
- **WebSocket Streaming**: Real-time execution logs
- **PostgreSQL Persistence**: Durable state storage
- **Hybrid LLM Support**: Optional Gemini integration

## Quick Start

1. **Clone repository**
2. **Install dependencies**
3. **Start PostgreSQL**
4. **Run application**
5. **Access API docs**

## API Examples

[Include curl examples]

## Architecture

[Include architecture diagram]

## Running Tests

```bash
pytest tests/ -v
```

## Future Enhancements

- Financial analysis workflow
- Redis caching layer
- Rate limiting
- Authentication
```

#### 7.2 API Documentation
**Subtasks:**
- [ ] Document all endpoints
- [ ] Add request/response examples
- [ ] Include error codes
- [ ] Add usage guides

#### 7.3 Code Documentation
**Subtasks:**
- [ ] Add docstrings to all functions
- [ ] Add type hints everywhere
- [ ] Add inline comments for complex logic
- [ ] Generate API docs

#### 7.4 Docker Setup
**Subtasks:**
- [ ] Create Dockerfile
- [ ] Update docker-compose.yml
- [ ] Add docker instructions
- [ ] Test docker deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Run migrations and start app
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 7.5 Final Polish
**Subtasks:**
- [ ] Code formatting (black)
- [ ] Linting (flake8)
- [ ] Type checking (mypy)
- [ ] Remove debug code
- [ ] Final testing

**Commands:**
```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/ --max-line-length=100

# Type check
mypy app/ --ignore-missing-imports

# Final test run
pytest tests/ -v --cov=app
```

### Validation Checklist

- [ ] README is comprehensive and clear
- [ ] All code has docstrings
- [ ] API docs are complete
- [ ] Docker build succeeds
- [ ] Docker container runs successfully
- [ ] Code is formatted consistently
- [ ] No linting errors
- [ ] Type hints are correct
- [ ] All tests still pass
- [ ] Project is ready for submission

**Success Criteria:**

Final checklist:
```bash
# 1. Code quality
black --check app/ tests/
flake8 app/ tests/
mypy app/

# 2. Tests
pytest tests/ -v --cov=app
# Coverage should be >80%

# 3. Docker
docker-compose up -d
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# 4. API
curl http://localhost:8000/docs
# Should show Swagger UI

# 5. Git
git status
# Should show clean working directory
```

---

## 🔮 Optional: Future Enhancement Prep (If Time Permits)

**Duration**: 2-4 hours (only if ahead of schedule)
**Goal**: Set up infrastructure for future enhancements

### Tasks

#### LLM Infrastructure
- [ ] Create `app/llm/` directory structure
- [ ] Implement Gemini client wrapper
- [ ] Add prompt templates
- [ ] Document LLM integration patterns

#### Financial Analysis Skeleton
- [ ] Create `app/workflows/financial_analysis/` directory
- [ ] Add placeholder nodes
- [ ] Document workflow design
- [ ] Add to README as future enhancement

#### Redis Caching
- [ ] Add Redis to docker-compose.yml
- [ ] Create cache client wrapper
- [ ] Add cache decorator
- [ ] Document caching strategy

---

## 📊 Success Metrics

Track these metrics throughout implementation:

### Code Quality
- [ ] Test coverage >80%
- [ ] No critical linting errors
- [ ] All functions have type hints
- [ ] All public APIs documented

### Performance
- [ ] Simple workflow completes in <100ms
- [ ] Complex workflow completes in <5s
- [ ] API response time <200ms
- [ ] Database queries optimized (no N+1)

### Functionality
- [ ] All assignment requirements met
- [ ] Code review workflow fully functional
- [ ] All API endpoints working
- [ ] WebSocket streaming operational
- [ ] Error handling comprehensive

### Documentation
- [ ] README complete
- [ ] API docs generated
- [ ] Code comments clear
- [ ] Examples provided

---

## 🚨 Risk Mitigation

### Common Pitfalls & Solutions

**Pitfall 1**: Database migrations fail
- **Solution**: Test migrations early, keep backups

**Pitfall 2**: Async code causes deadlocks
- **Solution**: Use proper async/await, test concurrency

**Pitfall 3**: Graph validation misses edge cases
- **Solution**: Write comprehensive validation tests

**Pitfall 4**: Time runs out before completion
- **Solution**: Prioritize core features, skip optional enhancements

**Pitfall 5**: Code becomes too complex
- **Solution**: Keep it simple, refactor early

---

## 📅 Daily Checklist

Use this for daily standup/review:

### End of Day 1
- [ ] Project structure complete
- [ ] Core engine functional
- [ ] Basic tests passing

### End of Day 2
- [ ] Database layer working
- [ ] Migrations successful
- [ ] Repository tests passing

### End of Day 3
- [ ] API endpoints operational
- [ ] WebSocket streaming works
- [ ] Can create and run workflows

### End of Day 4
- [ ] Code review workflow complete
- [ ] Rule-based analysis working
- [ ] Quality scoring functional

### End of Day 5
- [ ] LLM integration optional
- [ ] Workflow fully tested
- [ ] Integration tests passing

### End of Day 6
- [ ] All tests passing
- [ ] Error handling comprehensive
- [ ] Logging implemented

### End of Day 7
- [ ] Documentation complete
- [ ] Docker working
- [ ] Ready for submission

---

## 🎯 Submission Checklist

Before submitting on December 11th:

### Code
- [ ] All code committed to Git
- [ ] No sensitive data in repository (.env in .gitignore)
- [ ] Requirements.txt up to date
- [ ] Code formatted and linted

### Documentation
- [ ] README.md complete
- [ ] API examples provided
- [ ] Architecture documented
- [ ] Setup instructions clear

### Testing
- [ ] All tests passing
- [ ] Coverage >80%
- [ ] Manual testing complete

### Deployment
- [ ] Docker build succeeds
- [ ] Docker-compose up works
- [ ] Application accessible

### Repository
- [ ] GitHub repo public
- [ ] Proper .gitignore
- [ ] Clear commit history
- [ ] README at root

### Submission Email
- [ ] Resume (PDF)
- [ ] GitHub link
- [ ] Portfolio links
- [ ] Brief cover note

---

## 📞 Support & Questions

If anything is unclear during implementation:
- Review phase validation checklists
- Check success criteria for each phase
- Refer to code examples in this document
- Test incrementally, don't wait until the end

**Remember**: Clean structure and correctness matter more than extra features!

Good luck! 🚀

---

# Phase 8: Future Enhancements & Roadmap

**Current Status**: Production Ready (166/166 tests passing, 79% coverage)
**Last Updated**: December 9, 2025

---

## 🎯 Immediate Enhancements (High Priority)

### 1. Complete API Test Coverage (48% → 90%+)

**Current Gap**: API routes only 48% covered
- Background task execution not fully tested
- WebSocket streaming needs integration tests
- Error scenarios in workflow execution

**Action Items**:
```python
# Add tests for:
- test_websocket_streaming()
- test_background_workflow_execution()
- test_workflow_timeout()
- test_concurrent_runs()
- test_database_transaction_failures()
```

**Effort**: 2-3 hours
**Impact**: High (improves reliability)

---

### 2. LLM Integration Test Suite (22% → 80%+)

**Current Gap**: LLM client only 22% covered (no tests with actual API)

**Action Items**:
```python
# Add tests with mocked Gemini responses:
- test_llm_code_analysis_success()
- test_llm_network_failure()
- test_llm_invalid_api_key()
- test_llm_rate_limiting()
- test_llm_response_parsing()
```

**Alternative**: Use pytest fixtures to mock `google.generativeai`

**Effort**: 2-3 hours
**Impact**: Medium (LLM is optional)

---

### 3. WebSocket Real-Time Updates

**Current State**: WebSocket endpoint exists but not fully tested

**Enhancement**:
```python
# Add structured message format:
{
    "type": "status_update",
    "run_id": "run_123",
    "status": "running",
    "current_node": "complexity",
    "progress": 40,  # percentage
    "timestamp": "2025-12-09T10:00:00Z"
}

{
    "type": "node_completed",
    "node_name": "extract",
    "duration_ms": 125,
    "output_preview": {"function_count": 3}
}

{
    "type": "workflow_completed",
    "final_state": {...},
    "total_duration_ms": 5230
}
```

**Effort**: 3-4 hours
**Impact**: High (great UX for real-time monitoring)

---

### 4. Frontend Dashboard (Optional but Recommended)

**Purpose**: Visualize workflow execution in real-time

**Stack Suggestion**:
- React + TypeScript
- TailwindCSS for styling
- WebSocket for live updates
- Chart.js for complexity visualization

**Features**:
```
┌─────────────────────────────────────────┐
│  Workflow Orchestration Dashboard      │
├─────────────────────────────────────────┤
│  [Create Graph] [Run Workflow]          │
│                                         │
│  Active Runs:                           │
│  ├─ run_123  [████████░░] 80%          │
│  │   Status: Running (complexity)      │
│  │   Started: 10 sec ago               │
│  │                                     │
│  └─ run_124  [██████████] Complete    │
│      Quality: 94/100                   │
│                                         │
│  Recent Analysis:                       │
│  ┌─────────────────────────────────┐  │
│  │ Time: O(n²) → O(n)              │  │
│  │ Space: O(n)                     │  │
│  │ Issues: 3 (0 errors, 0 warnings)│  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Effort**: 1-2 days
**Impact**: Very High (production-ready interface)

---

## 🚀 Advanced Features (Medium Priority)

### 5. Workflow Templates Library

**Purpose**: Pre-built workflows for common use cases

**Templates to Add**:
```python
# 1. Security Audit Workflow
create_security_audit_workflow()
# Nodes: detect_sql_injection, check_xss, validate_auth, scan_dependencies

# 2. Performance Analysis Workflow
create_performance_workflow()
# Nodes: profile_execution, detect_memory_leaks, check_db_queries, analyze_algorithms

# 3. Documentation Generator Workflow
create_doc_generator_workflow()
# Nodes: extract_api_endpoints, generate_openapi, create_readme, update_changelog

# 4. Test Coverage Workflow
create_test_coverage_workflow()
# Nodes: run_tests, calculate_coverage, identify_untested_code, suggest_test_cases

# 5. Dependency Update Workflow
create_dependency_workflow()
# Nodes: check_outdated, analyze_vulnerabilities, test_updates, create_pr
```

**Effort**: 1 day per template
**Impact**: High (makes system more useful out-of-box)

---

### 6. Multi-Language Support

**Current**: Only Python code analysis
**Enhancement**: Support JavaScript, TypeScript, Java, Go, Rust

**Implementation**:
```python
# Abstract the analyzer:
class CodeAnalyzer(ABC):
    @abstractmethod
    def extract_functions(self, code: str) -> List[Dict]

    @abstractmethod
    def calculate_complexity(self, code: str) -> Dict

# Concrete implementations:
class PythonAnalyzer(CodeAnalyzer):  # Already done
class JavaScriptAnalyzer(CodeAnalyzer):  # TODO
class TypeScriptAnalyzer(CodeAnalyzer):  # TODO
class JavaAnalyzer(CodeAnalyzer):  # TODO
```

**Effort**: 2-3 days per language
**Impact**: Very High (broader use cases)

---

### 7. Workflow Visualization & DAG Editor

**Purpose**: Visual graph builder (like LangGraph Studio)

**Features**:
- Drag-and-drop node creation
- Visual edge connections
- Conditional routing with UI
- Live execution preview
- Export to Python code

**Tech Stack**: React Flow / Cytoscape.js

**Example**:
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Extract  │────▶│Complexity│────▶│  Detect  │
└──────────┘     └──────────┘     └──────────┘
                                        │
                                        ▼
                   ┌──────────┐     ┌──────────┐
           ┌──────▶│ Suggest  │◀────│  Check   │
           │       └──────────┘     └──────────┘
           │            │                │
           └────────────┘           [quality_pass?]
              (loop if fail)             │
                                         ▼
                                      [END]
```

**Effort**: 3-4 days
**Impact**: Very High (no-code workflow builder)

---

### 8. Caching Layer with Redis

**Purpose**: Speed up repeated analyses

**Implementation**:
```python
# Cache complexity analysis results:
@cache_result(ttl=3600)  # 1 hour
async def analyze_code_complexity(code: str):
    # Generate hash of code
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Check cache
    cached = await redis.get(f"complexity:{code_hash}")
    if cached:
        return json.loads(cached)

    # Compute and cache
    result = ComplexityAnalyzer().analyze(code)
    await redis.set(f"complexity:{code_hash}", json.dumps(result), ex=3600)
    return result
```

**Benefits**:
- Instant results for repeated code
- Reduced Gemini API costs
- Better performance under load

**Effort**: 4-6 hours
**Impact**: Medium (nice optimization)

---

### 9. Scheduled Workflows & Cron Jobs

**Purpose**: Automate periodic code reviews

**Implementation**:
```python
# app/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=0)  # Daily at midnight
async def nightly_code_review():
    """Review all changed files in last 24 hours"""
    changed_files = await get_git_changes(since="24h")

    for file in changed_files:
        code = read_file(file)
        result = await run_code_review(code, use_llm=True)

        if result.data["quality_score"] < 70:
            await send_notification(
                channel="slack",
                message=f"⚠️ Code quality alert: {file} scored {result.data['quality_score']}/100"
            )
```

**Effort**: 1 day
**Impact**: High (automation!)

---

### 10. Multi-Model LLM Support

**Current**: Only Google Gemini
**Enhancement**: Support multiple LLM providers

**Implementation**:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def analyze_code(self, code, issues, complexity): pass

class GeminiProvider(LLMProvider):  # Current
    async def analyze_code(self, code, issues, complexity):
        # Existing implementation
        pass

class OpenAIProvider(LLMProvider):  # NEW
    async def analyze_code(self, code, issues, complexity):
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        # GPT-4 implementation
        pass

class ClaudeProvider(LLMProvider):  # NEW
    async def analyze_code(self, code, issues, complexity):
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        # Claude implementation
        pass

class LLMRouter:
    """Route to different LLM based on config"""
    def get_provider(self) -> LLMProvider:
        if settings.LLM_PROVIDER == "gemini":
            return GeminiProvider()
        elif settings.LLM_PROVIDER == "openai":
            return OpenAIProvider()
        elif settings.LLM_PROVIDER == "claude":
            return ClaudeProvider()
```

**Effort**: 1 day
**Impact**: Medium (flexibility, cost optimization)

---

## 🔧 Infrastructure Improvements (Low Priority but Important)

### 11. Docker Compose for Full Stack

**Current**: Manual setup
**Enhancement**: One-command deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/workflow_engine
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: workflow_engine
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api

volumes:
  postgres_data:
```

**Usage**:
```bash
docker-compose up -d
# Everything running!
```

**Effort**: 3-4 hours
**Impact**: High (easy deployment)

---

### 12. CI/CD Pipeline

**Purpose**: Automate testing and deployment

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest tests/ --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

      - name: Lint with ruff
        run: ruff check app/

      - name: Type check with mypy
        run: mypy app/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Deploy to AWS/GCP/Azure
```

**Effort**: 2-3 hours
**Impact**: High (quality assurance)

---

### 13. Monitoring & Observability

**Purpose**: Track system health and performance

**Tools**:
- Prometheus for metrics
- Grafana for dashboards
- Sentry for error tracking
- OpenTelemetry for tracing

**Implementation**:
```python
# app/monitoring.py
from prometheus_client import Counter, Histogram
import sentry_sdk

# Metrics
workflow_executions = Counter('workflow_executions_total', 'Total workflows executed')
workflow_duration = Histogram('workflow_duration_seconds', 'Workflow execution time')
llm_api_calls = Counter('llm_api_calls_total', 'LLM API calls')

# Initialize Sentry
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0
)

# Use in engine
@workflow_duration.time()
async def execute_workflow(graph, state):
    workflow_executions.inc()
    try:
        result = await engine.execute(graph, state)
        return result
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
```

**Effort**: 1 day
**Impact**: High (production monitoring)

---

### 14. Authentication & Authorization

**Current**: No auth (open API)
**Enhancement**: Secure endpoints with JWT

```python
# app/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return username
    except JWTError:
        raise HTTPException(status_code=401)

# Protect routes:
@app.post("/graph/run", dependencies=[Depends(get_current_user)])
async def run_graph(...):
    pass
```

**Effort**: 1 day
**Impact**: High (security)

---

### 15. Rate Limiting

**Purpose**: Prevent abuse, manage LLM costs

```python
# app/middleware.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/graph/run")
@limiter.limit("10/minute")  # Max 10 runs per minute
async def run_graph(...):
    pass
```

**Effort**: 2-3 hours
**Impact**: High (cost control)

---

## 📊 Analytics & Reporting

### 16. Workflow Analytics Dashboard

**Metrics to Track**:
- Total workflows executed
- Average execution time
- Success/failure rates
- Most used nodes
- Quality score trends over time
- LLM vs rule-based suggestion acceptance

**Implementation**:
```python
# Store analytics in database
class AnalyticsModel(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True)
    metric_name = Column(String)
    metric_value = Column(Float)
    timestamp = Column(DateTime)
    metadata = Column(JSON)

# Query endpoints:
@app.get("/analytics/summary")
async def get_analytics():
    return {
        "total_runs": await count_runs(),
        "avg_quality_score": await avg_quality(),
        "top_issues": await most_common_issues(),
        "execution_time_trend": await time_series_execution()
    }
```

**Effort**: 2 days
**Impact**: Medium (insights)

---

### 17. Code Quality Trends Report

**Purpose**: Track code quality improvements over time

```python
# Generate weekly reports:
{
    "period": "2025-W49",
    "files_analyzed": 156,
    "avg_quality_score": 87.5,  # Up from 82.3
    "trend": "improving",
    "top_improvements": [
        "Reduced O(n²) algorithms by 40%",
        "Added docstrings to 89% of functions",
        "Decreased average complexity from 8.2 to 5.7"
    ],
    "top_issues_remaining": [
        "Deep nesting (12 occurrences)",
        "Long functions (8 occurrences)"
    ]
}
```

**Effort**: 1 day
**Impact**: Medium (team motivation)

---

## 🎓 Documentation & Education

### 18. Interactive Tutorial

**Purpose**: Help users learn the system

**Features**:
- Step-by-step workflow creation
- Live code editor
- Real-time analysis preview
- Best practices guide

**Effort**: 2-3 days
**Impact**: High (user adoption)

---

### 19. API Documentation with Swagger UI

**Current**: Basic FastAPI docs
**Enhancement**: Rich, interactive documentation

```python
# Already have FastAPI's auto-generated docs at /docs
# Enhance with better descriptions:

@app.post(
    "/graph/run",
    summary="Execute a workflow",
    description="""
    Executes a workflow asynchronously.

    **Workflow Process:**
    1. Validates graph exists
    2. Creates workflow run record
    3. Executes in background
    4. Returns run_id for tracking

    **Example:**
    ```json
    {
      "graph_name": "code_review",
      "initial_state": {
        "code": "def foo(): pass",
        "quality_threshold": 70
      }
    }
    ```
    """,
    response_description="Run details with ID for tracking"
)
async def run_graph(...):
    pass
```

**Effort**: 4-6 hours
**Impact**: Medium (better DX)

---

## 🔮 Experimental / Research Ideas

### 20. AI-Powered Workflow Generation

**Concept**: Describe workflow in natural language, AI generates it

```python
# Input:
"Create a workflow that checks Python code for security issues,
measures complexity, and suggests fixes using AI"

# AI generates:
builder = GraphBuilder(name="security_workflow")
builder.node("scan_security", SecurityScanNode())
builder.node("check_complexity", ComplexityNode())
builder.node("ai_suggestions", LLMSuggestionNode())
builder.edge("scan_security", "check_complexity")
builder.edge("check_complexity", "ai_suggestions")
builder.entry("scan_security")
```

**Effort**: 1 week (research project)
**Impact**: Very High (innovation)

---

### 21. Collaborative Code Review

**Purpose**: Multi-user workflow execution with comments

**Features**:
- Multiple reviewers can add comments
- Vote on suggestions
- Real-time collaboration
- Review history

**Effort**: 1 week
**Impact**: High (team collaboration)

---

### 22. Machine Learning for Pattern Detection

**Purpose**: Learn from past code reviews to improve suggestions

```python
# Train ML model on:
# - Code that got high quality scores
# - Code that got low scores
# - Which suggestions were accepted/rejected

# Use to:
# - Predict quality score before analysis
# - Prioritize most impactful suggestions
# - Personalize suggestions per team/project
```

**Effort**: 2-3 weeks (research)
**Impact**: Very High (adaptive system)

---

## 📋 Prioritization Matrix

| Enhancement | Effort | Impact | Priority |
|------------|--------|--------|----------|
| WebSocket Real-Time Updates | Low | High | **P0** |
| API Test Coverage | Low | High | **P0** |
| Docker Compose | Low | High | **P0** |
| Frontend Dashboard | Med | Very High | **P1** |
| Workflow Templates | Med | High | **P1** |
| Authentication | Low | High | **P1** |
| CI/CD Pipeline | Low | High | **P1** |
| Multi-Language Support | High | Very High | **P2** |
| Visual DAG Editor | Med | Very High | **P2** |
| Monitoring & Observability | Med | High | **P2** |
| Redis Caching | Low | Med | **P3** |
| Multi-Model LLM | Low | Med | **P3** |
| AI Workflow Generation | Very High | Very High | **P4** (Research) |

---

## 🎯 Recommended Next Steps

**Week 1 (Production Hardening):**
1. Complete API test coverage (2-3 hours)
2. Add WebSocket real-time updates (3-4 hours)
3. Set up Docker Compose (3-4 hours)
4. Add authentication (1 day)
5. Set up CI/CD (2-3 hours)

**Week 2 (User Experience):**
1. Build frontend dashboard (2 days)
2. Add workflow templates (2-3 days)

**Week 3+ (Expansion):**
1. Multi-language support
2. Visual workflow editor
3. Advanced analytics

---

## 💡 Innovation Opportunities

1. **GitHub Integration**: Automatically review PRs
2. **IDE Plugins**: VS Code extension for live code review
3. **Slack/Discord Bots**: Code review via chat
4. **Browser Extension**: Review code on GitHub/GitLab
5. **Cloud Service**: SaaS offering of the platform

---

**Questions to Consider:**
1. What's the primary use case? (Team code review vs. learning tool vs. CI/CD integration)
2. Self-hosted or SaaS?
3. Free tier + paid features?
4. Target audience? (Individual devs, teams, enterprises)

These decisions will guide which enhancements to prioritize!
