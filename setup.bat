@echo off
REM Setup script for Agent Workflow Engine (Windows)

echo 🚀 Setting up Agent Workflow Engine...

REM Check Python version
echo 📋 Checking Python version...
python --version

REM Create virtual environment
if not exist "venv" (
    echo 🔨 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo ✨ Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
pip install -r requirements-dev.txt

REM Create .env from example
if not exist ".env" (
    echo 📝 Creating .env file...
    copy .env.example .env
    echo ⚠️  Please update .env with your configuration
)

REM Start PostgreSQL with Docker
echo 🐘 Starting PostgreSQL...
docker-compose up -d postgres

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak > nul

REM Run migrations
echo 🔄 Running database migrations...
alembic upgrade head

echo.
echo ✅ Setup complete!
echo.
echo To start the application:
echo   venv\Scripts\activate.bat
echo   uvicorn app.main:app --reload
echo.
echo To access the API:
echo   API Docs: http://localhost:8000/docs
echo   Health Check: http://localhost:8000/health
echo.

pause
