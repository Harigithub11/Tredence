"""Pytest configuration and fixtures"""

import pytest
import asyncio

# Import database components only if they exist (for Phase 3+)
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import sessionmaker
    from app.database.models import Base
    HAS_DATABASE = True
except (ImportError, ModuleNotFoundError):
    HAS_DATABASE = False


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    """Create test database engine (in-memory SQLite)"""
    if not HAS_DATABASE:
        pytest.skip("Database components not yet implemented")

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create test database session"""
    if not HAS_DATABASE:
        pytest.skip("Database components not yet implemented")

    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def sample_graph_data():
    """Sample graph data for testing"""
    return {
        "name": "test_workflow",
        "description": "Test workflow for unit tests",
        "nodes": [
            {"name": "node_a", "tool": "test_tool_a"},
            {"name": "node_b", "tool": "test_tool_b"}
        ],
        "edges": [
            {"from": "node_a", "to": "node_b"}
        ],
        "entry_point": "node_a"
    }


@pytest.fixture
def sample_code():
    """Sample Python code for code review testing"""
    return """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def very_long_function_without_docstring(a, b, c, d, e, f, g, h):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return f + g + h
    return 0
"""
