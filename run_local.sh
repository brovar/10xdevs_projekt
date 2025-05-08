#!/bin/bash

# Check if PostgreSQL is running
pg_isready -h localhost -p 5432 -U postgres
if [ $? -ne 0 ]; then
    echo "PostgreSQL is not running. Starting PostgreSQL..."
    # This command will vary depending on the OS, this is for systemd-based systems
    sudo systemctl start postgresql
    sleep 5
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export ENVIRONMENT=development
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/steambay"
export ALLOWED_ORIGINS="http://localhost:3000"
export SESSION_SECRET="development_session_secret"

# Initialize database and run backend
echo "Initializing database..."
python -m src.init_db

# Start the backend
echo "Starting backend server..."
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 