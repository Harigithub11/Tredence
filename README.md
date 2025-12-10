# Agent Workflow Engine - Mini LangGraph

A production-ready workflow orchestration engine with real-time dashboard for building multi-agent systems, created for Tredence AI Engineering Internship.

## 🎯 Overview

This project implements a minimal but complete workflow/graph engine inspired by LangGraph, featuring a **Code Review Mini-Agent** with hybrid test generation (pattern-based + LLM fallback) and a real-time React dashboard.

## ✨ Key Features

### Core Engine
- **Graph-based Workflows**: Define workflows as directed graphs with nodes and edges
- **State Management**: Type-safe state flow using Pydantic models (dictionary-based)
- **Conditional Branching**: Dynamic routing based on state conditions (`quality_score >= threshold`)
- **Looping Support**: Iterative execution until conditions met (max 3 iterations)
- **Tool Registry**: Pre-registered Python functions as workflow tools
- **Async Execution**: Fully async with FastAPI and asyncio

### API & Real-time
- **FastAPI Endpoints**:
  - `POST /graph/create` - Create workflow graphs
  - `POST /graph/run` - Execute workflows
  - `GET /graph/state/{run_id}` - Query execution state
  - `GET /graph/stats/summary` - Aggregated statistics
  - `GET /graph/runs/list` - List all workflow runs
- **WebSocket Streaming**: Real-time execution logs (`/ws/run/{run_id}`)
- **PostgreSQL Persistence**: Durable storage with SQLAlchemy ORM

### Frontend Dashboard
- **Real-time Monitoring**: WebSocket-powered live updates
- **Dynamic Progress**: Node-based progress tracking (10% → 95% → 100%)
- **Component Persistence**: Tabs don't unmount (polling continues when hidden)
- **Dashboard Stats**: Total runs, running, completed, failed, success rate, avg execution time
- **Active Runs**: Expandable cards with progress bars, current node, execution time
- **Recent Analysis**: Complexity (O notation), quality scores, expandable execution flow

### Code Review Workflow
- **Extract Functions**: AST-based Python function extraction
- **Calculate Complexity**: Radon cyclomatic complexity analysis (time/space O notation)
- **Detect Issues**: PEP-8, complexity, best practice violations
- **Improve Code**: Type hints, docstrings, algorithm optimization
- **Hybrid Test Generation**: Pattern matching (9 categories) + Gemini LLM fallback
- **Quality Loop**: Iterates until `quality_score >= threshold` (max 3 iterations)

---

## 🏗️ Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │  Dashboard   │  │ Code Review  │  │  WebSocket Hook     │  │
│  │  (Stats)     │  │  Form        │  │  (Real-time logs)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘  │
└─────────┼──────────────────┼───────────────────────┼────────────┘
          │                  │                       │
          │ HTTP/REST        │ HTTP/POST             │ WebSocket
          │                  │                       │
┌─────────▼──────────────────▼───────────────────────▼────────────┐
│                    FastAPI Backend (Port 8001)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API Routes (/api/v1/graph/*)                              │ │
│  │  - create, run, state, stats/summary, runs/list           │ │
│  └────────────┬───────────────────────────────────────────────┘ │
│               │                                                  │
│  ┌────────────▼───────────────────────────────────────────────┐ │
│  │          Workflow Engine (Orchestrator)                    │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │ │
│  │  │   Graph     │  │    Edge     │  │  WorkflowState   │  │ │
│  │  │  (Nodes)    │  │  Manager    │  │  (Pydantic)      │  │ │
│  │  └─────────────┘  └─────────────┘  └──────────────────┘  │ │
│  └────────────┬───────────────────────────────────────────────┘ │
│               │                                                  │
│  ┌────────────▼───────────────────────────────────────────────┐ │
│  │  Tool Registry (Decorator-based)                           │ │
│  │  - extract_functions   - detect_issues                     │ │
│  │  - calculate_complexity - suggest_improvements             │ │
│  │  - check_quality       - generate_tests (hybrid)           │ │
│  └────────────┬───────────────────────────────────────────────┘ │
└───────────────┼──────────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────────┐
│              PostgreSQL Database (Port 5432)                      │
│  - graphs (workflow definitions)                                 │
│  - runs (execution records)                                      │
│  - execution_logs (node-level logs)                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│             Optional: Gemini API (LLM Fallback)                   │
│  - Test case generation when pattern matching fails               │
│  - Timeout: 2 seconds, graceful degradation                       │
└──────────────────────────────────────────────────────────────────┘
```

### Workflow Execution Flow

```
Code Review Workflow Graph:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  extract    │────▶│ complexity  │────▶│   detect    │
│ _functions  │     │  _analysis  │     │  _issues    │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   check     │◀────│   improve   │
                    │  _quality   │     │    _code    │
                    └──────┬──────┘     └─────────────┘
                           │
                    quality_score >= threshold?
                           │
                    ┌──────┴──────┐
                    │             │
                  YES            NO (iteration < 3)
                    │             │
                   END      Loop back to improve
```

**Edges:**
- `extract → complexity → detect → improve → check` (linear)
- `check → improve` (conditional: `quality_score < threshold AND iteration < 3`)

**Branching:**
- After `check_quality` node: If quality passed → END, else → loop back to `improve_code`

**Looping:**
- Max 3 iterations
- Loop condition: `quality_score < quality_threshold AND iteration < max_iterations`

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (running)
- **Node.js 18+** (for frontend)
- **Git**
- **Gemini API Key** (optional, for LLM fallback)

### Installation Steps

#### 1. Clone Repository

```bash
git clone https://github.com/Harigithub11/Tredence.git
cd agent-workflow-engine
```

#### 2. Backend Setup (Docker)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key (optional)
# GEMINI_API_KEY=your_actual_key_here

# Start backend + PostgreSQL + Redis
docker-compose up -d

# Verify containers are running
docker-compose ps
```

Expected output:
```
NAME                   STATUS         PORTS
workflow_engine_app    running        0.0.0.0:8001->8000/tcp
workflow_engine_db     running        5432/tcp
workflow_engine_redis  running        6379/tcp
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create frontend .env
echo "VITE_API_URL=http://localhost:8001/api/v1" > .env
echo "VITE_WS_URL=ws://localhost:8001" >> .env

# Start development server
npm run dev
```

#### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

---

## 📖 Usage

### Using the Dashboard (Recommended)

1. Open http://localhost:3000
2. Go to "Code Review" tab
3. Paste Python code
4. Toggle "Use LLM for Test Generation" (optional)
5. Set quality threshold (default: 70)
6. Click "Run Code Review"
7. Watch real-time progress
8. Switch to "Dashboard" tab to see stats update live
9. View results: improved code, complexity, issues, improvements applied

### Using API Directly

#### Create Workflow Graph

```bash
curl -X POST http://localhost:8001/api/v1/graph/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code_review",
    "description": "Python code quality analysis",
    "nodes": [
      {"name": "extract", "tool": "extract_functions"},
      {"name": "complexity", "tool": "calculate_complexity"},
      {"name": "detect", "tool": "detect_issues"},
      {"name": "improve", "tool": "suggest_improvements"},
      {"name": "check", "tool": "check_quality"}
    ],
    "edges": [
      {"from": "extract", "to": "complexity"},
      {"from": "complexity", "to": "detect"},
      {"from": "detect", "to": "improve"},
      {"from": "improve", "to": "check"},
      {"from": "check", "to": "improve", "condition": "quality_fail"}
    ],
    "entry_point": "extract"
  }'
```

#### Run Workflow

```bash
curl -X POST http://localhost:8001/api/v1/graph/run \
  -H "Content-Type: application/json" \
  -d '{
    "graph_name": "code_review",
    "initial_state": {
      "code": "def find_max(nums):\n    max = nums[0]\n    for n in nums:\n        if n > max: max = n\n    return max",
      "use_llm": false,
      "quality_threshold": 70
    },
    "timeout": 300
  }'
```

#### Check Run State

```bash
curl http://localhost:8001/api/v1/graph/state/run_abc123
```

#### Get Statistics

```bash
curl http://localhost:8001/api/v1/graph/stats/summary
```

Response:
```json
{
  "total": 48,
  "running": 1,
  "completed": 44,
  "failed": 3,
  "avg_execution_time_ms": 10900.5,
  "success_rate": 91.67
}
```

---

## 📁 Project Structure

```
agent-workflow-engine/
├── app/
│   ├── core/                      # Core engine components
│   │   ├── engine.py              # Workflow orchestrator
│   │   ├── graph.py               # Graph definition & builder
│   │   ├── node.py                # Node implementations
│   │   ├── edge.py                # Edge manager + conditional routing
│   │   ├── state.py               # WorkflowState Pydantic model
│   │   └── registry.py            # Tool registry (@registry.tool)
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models (GraphModel, RunModel)
│   │   └── repositories.py        # Database operations
│   ├── api/
│   │   └── routes/
│   │       └── graph.py           # FastAPI endpoints
│   ├── websocket/
│   │   ├── manager.py             # WebSocket connection manager
│   │   └── messages.py            # Message schemas
│   ├── workflows/
│   │   └── code_review/
│   │       ├── workflow.py        # Graph definition
│   │       ├── nodes.py           # 5 workflow nodes
│   │       ├── test_validator.py  # Hybrid test generation
│   │       └── code_improver.py   # AST-based improvements
│   ├── llm/
│   │   └── client.py              # Gemini API client
│   └── main.py                    # FastAPI app entry point
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx      # Main dashboard (stats cards)
│   │   │   ├── CodeReviewForm.tsx # Code submission form
│   │   │   ├── ActiveRuns.tsx     # Running workflows (progress bars)
│   │   │   ├── RecentAnalysis.tsx # Completed runs (with execution flow)
│   │   │   ├── WorkflowStats.tsx  # Avg time, success rate
│   │   │   └── SystemHealth.tsx   # API/DB health
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts    # WebSocket real-time hook
│   │   ├── services/
│   │   │   └── api.ts             # Axios API client
│   │   ├── App.tsx                # Main app (tab switching, CSS visibility)
│   │   └── main.tsx               # React entry point
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml             # Docker services (app, db, redis)
├── Dockerfile                     # Backend container
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## 🔧 Requirements Verification

### ✅ 1. Minimal Workflow/Graph Engine

- **Nodes**: Python functions decorated with `@registry.tool` ✓
  - `extract_functions`, `calculate_complexity`, `detect_issues`, `suggest_improvements`, `check_quality`
- **State**: `WorkflowState` Pydantic model (dictionary `data` field) ✓
- **Edges**: Simple mapping in `workflow.py` ✓
  - `builder.edge("extract", "complexity")`
- **Branching**: Conditional routing with `should_loop()` function ✓
  - `builder.edge("check", "improve", condition=should_loop)`
- **Looping**: Iterative execution until `quality_score >= threshold` ✓
  - Max 3 iterations enforced

### ✅ 2. Tool Registry

- **Dictionary of tools**: `ToolRegistry` class in `app/core/registry.py` ✓
- **Pre-registered tools**: 5 tools registered with decorators ✓
- **Example tool**:
  ```python
  @registry.tool(name="detect_issues", description="Detect code quality issues")
  async def detect_issues_node(state: WorkflowState) -> WorkflowState:
      # Implementation
      return state
  ```

### ✅ 3. FastAPI Endpoints

- **POST /graph/create**: Create workflow graph ✓
- **POST /graph/run**: Execute workflow ✓
- **GET /graph/state/{run_id}**: Query execution state ✓
- **Database**: PostgreSQL (not in-memory) ✓

### ✅ 4. Sample Workflow - Code Review Mini-Agent

1. **Extract functions**: AST-based Python function extraction ✓
2. **Check complexity**: Radon cyclomatic complexity (time/space) ✓
3. **Detect issues**: PEP-8, complexity, best practices ✓
4. **Suggest improvements**: Type hints, docstrings, optimization ✓
5. **Loop until quality >= threshold**: Conditional edge with max 3 iterations ✓

### ✅ BONUS Features

- **WebSocket endpoint**: `/ws/run/{run_id}` for streaming logs ✓
- **Async execution**: Full async/await with FastAPI ✓
- **Real-time dashboard**: React frontend with live updates ✓
- **Hybrid test generation**: Pattern-based + LLM fallback ✓

---

## 🎨 Features Showcase

### Dashboard Statistics
- **Total Runs**: 48
- **Running**: 1
- **Completed**: 44
- **Failed**: 3
- **Avg Execution Time**: 10.9s
- **Success Rate**: 92%

### Active Runs - Dynamic Progress
- **10%**: Just started (initialized)
- **20%**: `extract_functions` completed (1/5 nodes)
- **40%**: `analyze_complexity` completed (2/5 nodes)
- **60%**: `detect_issues` completed (3/5 nodes)
- **80%**: `improve_code` completed (4/5 nodes)
- **95%**: `validate_tests` completed (5/5 nodes)
- **100%**: Workflow finished

### Recent Analysis - Execution Flow (Expandable)
Click "Show Execution Flow" to see:
- **Nodes**: extract_functions → analyze_complexity → detect_issues → improve_code → validate_tests
- **State**: Shared dict with code, functions, issues, complexity, improved_code
- **Edges**: Linear flow: extract→analyze→detect→improve→validate
- **Branching**: After validate_tests: quality_score ≥ threshold → end, else → improve_code
- **Looping**: Improve→Validate loop until quality_score ≥ 70 (max 3 iterations)
- **Tools**: AST parser, Radon complexity analyzer, Gemini LLM/Pattern-based test generator
- **API**: POST /graph/run triggered, GET /graph/state/{run_id} polled for updates
- **Functions**: 1 function(s) extracted from code
- **Complexity**: Time: O(n^2), Space: O(n)
- **Issues**: 3 issue(s) detected (style, complexity, best practices)
- **Improvements**: 5 improvement(s) applied: Fixed missing_docstring, Added type hints, etc.
- **Iterations**: 2 iteration(s) to reach quality score 85/100

---

## 🛠️ Development

### Environment Setup

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Running Locally (Without Docker)

```bash
# Start PostgreSQL manually
psql -U postgres -c "CREATE DATABASE workflow_engine"

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Start frontend (separate terminal)
cd frontend && npm run dev
```

### Code Quality

```bash
# Format
black app/ tests/

# Lint
flake8 app/ tests/

# Type check
mypy app/
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild after code changes
docker-compose up --build -d

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 🔑 Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/workflow_engine

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000

# LLM (Optional)
GEMINI_API_KEY=your_gemini_api_key_here
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8001/api/v1
VITE_WS_URL=ws://localhost:8001
```

---

## 📊 API Endpoints Reference

| Method | Endpoint | Description | Input | Output |
|--------|----------|-------------|-------|--------|
| POST | `/api/v1/graph/create` | Create workflow graph | `{name, nodes, edges, entry_point}` | `{graph_id, name, created_at}` |
| POST | `/api/v1/graph/run` | Execute workflow | `{graph_name, initial_state, timeout}` | `{run_id, status, started_at}` |
| GET | `/api/v1/graph/state/{run_id}` | Get execution state | - | `{run_id, status, final_state, logs}` |
| GET | `/api/v1/graph/stats/summary` | Get statistics | - | `{total, running, completed, failed, avg_time, success_rate}` |
| GET | `/api/v1/graph/runs/list` | List all runs | `?limit=50&status=completed` | `[{run_id, status, ...}]` |
| WS | `/ws/run/{run_id}` | Stream logs | - | `{type, node_name, status, timestamp}` |
| GET | `/health` | Health check | - | `{status: "healthy"}` |

---

## 🎓 Assignment Context

**Created for**: Tredence AI Engineering Internship
**Author**: E Hari
**Email**: enguvahari@gmail.com
**GitHub**: https://github.com/Harigithub11/Tredence

### Assignment Requirements Met

✅ **Minimal Workflow Engine**
- Nodes, State, Edges, Branching, Looping

✅ **Tool Registry**
- Decorator-based registration

✅ **FastAPI Endpoints**
- /graph/create, /graph/run, /graph/state/{run_id}

✅ **Code Review Workflow**
- All 5 steps + quality loop

✅ **BONUS**
- WebSocket streaming
- Async execution
- Real-time React dashboard
- PostgreSQL persistence
- Hybrid LLM integration

---

## 🚀 Production Deployment Notes

### Security Checklist
- [ ] Change default PostgreSQL password
- [ ] Add authentication (JWT tokens)
- [ ] Enable HTTPS/TLS
- [ ] Set up API rate limiting
- [ ] Rotate Gemini API keys
- [ ] Enable CORS only for trusted origins

### Monitoring
- Add Prometheus metrics
- Set up logging with ELK stack
- Monitor WebSocket connections
- Track API response times

### Scaling
- Use PostgreSQL connection pooling
- Add Redis for caching
- Deploy with Kubernetes
- Use horizontal pod autoscaling

---

## 📝 License

This project is created as part of an internship assignment. All rights reserved.

---

## 🙏 Acknowledgments

- **LangGraph** by LangChain - Inspiration for graph-based workflow design
- **FastAPI** - Modern async web framework
- **React + Vite** - Lightning-fast frontend development
- **Gemini API** - LLM capabilities for hybrid workflows

---

**Built with ❤️ using Python, FastAPI, React, PostgreSQL, and WebSockets**
