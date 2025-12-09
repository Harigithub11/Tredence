# Agent Workflow Engine

A production-ready workflow orchestration engine for building multi-agent systems, inspired by LangGraph.

## 🎯 Features

- **Graph-based Workflows**: Define workflows as directed graphs with nodes and edges
- **Async Execution**: Fully async/await support with FastAPI
- **State Management**: Type-safe state management with Pydantic models
- **Conditional Branching**: Dynamic routing based on state conditions
- **Looping Support**: Built-in loop detection with max iteration limits
- **Tool Registry**: Decorator-based tool registration system
- **REST API**: Comprehensive FastAPI endpoints for workflow management
- **WebSocket Streaming**: Real-time execution logs via WebSocket
- **PostgreSQL Persistence**: Durable state storage with SQLAlchemy
- **Hybrid LLM Support**: Optional Gemini integration for advanced workflows

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Future Enhancements](#future-enhancements)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or use Docker)
- Git

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd agent-workflow-engine
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start PostgreSQL (using Docker)**
```bash
docker-compose up -d postgres
```

6. **Run database migrations**
```bash
alembic upgrade head
```

7. **Start the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Access the API**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📖 Usage

### 1. Create a Workflow Graph

```bash
curl -X POST http://localhost:8000/api/v1/graph/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code_review_workflow",
    "description": "Analyzes Python code quality",
    "nodes": [
      {"name": "extract", "tool": "extract_functions"},
      {"name": "analyze", "tool": "calculate_complexity"},
      {"name": "report", "tool": "check_quality"}
    ],
    "edges": [
      {"from": "extract", "to": "analyze"},
      {"from": "analyze", "to": "report"}
    ],
    "entry_point": "extract"
  }'
```

**Response:**
```json
{
  "graph_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "code_review_workflow",
  "created_at": "2025-12-08T10:30:00Z"
}
```

### 2. Execute a Workflow

```bash
curl -X POST http://localhost:8000/api/v1/graph/run \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "550e8400-e29b-41d4-a716-446655440000",
    "initial_state": {
      "code": "def hello():\n    pass"
    }
  }'
```

**Response:**
```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "started_at": "2025-12-08T10:35:00Z"
}
```

### 3. Query Execution State

```bash
curl http://localhost:8000/api/v1/graph/state/660e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "current_state": {
    "code": "def hello():\n    pass",
    "quality_score": 85,
    "suggestions": ["Add docstring"]
  }
}
```

### 4. WebSocket Streaming (Real-time Logs)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/graph/ws/660e8400-e29b-41d4-a716-446655440000');

ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log);
  // { "type": "log", "node": "extract", "status": "completed" }
};
```

## 📚 API Documentation

Full API documentation is available at: http://localhost:8000/docs

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/graph/create` | Create a new workflow graph |
| POST | `/api/v1/graph/run` | Execute a workflow |
| GET | `/api/v1/graph/state/{run_id}` | Query execution state |
| GET | `/api/v1/graph/{graph_id}` | Get workflow definition |
| WS | `/api/v1/graph/ws/{run_id}` | Stream execution logs |

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────┐
│  FastAPI    │
│  REST API   │
└──────┬──────┘
       │
┌──────▼──────────┐
│ Workflow Engine │
│  (Orchestrator) │
└──────┬──────────┘
       │
   ┌───┴───┬──────────┐
   │       │          │
┌──▼─┐  ┌─▼──┐  ┌───▼────┐
│Core│  │Tool│  │Database│
│    │  │Reg │  │(Postgres)
└────┘  └────┘  └────────┘
```

### Core Components

1. **Workflow Engine** (`app/core/engine.py`): Main orchestrator for graph execution
2. **State Management** (`app/core/state.py`): Type-safe Pydantic models
3. **Node System** (`app/core/node.py`): Executable workflow units
4. **Graph Definition** (`app/core/graph.py`): Workflow structure
5. **Tool Registry** (`app/core/registry.py`): Function management
6. **Database Layer** (`app/database/`): PostgreSQL persistence

For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🛠️ Development

### Project Structure

```
agent-workflow-engine/
├── app/
│   ├── core/              # Core engine components
│   ├── database/          # Database models & repositories
│   ├── api/               # FastAPI routes
│   ├── workflows/         # Workflow implementations
│   │   └── code_review/   # Code review workflow
│   ├── llm/               # LLM integration (optional)
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── alembic/               # Database migrations
├── docs/                  # Additional documentation
├── requirements.txt       # Python dependencies
└── docker-compose.yml     # Docker configuration
```

### Code Quality Tools

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type check
mypy app/

# Sort imports
isort app/ tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ -v --cov=app --cov-report=html
```

View coverage report: `htmlcov/index.html`

### Run Specific Test Files

```bash
pytest tests/test_core/test_engine.py -v
```

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Option 2: Docker Only

```bash
# Build image
docker build -t agent-workflow-engine .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  agent-workflow-engine
```

## 📊 Example: Code Review Workflow

The included Code Review workflow demonstrates the engine's capabilities:

**Features:**
- Extracts Python functions using AST
- Calculates cyclomatic complexity
- Detects code quality issues
- Generates improvement suggestions
- Hybrid approach: Rules + optional LLM
- Loops until quality threshold met

**Usage:**

```python
from app.workflows.code_review.workflow import run_code_review

code = """
def calculate_sum(numbers):
    return sum(numbers)
"""

result = await run_code_review(code, use_llm=False)
print(f"Quality Score: {result.data['quality_score']}")
print(f"Suggestions: {result.data['suggestions']}")
```

## 🔮 Future Enhancements

### Planned Features

1. **Financial Analysis Workflow** (Priority: High)
   - Multi-agent stock analysis
   - Real-time market data integration
   - LLM-powered insights

2. **Caching Layer** (Priority: Medium)
   - Redis integration
   - Multi-level caching
   - Reduce API costs

3. **Advanced Features** (Priority: Low)
   - Parallel node execution
   - Human-in-the-loop workflows
   - Visual workflow editor

4. **Production Hardening**
   - Authentication & authorization
   - Rate limiting
   - Monitoring & observability
   - Circuit breakers

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed enhancement roadmap.

## 🤝 Contributing

This is a personal assignment project, but suggestions are welcome!

### Development Guidelines

1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation
4. Use type hints
5. Format with Black

## 📄 License

This project is created as part of an internship assignment.

## 📞 Contact

**Author**: E Hari
**Email**: enguvahari@gmail.com
**GitHub**: https://github.com/Harigithub11/Tredence/

---

## 🎓 Assignment Context

This project was created as part of the AI Engineering Internship assignment for Tredence. The goal was to build a minimal workflow orchestration engine demonstrating:

- ✅ Clean Python code structure
- ✅ Async programming with FastAPI
- ✅ Database design and ORM usage
- ✅ API design best practices
- ✅ State management in workflows
- ✅ Production-ready engineering practices

**Key Achievements:**
- Complete workflow engine with branching and looping
- Production-grade FastAPI application
- PostgreSQL persistence with Alembic migrations
- WebSocket streaming for real-time updates
- Comprehensive test coverage (>80%)
- Docker deployment configuration
- Hybrid workflow supporting both rules and LLM

---

**Built with ❤️ using Python, FastAPI, PostgreSQL, and lots of async/await**
