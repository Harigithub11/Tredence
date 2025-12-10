"""Test configuration for API tests"""

import pytest
import os
import tempfile

# Create a named temporary SQLite file for tests (not in-memory)
# This ensures all connections share the same database
test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
test_db_path = test_db_file.name
test_db_file.close()

# Set test database URL BEFORE any imports that load settings
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db_path}"

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.connection import init_db, drop_db, close_db


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Set up test database once for all tests"""
    # Close any existing connections
    await close_db()

    # Initialize test database
    await init_db()

    yield

    # Cleanup
    await drop_db()
    await close_db()

    # Remove temp file
    import os as os_module
    try:
        os_module.unlink(test_db_path)
    except:
        pass


@pytest.fixture
async def test_client(setup_test_database):
    """Create test client with /api/v1 prefix for API endpoints"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        yield client


@pytest.fixture
async def root_client(setup_test_database):
    """Create test client for root-level endpoints (health, root)"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
