"""WebSocket Message Types

Structured message formats for real-time workflow updates.
"""

from typing import Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """Base WebSocket message"""
    type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StatusUpdateMessage(WebSocketMessage):
    """Status update message

    Sent when workflow status changes (pending -> running -> completed/failed)
    """
    type: Literal["status_update"] = "status_update"
    run_id: str
    status: str  # pending, running, completed, failed, cancelled
    current_node: Optional[str] = None
    progress: Optional[int] = None  # 0-100 percentage
    started_at: Optional[str] = None


class NodeCompletedMessage(WebSocketMessage):
    """Node completion message

    Sent when a workflow node completes execution
    """
    type: Literal["node_completed"] = "node_completed"
    run_id: str
    node_name: str
    duration_ms: float
    output_preview: Optional[Dict[str, Any]] = None
    iteration: int = 0
    node_status: str = "completed"  # completed, failed, skipped


class WorkflowCompletedMessage(WebSocketMessage):
    """Workflow completion message

    Sent when entire workflow completes (success or failure)
    """
    type: Literal["workflow_completed"] = "workflow_completed"
    run_id: str
    status: str  # completed, failed
    final_state: Dict[str, Any]
    total_duration_ms: float
    total_iterations: int
    error_message: Optional[str] = None


class ProgressUpdateMessage(WebSocketMessage):
    """Progress update message

    Sent periodically during execution to show progress
    """
    type: Literal["progress_update"] = "progress_update"
    run_id: str
    current_node: str
    completed_nodes: int
    total_nodes: int
    progress_percentage: int  # 0-100
    estimated_time_remaining_ms: Optional[float] = None


class ErrorMessage(WebSocketMessage):
    """Error message

    Sent when an error occurs
    """
    type: Literal["error"] = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PongMessage(WebSocketMessage):
    """Pong response to ping"""
    type: Literal["pong"] = "pong"


class LogMessage(WebSocketMessage):
    """Execution log message"""
    type: Literal["log"] = "log"
    run_id: str
    node_name: str
    status: str
    iteration: int
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None
