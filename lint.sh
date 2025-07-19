#!/bin/bash

echo "Running type checking with mypy..."
mypy .

echo "Running linting with ruff..."
ruff check .

echo "All checks completed!" 