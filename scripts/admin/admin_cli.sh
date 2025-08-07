#!/bin/bash
# Wrapper script to run the admin CLI with correct PYTHONPATH

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$SCRIPT_DIR"

# Run the admin CLI script
python "$SCRIPT_DIR/scripts/admin_cli.py" "$@" 