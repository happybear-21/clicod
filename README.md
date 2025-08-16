# Clicod – Enterprise CLI Perl Code Generator

**clicod** is a CLI application that uses Gemini AI to generate production-ready Perl code from natural language prompts. It is designed for enterprise development with advanced security, validation, and modular architecture. Outputs include structured code and comprehensive documentation for robust, real-world deployment.

***

## Features

- **AI-driven Perl code generation:** Enterprise Perl scripts from natural language prompts.
- **Secure coding:** Input validation, error handling, safe file operations, and more.
- **Comprehensive output:** Includes architecture, dependencies, best practices, and code structure.
- **Rich CLI experience:** Syntax highlighting, interactive prompts, config management.
- **Configurable model:** Easily set Gemini API key, default model, save location.
- **Structured responses** for integration and automation.

***

## Installation

### Prerequisites

First, install `uv` if you haven't already:

```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using wget
wget -qO- https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install clicod

```bash
# Clone the repository
git clone https://github.com/happybear-21/clicod.git
cd clicod

# Install Python if needed
uv python install

# Create project and install dependencies
uv init --no-readme --no-workspace
uv sync
uv run clicod --help
```

***

## Quickstart

**First-time setup required:** Set your Gemini AI API key.

```bash
# Using uv to run clicod
uv run clicod config --set-key      # Enter your Gemini API key
uv run clicod config --show         # Review current configuration
uv run clicod test                  # Test connection to Gemini API

# Or if installed globally
clicod config --set-key
clicod config --show
clicod test
```

**Basic Usage:**
```bash
# Using uv run
uv run clicod generate "Create a CSV parser with error handling"
uv run clicod generate "Build a log file analyzer" --save
uv run clicod generate "Simple web scraper" --stream

# Or if installed globally
clicod generate "Create a CSV parser with error handling"
clicod generate "Build a log file analyzer" --save
clicod generate "Simple web scraper" --stream
```

**Interactive Mode (recommended for multi-step workflows):**
```bash
uv run clicod generate --interactive
```

***

## Configuration

Your configuration is stored in `~/.clicod/config.json`.

Options:
- Gemini API Key (`gemini_api_key`)
- Default model (`default_model`)
- Save location (`save_location`)
- Auto-save (`auto_save`)
- Streaming response (`streaming`)
- Structured JSON output (`json_format`)

Update via CLI:
```bash
uv run clicod config --set-model gemini-2.5-flash
uv run clicod config --set-save-location ~/projects
uv run clicod config --auto-save True
```


## Development Setup

### Setting up the Development Environment

```bash
# Clone the repository
git clone https://github.com/happybear-21/clicod.git
cd clicod

# Install Python and create virtual environment
uv python install
uv venv

# Install dependencies
uv pip install click rich google-genai

# Install development dependencies (optional)
uv pip install pytest black flake8 mypy

# Install in editable mode
uv pip install -e .
```

### Running in Development Mode

```bash
# Run directly with uv
uv run python main.py --help

# Or activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py --help
```

### Project Structure

```
clicod/
├── main.py            # Main CLI implementation
├── pyproject.toml      # Project configuration
├── uv.lock             # Dependency lock file
├── README.md
├── LICENSE
└── tests/              # Test files (if any)
```

***

## Command Reference

| Command              | Description                                         |
|----------------------|-----------------------------------------------------|
| `clicod generate`    | Generate production Perl code from a prompt         |
| `clicod config`      | Manage configuration and settings                   |
| `clicod test`        | Test Gemini API integration                         |
| `clicod examples`    | Show curated usage examples                         |
| `clicod about`       | Display tool info and version                       |

All commands support `--help` for details.

***

## Example Prompts

- `"Create a Perl script to monitor disk usage and send alerts"`
- `"Build a JSON parser with validation and error handling"`
- `"Generate a simple HTTP client with authentication"`
- `"Create a log rotation script for system administration"`

***

## Output Structure

Generated code includes:

- **Main Perl script:** Enterprise-ready, secure, documented, modular
- **Additional files:** Configs, modules, helpers as needed for complexity
- **Documentation:** Usage examples, features, dependencies, installation, security, notes
- **Testing:** Sample input/output, unit/integration/security tests
- **Performance & monitoring:** Error handling, signal support, logging
- **Deployment guidelines:** Permissions, updates, backup, directory structure
- **Best practices:** Modern Perl guidelines, refactoring, modularity

