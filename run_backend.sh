#!/bin/bash

# Ensure we are executing from the script's directory (the project root)
cd "$(dirname "$0")"

# 1. Activate the Python virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️ Warning: .venv folder not found. Running with global python environment..."
fi

# 2. Re-verify output staging directory exists 
mkdir -p outputs

# 3. Fire up the FastAPI server via module notation from the root directory context
echo "⚡ Starting EPC Platform Engine on http://127.0.0.1:8000/docs ..."
uvicorn backend.main:app --reload