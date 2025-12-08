# Quick Start Guide

Get the Agent Workflow Engine running in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Docker Desktop (for PostgreSQL)
- Git

## Step 1: Clone and Navigate

```bash
cd C:\Hari\JOB\Tredence\agent-workflow-engine
```

## Step 2: Run Setup Script

### On Windows:
```bash
setup.bat
```

### On Linux/Mac:
```bash
chmod +x setup.sh
./setup.sh
```

The script will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Start PostgreSQL in Docker
- ✅ Run database migrations
- ✅ Create .env file

## Step 3: Activate Virtual Environment

### On Windows:
```bash
venv\Scripts\activate
```

### On Linux/Mac:
```bash
source venv/bin/activate
```

## Step 4: Start the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 5: Verify Installation

Open your browser to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see:
```json
{"status": "healthy"}
```

## Next Steps

### Create Your First Workflow

```bash
curl -X POST http://localhost:8000/api/v1/graph/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello_workflow",
    "description": "My first workflow",
    "nodes": [
      {"name": "step1", "tool": "test_tool"}
    ],
    "edges": [],
    "entry_point": "step1"
  }'
```

### Run Tests

```bash
pytest tests/ -v
```

### View API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- All endpoints documented
- Try it out feature
- Request/response examples

## Troubleshooting

### Port 8000 already in use
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Use a different port
uvicorn app.main:app --reload --port 8001
```

### PostgreSQL connection error
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres

# View logs
docker-compose logs postgres
```

### Module not found errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check virtual environment is activated
which python  # Should show venv/bin/python
```

### Database migration errors
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

## Development Workflow

1. **Make changes** to code in `app/`
2. **Format code**: `black app/`
3. **Run tests**: `pytest tests/ -v`
4. **Check types**: `mypy app/`
5. **Commit**: `git commit -m "Your message"`

## Useful Commands

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1

# Docker commands
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose logs -f app    # View app logs
docker-compose ps             # View service status
```

## What's Next?

- 📖 Read the [Architecture](ARCHITECTURE.md) document
- 📋 Follow the [Implementation Phases](PROJECT_PHASES.md)
- 🔧 Start implementing the core engine (Phase 2)
- 🧪 Write tests as you go

## Getting Help

- Check [README.md](README.md) for detailed documentation
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [PROJECT_PHASES.md](PROJECT_PHASES.md) for implementation guide

---

**You're all set!** 🎉

The development environment is ready. Time to start building! 🚀
