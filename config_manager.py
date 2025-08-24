#!/usr/bin/env python3
"""
Configuration Manager for God CLI
Allows easy modification of settings through an interactive interface
"""

import json
import os
import sys
from pathlib import Path

def load_config(config_path):
    """Load configuration from file"""
    default_config = {
        "ollama_url": "http://localhost:11434",
        "default_model": "gemma3:1b",
        "temperature": 0.7,
        "max_tokens": 2048,
        "system_prompt": "You are a helpful AI assistant.",
        "chat_history": [],
        "max_history": 10
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    return default_config

def save_config(config, config_path):
    """Save configuration to file"""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_input(prompt, default_value, input_type=str):
    """Get user input with default value"""
    while True:
        try:
            if input_type == float:
                user_input = input(f"{prompt} (default: {default_value}): ").strip()
                if not user_input:
                    return default_value
                return float(user_input)
            elif input_type == int:
                user_input = input(f"{prompt} (default: {default_value}): ").strip()
                if not user_input:
                    return default_value
                return int(user_input)
            else:
                user_input = input(f"{prompt} (default: {default_value}): ").strip()
                if not user_input:
                    return default_value
                return user_input
        except ValueError:
            print("Invalid input. Please try again.")

def main():
    config_path = os.path.expanduser("~/.god_cli_config.json")
    
    print("⚙️  God CLI Configuration Manager")
    print("=" * 40)
    
    # Load current config
    config = load_config(config_path)
    
    while True:
        print(f"\nCurrent Configuration:")
        print(f"1. Ollama URL: {config['ollama_url']}")
        print(f"2. Default Model: {config['default_model']}")
        print(f"3. Temperature: {config['temperature']}")
        print(f"4. Max Tokens: {config['max_tokens']}")
        print(f"5. System Prompt: {config['system_prompt'][:50]}...")
        print(f"6. Max History: {config['max_history']}")
        print(f"7. Save and Exit")
        print(f"8. Exit without saving")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == "1":
            config['ollama_url'] = get_input("Enter Ollama URL", config['ollama_url'])
        elif choice == "2":
            config['default_model'] = get_input("Enter default model name", config['default_model'])
        elif choice == "3":
            config['temperature'] = get_input("Enter temperature (0.0-1.0)", config['temperature'], float)
            config['temperature'] = max(0.0, min(1.0, config['temperature']))
        elif choice == "4":
            config['max_tokens'] = get_input("Enter max tokens", config['max_tokens'], int)
            config['max_tokens'] = max(1, config['max_tokens'])
        elif choice == "5":
            print("Enter new system prompt (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "" and lines:
                    break
                lines.append(line)
            if lines:
                config['system_prompt'] = "\n".join(lines)
        elif choice == "6":
            config['max_history'] = get_input("Enter max history size", config['max_history'], int)
            config['max_history'] = max(1, config['max_history'])
        elif choice == "7":
            if save_config(config, config_path):
                print("✅ Configuration saved successfully!")
                print(f"Config file: {config_path}")
            else:
                print("❌ Failed to save configuration")
            break
        elif choice == "8":
            print("Exiting without saving changes.")
            break
        else:
            print("Invalid option. Please select 1-8.")

if __name__ == "__main__":
    main()
