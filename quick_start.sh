#!/bin/bash

# Quick Start Script for God CLI
# This script provides immediate access without full installation

echo "🚀 God CLI Quick Start"
echo "======================"

# Check if Ollama is running
echo "🔍 Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running and accessible"
else
    echo "❌ Ollama is not running or not accessible"
    echo "Please start Ollama with: ollama serve"
    echo "Then ensure you have at least one model: ollama pull llama2"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Check if Python dependencies are available in venv
echo "📦 Checking Python dependencies in virtual environment..."
source venv/bin/activate
if python -c "import requests" 2>/dev/null; then
    echo "✅ Python dependencies are available"
else
    echo "⚠️  Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Make scripts executable
chmod +x god_cli.py config_manager.py

echo ""
echo "🎯 Quick Start Options:"
echo "1. Start chat immediately: source venv/bin/activate && python god_cli.py"
echo "2. Test connection: source venv/bin/activate && python god_cli.py --test"
echo "3. Configure settings: source venv/bin/activate && python config_manager.py"
echo "4. Full installation: ./install.sh"
echo ""

# Ask user what they want to do
read -p "What would you like to do? (1-4): " choice

case $choice in
    1)
        echo "🚀 Starting God CLI chat..."
        source venv/bin/activate && python god_cli.py
        ;;
    2)
        echo "🧪 Testing connection..."
        source venv/bin/activate && python god_cli.py --test
        ;;
    3)
        echo "⚙️  Opening configuration manager..."
        source venv/bin/activate && python config_manager.py
        ;;
    4)
        echo "📥 Running full installation..."
        ./install.sh
        ;;
    *)
        echo "Invalid choice. Starting chat by default..."
        source venv/bin/activate && python god_cli.py
        ;;
esac
