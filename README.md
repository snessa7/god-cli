# God CLI - Ollama Chat Interface

A powerful Python CLI tool for interacting with your local Ollama instance. Chat with AI models, manage settings, and enjoy a smooth command-line experience.

## Features

- 🤖 **Interactive Chat**: Seamless conversation with AI models
- ⚙️ **Configurable Settings**: Customize temperature, tokens, system prompts
- 📚 **Model Management**: List and switch between available models
- 💾 **Chat History**: Persistent conversation history
- 🔧 **Easy Configuration**: Simple JSON-based config file
- 🚀 **Fast Setup**: Quick installation and ready to use

## Prerequisites

- Python 3.7 or higher
- Ollama running locally (default: http://localhost:11434)
- At least one model pulled in Ollama (e.g., `ollama pull llama2`)

## Installation

### Option 1: Install via pip (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd god-cli

# Install the package
pip install -e .

# The 'god' command should now be available globally
```

### Option 2: Direct script execution

```bash
# Make the script executable
chmod +x god_cli.py

# Run directly
./god_cli.py
```

### Option 3: Create a shell alias

Add this to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
alias god="python3 /path/to/your/god_cli.py"
```

Then reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

## Usage

### Basic Chat

```bash
# Start interactive chat
god

# Or with specific model
god --model llama2
```

### Command Line Options

```bash
god --help                    # Show help
god --test                    # Test connection
god --url http://localhost:11434  # Custom Ollama URL
god --model llama2            # Specify default model
god --config ~/.my_config.json # Custom config file
```

### Interactive Commands

Once in the chat interface:

- `help` - Show available commands
- `models` - List available models
- `config` - Show current configuration
- `clear` - Clear the screen
- `quit` / `exit` / `q` - Exit the chat

## Configuration

The tool automatically creates a configuration file at `~/.god_cli_config.json`:

```json
{
  "ollama_url": "http://localhost:11434",
  "default_model": "llama2",
  "temperature": 0.7,
  "max_tokens": 2048,
  "system_prompt": "You are a helpful AI assistant.",
  "chat_history": [],
  "max_history": 10
}
```

### Configuration Options

- **ollama_url**: URL of your Ollama instance
- **default_model**: Default model to use for chat
- **temperature**: Controls randomness (0.0 = deterministic, 1.0 = very random)
- **max_tokens**: Maximum tokens in response
- **system_prompt**: System message sent before each conversation
- **max_history**: Number of chat messages to keep in history

## Examples

### Start a chat session
```bash
$ god
🤖 God CLI - Ollama Chat Interface
==================================================
Connected to: http://localhost:11434
Default model: llama2
Type 'quit', 'exit', or 'q' to end session
Type 'help' for commands
==================================================

💬 You: Hello! How are you today?
🤖 Assistant: Hello! I'm doing well, thank you for asking. I'm here and ready to help you with any questions or tasks you might have. How can I assist you today?
```

### Test connection
```bash
$ god --test
✅ Connection successful!
📚 Available models: llama2, codellama, mistral
```

### Use a different model
```bash
$ god --model codellama
```

## Troubleshooting

### Connection Issues

1. **Make sure Ollama is running:**
   ```bash
   ollama serve
   ```

2. **Check if Ollama is accessible:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Verify your models are pulled:**
   ```bash
   ollama list
   ```

### Common Issues

- **"Cannot connect to Ollama"**: Ensure Ollama is running and accessible
- **"No models found"**: Pull at least one model with `ollama pull <model_name>`
- **Permission denied**: Make sure the script is executable (`chmod +x god_cli.py`)

## Development

### Project Structure

```
god-cli/
├── god_cli.py          # Main CLI script
├── setup.py            # Installation script
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Running Tests

```bash
# Test connection
god --test

# Test with custom URL
god --url http://localhost:11434 --test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Ensure Ollama is running and accessible
3. Verify you have at least one model pulled
4. Open an issue on GitHub with details about your setup

---

**Happy chatting with your local AI! 🚀**
