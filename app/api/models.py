"""FastAPI Request and Response Models

Pydantic models for API validation and documentation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
from datetime import datetime


class NodeDefinition(BaseModel):
    """Node definition in graph creation"""
    name: str = Field(..., description="Unique node name")
    tool: str = Field(..., description="Tool/function to execute")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "extract_functions",
                "tool": "extract_code_functions"
            }
        }
    }


class EdgeDefinition(BaseModel):
    """Edge definition connecting nodes"""
    from_node: str = Field(..., alias="from", description="Source node name")
    to_node: str = Field(..., alias="to", description="Target node name")
    condition: Optional[str] = Field(None, description="Conditional routing function")

    model_config = {
        "json_schema_extra": {
            "example": {
                "from": "node_a",
                "to": "node_b",
                "condition": None
            }
        },
        "populate_by_name": True
    }


class CreateGraphRequest(BaseModel):
    """Request to create a new workflow graph"""
    name: str = Field(..., min_length=1, max_length=255, description="Unique graph name")
    description: Optional[str] = Field("", max_length=1000, description="Graph description")
    nodes: List[NodeDefinition] = Field(..., min_length=1, description="List of nodes")
    edges: List[EdgeDefinition] = Field(..., description="List of edges")
    entry_point: str = Field(..., description="Starting node name")

    @field_validator("entry_point")
    @classmethod
    def validate_entry_point(cls, v: str, info) -> str:
        """Ensure entry_point exists in nodes"""
        if "nodes" in info.data:
            node_names = [node.name for node in info.data["nodes"]]
            if v not in node_names:
                raise ValueError(f"Entry point '{v}' not found in nodes")
        return v

    model_config = {
        "json_schema_extra": {
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
    }


class RunGraphRequest(BaseModel):
    """Request to execute a workflow"""
    graph_name: str = Field(..., description="Graph name or ID")
    initial_state: Dict[str, Any] = Field(..., description="Initial workflow state")
    timeout: Optional[int] = Field(None, ge=1, le=3600, description="Timeout in seconds")
    use_llm: bool = Field(False, description="Enable LLM features")

    model_config = {
        "json_schema_extra": {
            "example": {
                "graph_name": "code_review_workflow",
                "initial_state": {
                    "code": "def hello(): pass"
                },
                "timeout": 300,
                "use_llm": False
            }
        }
    }


class GraphResponse(BaseModel):
    """Response after graph creation"""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    version: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "code_review_workflow",
                "description": "Analyzes code quality",
                "created_at": "2025-12-08T10:30:00Z",
                "version": 1
            }
        },
        "from_attributes": True
    }


class ExecutionLogEntry(BaseModel):
    """Single execution log entry"""
    timestamp: datetime
    node_name: str
    status: str  # started, completed, failed
    iteration: int
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class RunResponse(BaseModel):
    """Response after workflow execution"""
    id: int
    run_id: str
    graph_id: int
    status: str  # pending, running, completed, failed
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    initial_state: Dict[str, Any]
    final_state: Optional[Dict[str, Any]]
    total_iterations: Optional[int]
    total_execution_time_ms: Optional[float]
    error_message: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "run_id": "run_123",
                "graph_id": 1,
                "status": "completed",
                "started_at": "2025-12-08T10:35:00Z",
                "completed_at": "2025-12-08T10:35:05Z",
                "initial_state": {"code": "def hello(): pass"},
                "final_state": {"complexity": 1},
                "total_iterations": 3,
                "total_execution_time_ms": 125.5,
                "error_message": None
            }
        },
        "from_attributes": True
    }


class RunWithLogsResponse(RunResponse):
    """Run response with execution logs"""
    execution_logs: List[ExecutionLogEntry] = []

    model_config = {
        "from_attributes": True
    }


class StateResponse(BaseModel):
    """Response for state query"""
    run_id: str
    status: str
    current_state: Optional[Dict[str, Any]]
    final_state: Optional[Dict[str, Any]]

    model_config = {
        "from_attributes": True
    }


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
    error_type: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Graph not found",
                "error_type": "NotFoundError"
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: bool
    timestamp: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "database": True,
                "timestamp": "2025-12-08T10:00:00Z"
            }
        }
    }
