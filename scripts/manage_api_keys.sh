#!/bin/bash
# Wrapper script to run the API key management CLI with correct PYTHONPATH

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH to include the project root (parent directory)
export PYTHONPATH="$(dirname "$SCRIPT_DIR")"

# Run the API key management script
python "$SCRIPT_DIR/manage_api_keys.py" "$@" 