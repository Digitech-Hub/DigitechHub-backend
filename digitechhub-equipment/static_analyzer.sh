#!/bin/bash
set -e

echo "✍️ Runnning isort..."
uv run isort .

echo "🔍 Checking syntax errors..."
python3 -m compileall -q .

echo "🔍 Running Ruff..."
uv run ruff check .

echo "🔍 Running Mypy..."
uv run mypy .
