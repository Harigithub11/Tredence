#!/bin/bash
# Setup script for Agent Workflow Engine

set -e

echo "🚀 Setting up Agent Workflow Engine..."

# Check Python version
echo "📋 Checking Python version..."
python --version

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔨 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "✨ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create .env from example
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Start PostgreSQL with Docker
echo "🐘 Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "To access the API:"
echo "  API Docs: http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo ""
