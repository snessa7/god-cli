#!/bin/bash

# God CLI Launcher Script
# This script provides the 'god' command functionality

# Get the directory where this script is located
# Follow symlinks to get the real directory
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "❌ Virtual environment not found in $SCRIPT_DIR"
    echo "Please run the installation from the God CLI directory:"
    echo "  cd '$SCRIPT_DIR'"
    echo "  ./install.sh"
    exit 1
fi

# Change to script directory and activate virtual environment
cd "$SCRIPT_DIR"
source venv/bin/activate

# Run the CLI tool with all arguments
python god_cli.py "$@"
