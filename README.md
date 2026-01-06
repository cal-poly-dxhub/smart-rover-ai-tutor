# Thonny-AI-Tutor

A Thonny IDE plugin that provides an interactive PTY-based terminal interface for kiro-cli.

## Features

- **Interactive Terminal**: Full PTY-based terminal emulation for kiro-cli on Unix/Linux/macOS
- **Real-time I/O**: Non-blocking I/O with background thread processing
- **Line Editing**: Support for readline, arrow keys, and terminal control sequences
- **Cross-platform**: Works on Unix/Linux/macOS (with PTY) and Windows (with pipes fallback)
- **Thonny Integration**: Seamlessly integrated as a dockable view in Thonny IDE

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Thonny-AI-Tutor

# Install in development mode
pip install -e .

# Or build and install the wheel
python -m build
pip install dist/thonny_chatbot-*.whl
```

## Usage

### In Thonny IDE

1. Start Thonny
2. Open View > Kiro CLI Terminal
3. Click "Start" to launch kiro-cli
4. Type commands in the input field
5. Press Enter to send (Shift+Enter for multi-line input)
6. Output appears in real-time in the terminal display

### Standalone

```python
from thonnycontrib.main import KiroCliTerminal

def on_output(text):
    print(text, end='', flush=True)

terminal = KiroCliTerminal(on_output_callback=on_output)
terminal.start()

# Send commands
terminal.write("help\n")

# Cleanup
terminal.stop()
```

See [example_standalone.py](example_standalone.py) for a complete example.

## Architecture

The plugin uses a PTY (pseudo-terminal) on Unix-like systems to provide true terminal emulation:

1. Creates a master/slave PTY pair using `pty.openpty()`
2. Launches kiro-cli with stdin/stdout/stderr attached to the slave PTY
3. Reads output from master PTY in a background thread
4. Writes user input to master PTY
5. Handles terminal control sequences, line editing, and colors

For detailed technical documentation, see [KIRO_CLI_INTEGRATION.md](KIRO_CLI_INTEGRATION.md).

## Requirements

- Python 3.9+
- Thonny 4.x-5.x
- kiro-cli installed and available in PATH
- Unix/Linux/macOS for full PTY support (Windows uses pipe-based fallback)

## Documentation

- [Full Integration Guide](KIRO_CLI_INTEGRATION.md) - Complete technical documentation
- [Quick Reference](QUICK_REFERENCE.md) - API and implementation reference
- [Standalone Example](example_standalone.py) - Usage outside of Thonny

## Platform Support

| Platform | PTY Support | Features |
|----------|-------------|----------|
| Linux | ✓ | Full terminal emulation, line editing, colors |
| macOS | ✓ | Full terminal emulation, line editing, colors |
| Windows | ✗ | Basic pipe-based I/O (no line editing) |

## License

MIT License - See [LICENSE](LICENSE) file

## Contributing

Contributions are welcome! Please ensure code follows the existing style and includes appropriate documentation.