# Contributing to notebook-tools

Thank you for contributing to `notebook-tools`. This document covers how to set up, develop, test, and extend the project.

## Development Setup

### Prerequisites

- Python 3.11+
- `pip`

### Quick Start

```bash
# Clone the repo
git clone https://github.com/Fariz36/notebook-tools.git
cd notebook-tools

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify the CLI works
notebook-tools list-cells --notebook tests/fixtures/simple.ipynb
```

## Running Tests

```bash
# Run the full test suite
python -m unittest discover -s tests -p "test_*.py"

# Run a single test file
python -m unittest tests/test_cli.py
```

## Code Style

This project follows standard Python conventions. Before committing:

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## Adding a New Command

Commands live in `src/notebook_tools/commands/`. Each command is a module that:

1. Accepts parsed arguments
2. Returns a structured Python dict
3. The CLI layer serializes it to JSON

### Steps

1. Create `src/notebook_tools/commands/my_command.py`
2. Implement a `run(args)` function that returns a dict
3. Register the subcommand in `src/notebook_tools/cli.py`
4. Add tests in `tests/test_my_command.py`
5. Update `CLI_CONTRACT.md` with the new command contract

### Response Contract

Every command must return a dict matching the standard envelope:

```python
{
    "ok": True,
    "command": "my-command",
    "data": {...},
    "warnings": [],
    "errors": [],
    "meta": {...}
}
```

See `CLI_CONTRACT.md` for the full specification.

## Adding a Skill

Skills are higher-level workflows documented in `AGENTS.md`. To add one:

1. Add a new section to `AGENTS.md` following the existing template
2. Create a `SKILL.md` in `.claude/skills/<skill-name>/`, `.codex/skills/<skill-name>/`, and `.opencode/skills/<skill-name>/`
3. Include: Goal, Trigger phrases, Suggested tool flow, Expected output
4. Reference the skill in the README's "How To Set This Up For An LLM" section

## Pull Requests

- Keep PRs focused on one feature or fix
- Include tests for new commands
- Update documentation if the CLI contract changes
- Follow the existing code style

## Reporting Issues

When filing a bug, include:

- The command you ran
- The notebook file (or a minimal reproduction)
- The expected vs actual JSON output
- Python version and OS

## Architecture Overview

```
src/notebook_tools/
  cli.py              # Entry point, argument parsing, JSON serialization
  commands/           # Individual command handlers
  notebook/           # Notebook model, loader, selectors, search, mutations
  runtime/            # Kernel management, execution, variable inspection
  schemas/            # Request/response schema definitions
  utils/              # Shared helpers (JSON I/O, truncation, errors)
```

## Design Principles

- **Machine-first**: The primary consumer is an LLM agent, not a human typing at a terminal
- **Notebook-native**: Operate on cells, outputs, and kernel state, not raw JSON
- **Token-efficient**: All reads are bounded and summarizable by default
- **Safe by default**: Destructive actions require explicit confirmation
- **Structured errors**: Domain failures return JSON errors, not exit codes
