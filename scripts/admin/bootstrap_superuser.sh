#!/bin/bash
# Wrapper script to run the superuser bootstrap with correct PYTHONPATH

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$SCRIPT_DIR"

# Run the bootstrap script
python "$SCRIPT_DIR/scripts/bootstrap_superuser.py" "$@" 