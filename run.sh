#!/bin/bash
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv .venv
    echo "Installing dependencies from pyproject.toml..."
    uv pip install -e .
fi

source .venv/bin/activate
python main.py
