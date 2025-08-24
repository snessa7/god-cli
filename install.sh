#!/bin/bash

# God CLI Installation Script
# This script will install the God CLI tool and create the 'god' alias

set -e

echo "🚀 Installing God CLI - Ollama Chat Interface"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION detected. Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✅ pip3 detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies in virtual environment..."
source venv/bin/activate
pip install -r requirements.txt

# Make the script executable
echo "🔧 Making script executable..."
chmod +x god_cli.py

# Install the package in development mode
echo "📥 Installing God CLI package..."
pip install -e .

# Detect shell and create alias
SHELL_PROFILE=""
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [[ "$SHELL" == *"fish"* ]]; then
    SHELL_PROFILE="$HOME/.config/fish/config.fish"
else
    echo "⚠️  Could not detect shell type. Please manually add the alias to your shell profile."
    echo "   Add this line: alias god='source $(pwd)/venv/bin/activate && python $(pwd)/god_cli.py'"
fi

if [ -n "$SHELL_PROFILE" ]; then
    # Check if alias already exists
    if ! grep -q "alias god=" "$SHELL_PROFILE"; then
        echo "🔗 Adding 'god' alias to $SHELL_PROFILE..."
        echo "" >> "$SHELL_PROFILE"
        echo "# God CLI alias" >> "$SHELL_PROFILE"
        echo "alias god='source $(pwd)/venv/bin/activate && python $(pwd)/god_cli.py'" >> "$SHELL_PROFILE"
        echo "✅ Alias added to $SHELL_PROFILE"
    else
        echo "✅ Alias already exists in $SHELL_PROFILE"
    fi
fi

# Test the installation
echo "🧪 Testing installation..."
if source venv/bin/activate && python god_cli.py --test &> /dev/null; then
    echo "✅ Installation test successful!"
else
    echo "⚠️  Installation test failed. This might be normal if Ollama is not running."
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To use God CLI:"
echo "  1. Make sure Ollama is running: ollama serve"
echo "  2. Pull a model: ollama pull llama2 (or use your existing gemma3:1b)"
echo "  3. Start chatting: god"
echo ""
echo "If you added the alias, reload your shell:"
if [[ "$SHELL" == *"zsh"* ]]; then
    echo "  source ~/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    echo "  source ~/.bashrc"
elif [[ "$SHELL" == *"fish"* ]]; then
    echo "  source ~/.config/fish/config.fish"
fi
echo ""
echo "For more information, see README.md"
echo ""
echo "Happy chatting! 🚀"
