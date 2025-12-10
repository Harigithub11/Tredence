# Docker Deployment Guide

Complete guide for deploying the Agent Workflow Engine using Docker Compose.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd agent-workflow-engine
cp .env.example .env  # Configure your environment variables
```

### 2. Configure Environment

Edit `.env` file with your settings:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (defaults provided)
ENABLE_LLM=True
DEBUG=True
LOG_LEVEL=INFO
```

### 3. Start All Services

```bash
# Start core services (API, PostgreSQL, Redis)
docker-compose up -d

# Or start with database management tools
docker-compose --profile tools up -d
```

### 4. Verify Deployment

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f app

# Test API
curl http://localhost:8000/health
```

## 🏗️ Services Overview

| Service | Port | Description | Access |
|---------|------|-------------|--------|
| **API** | 8000 | FastAPI application | http://localhost:8000 |
| **PostgreSQL** | 5432 | Workflow database | localhost:5432 |
| **Redis** | 6379 | Cache layer | localhost:6379 |
| **pgAdmin** | 5050 | DB management UI (optional) | http://localhost:5050 |

### API Endpoints

- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws/run/{run_id}

## 📊 Service Details

### PostgreSQL Database

**Container**: `workflow_engine_db`

```yaml
Credentials:
  User: workflow_user
  Password: workflow_pass
  Database: workflow_engine
```

**Connection String**:
```
postgresql://workflow_user:workflow_pass@localhost:5432/workflow_engine
```

### Redis Cache

**Container**: `workflow_engine_redis`

- Persistence: AOF enabled
- Volume: `redis_data`

### pgAdmin (Optional)

**Container**: `workflow_engine_pgadmin`

```yaml
Access:
  URL: http://localhost:5050
  Email: admin@workflow.com
  Password: admin
```

**Add Server in pgAdmin**:
1. Right-click "Servers" → Register → Server
2. Name: Workflow Engine
3. Connection tab:
   - Host: postgres
   - Port: 5432
   - Database: workflow_engine
   - Username: workflow_user
   - Password: workflow_pass

## 🔧 Common Operations

### Start Services

```bash
# All services
docker-compose up -d

# Specific service
docker-compose up -d app

# With tools (pgAdmin)
docker-compose --profile tools up -d
```

### Stop Services

```bash
# Stop all
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app
```

### Restart Service

```bash
docker-compose restart app
```

### Execute Commands in Container

```bash
# Access app shell
docker-compose exec app bash

# Run tests
docker-compose exec app pytest tests/

# Run migrations
docker-compose exec app alembic upgrade head

# Python shell
docker-compose exec app python
```

## 🧪 Running Tests

```bash
# Run all tests
docker-compose exec app pytest tests/ -v

# With coverage
docker-compose exec app pytest tests/ --cov=app --cov-report=term-missing

# Specific test file
docker-compose exec app pytest tests/test_api/test_graph_routes.py -v
```

## 🔄 Database Management

### Run Migrations

```bash
# Apply all migrations
docker-compose exec app alembic upgrade head

# Rollback one migration
docker-compose exec app alembic downgrade -1

# View migration history
docker-compose exec app alembic history
```

### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U workflow_user workflow_engine > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U workflow_user workflow_engine < backup.sql
```

### Reset Database

```bash
# ⚠️ Warning: This deletes all data
docker-compose down -v
docker-compose up -d
```

## 📈 Monitoring

### Health Checks

All services include health checks:

```bash
# Check all services
docker-compose ps

# Service-specific health
docker inspect --format='{{.State.Health.Status}}' workflow_engine_app
```

### Resource Usage

```bash
# View stats
docker stats

# Specific service
docker stats workflow_engine_app
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Database Connection Failed

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify database is healthy
docker-compose exec postgres pg_isready -U workflow_user

# Recreate database
docker-compose down postgres
docker volume rm agent-workflow-engine_postgres_data
docker-compose up -d postgres
```

### Application Won't Start

```bash
# View full logs
docker-compose logs app

# Check healthcheck
docker inspect workflow_engine_app | grep -A 10 Health

# Rebuild image
docker-compose build --no-cache app
docker-compose up -d app
```

### Out of Memory

```bash
# Increase Docker memory limit (Docker Desktop → Settings → Resources)
# Or add to docker-compose.yml:

services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
```

## 🔐 Production Considerations

### Security

**Before deploying to production**:

1. **Change default passwords**:
   ```yaml
   POSTGRES_PASSWORD: <strong-password>
   PGADMIN_DEFAULT_PASSWORD: <strong-password>
   ```

2. **Disable DEBUG mode**:
   ```yaml
   DEBUG: "False"
   ```

3. **Use secrets management**:
   ```bash
   # Use Docker secrets or environment variables
   docker-compose --env-file .env.production up -d
   ```

4. **Enable authentication** (see Authentication enhancement)

5. **Add rate limiting** (see Rate Limiting enhancement)

### Performance

1. **Resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
       reservations:
         cpus: '1.0'
         memory: 2G
   ```

2. **Connection pooling**:
   - PostgreSQL: max_connections = 100
   - Redis: maxmemory-policy allkeys-lru

3. **Logging**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

### Scaling

```bash
# Scale app instances
docker-compose up -d --scale app=3

# Add load balancer (nginx/traefik)
# See advanced deployment docs
```

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | auto | PostgreSQL connection string |
| `REDIS_URL` | auto | Redis connection string |
| `DEBUG` | True | Enable debug mode |
| `LOG_LEVEL` | INFO | Logging level |
| `ENABLE_LLM` | True | Enable LLM features |
| `GEMINI_API_KEY` | - | Google Gemini API key |
| `HOST` | 0.0.0.0 | API host |
| `PORT` | 8000 | API port |

## 🎯 Next Steps

1. ✅ Services running
2. 📖 Read API docs: http://localhost:8000/docs
3. 🧪 Run example workflow:
   ```bash
   cd examples
   python demo_code_review.py
   ```
4. 🚀 Build your first workflow
5. 📊 Monitor via pgAdmin: http://localhost:5050

## 📚 Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [Project README](README.md)
- [Development Guide](DEVELOPMENT.md)
- [Future Enhancements](PROJECT_PHASES.md#phase-8-future-enhancements--roadmap)

## 🆘 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify health: `docker-compose ps`
3. Review [Troubleshooting](#-troubleshooting)
4. Check GitHub Issues

---

**Ready to deploy?** Run `docker-compose up -d` and you're live! 🎉
