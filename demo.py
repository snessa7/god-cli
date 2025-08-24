#!/usr/bin/env python3
"""
Demo script for God CLI
Shows the tool's capabilities without requiring user interaction
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from god_cli import OllamaCLI

def demo():
    """Run a demonstration of the God CLI tool"""
    print("🎭 God CLI Demo Mode")
    print("=" * 50)
    
    # Initialize CLI
    cli = OllamaCLI()
    
    print(f"🔧 Configuration loaded from: {cli.config_path}")
    print(f"🌐 Ollama URL: {cli.base_url}")
    print(f"🤖 Default Model: {cli.config.get('default_model')}")
    print(f"🌡️  Temperature: {cli.config.get('temperature')}")
    print(f"📝 Max Tokens: {cli.config.get('max_tokens')}")
    print(f"💬 System Prompt: {cli.config.get('system_prompt')}")
    
    print("\n" + "=" * 50)
    print("🧪 Testing Connection...")
    
    if cli.test_connection():
        print("✅ Connection successful!")
        
        # List available models
        models = cli.list_models()
        if models:
            print(f"📚 Available models: {', '.join(models)}")
        else:
            print("⚠️  No models found (this is normal if no models are pulled)")
    else:
        print("❌ Connection failed!")
        print("💡 Make sure Ollama is running with: ollama serve")
        print("💡 Pull a model with: ollama pull llama2")
    
    print("\n" + "=" * 50)
    print("🎯 Demo Complete!")
    print("\nTo start using God CLI:")
    print("1. Quick start: ./quick_start.sh")
    print("2. Direct usage: ./god_cli.py")
    print("3. Full install: ./install.sh")
    print("4. Configure: ./config_manager.py")
    
    print("\n🚀 Happy chatting!")

if __name__ == "__main__":
    demo()
