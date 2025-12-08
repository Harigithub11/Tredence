"""FastAPI Application

Main application entry point with routes and WebSocket support.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import (
    init_db,
    close_db,
    check_database_connection,
    get_session
)
from app.database.repositories import RunRepository, ExecutionLogRepository
from app.api.routes import graph
from app.api.models import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.

    Handles startup and shutdown events.
    """
    # Startup
    if settings.DEBUG:
        print("🚀 Starting FastAPI application...")
        print(f"📊 Database: {settings.DATABASE_URL}")

    # Initialize database in development (in production, use Alembic migrations)
    if settings.DEBUG and "sqlite" in settings.DATABASE_URL:
        await init_db()
        print("✅ Database initialized")

    yield

    # Shutdown
    if settings.DEBUG:
        print("🛑 Shutting down FastAPI application...")

    await close_db()
    if settings.DEBUG:
        print("✅ Database connections closed")


app = FastAPI(
    title="Workflow Orchestration Engine",
    description="Mini-LangGraph workflow execution engine with database persistence",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware for development
if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(graph.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Workflow Orchestration Engine API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns application status and database connectivity.
    """
    db_healthy = await check_database_connection()

    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        database=db_healthy,
        timestamp=datetime.utcnow()
    )


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, run_id: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)

    def disconnect(self, websocket: WebSocket, run_id: str):
        """Remove a WebSocket connection"""
        if run_id in self.active_connections:
            self.active_connections[run_id].remove(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]

    async def send_message(self, run_id: str, message: dict):
        """Send message to all connections for a run_id"""
        if run_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection, run_id)


manager = ConnectionManager()


@app.websocket("/ws/run/{run_id}")
async def websocket_run_updates(
    websocket: WebSocket,
    run_id: str
):
    """
    WebSocket endpoint for real-time workflow execution updates.

    **Parameters:**
    - run_id: Run identifier to monitor

    **Messages:**
    - status: Current run status (pending, running, completed, failed)
    - log: New execution log entry
    - final_state: Final workflow state (on completion)

    **Example:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/run/run_123abc');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Update:', data);
    };
    ```
    """
    await manager.connect(websocket, run_id)

    try:
        # Get database session
        from app.database.connection import get_session_context

        async with get_session_context() as session:
            run_repo = RunRepository(session)
            log_repo = ExecutionLogRepository(session)

            # Get run
            run = await run_repo.get_by_run_id(run_id)
            if not run:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Run '{run_id}' not found"
                })
                await websocket.close()
                return

            # Send initial status
            await websocket.send_json({
                "type": "status",
                "run_id": run_id,
                "status": run.status.value,
                "started_at": run.started_at.isoformat() if run.started_at else None
            })

            # Send existing logs
            logs = await log_repo.get_by_run_id(run.id)
            for log in logs:
                await websocket.send_json({
                    "type": "log",
                    "node_name": log.node_name,
                    "status": log.status.value,
                    "iteration": log.iteration,
                    "execution_time_ms": log.execution_time_ms,
                    "timestamp": log.timestamp.isoformat(),
                    "error_message": log.error_message
                })

            # Send final state if completed
            if run.status.value in ["completed", "failed", "cancelled"]:
                await websocket.send_json({
                    "type": "final",
                    "status": run.status.value,
                    "final_state": run.final_state,
                    "total_iterations": run.total_iterations,
                    "total_execution_time_ms": run.total_execution_time_ms,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    "error_message": run.error_message
                })

        # Keep connection alive and wait for client messages
        while True:
            # In a real implementation, this would poll the database for updates
            # or use a pub/sub system like Redis to get real-time notifications
            data = await websocket.receive_text()

            # Echo back or handle client requests
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(websocket, run_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
