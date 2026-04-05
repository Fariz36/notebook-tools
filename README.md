# notebook-tools

LLM-first tools for operating on Jupyter notebooks.

`notebook-tools` is a Python CLI that lets an LLM or another agent work with `.ipynb` notebooks as notebooks, not as raw JSON blobs.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## The Problem

An `.ipynb` file is not a text file. It is a JSON document that stores code, markdown, outputs, metadata, and execution state in a deeply nested structure. When an LLM agent treats a notebook like a generic file, everything becomes expensive, fragile, and error-prone.

### Concrete Example

A real student submission notebook is **924KB** with **93 cells**. The raw JSON is **740,959 characters**.

A simple task: *"What does the data loading cell output?"*

**Without notebook-tools:**
1. Read the entire 924KB file into context (~185,000 tokens)
2. Manually navigate nested JSON to find the right cell
3. Extract output from `cells[4].outputs[0].text` buried inside arrays of arrays
4. Parse through base64 images, HTML renderers, and Colab metadata

**With notebook-tools:**
```bash
notebook-tools cell-output --index 4 --notebook notebook.ipynb
```
One command. ~500 tokens. **370x less context.**

### What Goes Wrong Without Notebook-Native Tools

**Read amplification.** To find a cell by keyword, a generic agent reads the entire file (740K chars). `search-cells` returns only matches (~1K chars). To understand notebook structure, it reads everything. `list-cells` returns an outline (~3K chars).

**Edit fragility.** To insert a markdown cell, an agent must read the entire file, manually construct a valid cell object with correct `id` and `metadata`, splice it into the JSON array at the right index, and rewrite the entire 924KB file. One misplaced comma and the notebook is corrupted. `insert-cell` handles cell ID generation, metadata, and JSON validity automatically.

**No concept of notebook structure.** A generic file editor sees nested JSON. It does not understand which cells depend on which, which outputs are stale, what section a cell belongs to, or whether a cell has errors. Notebook-tools provides this through `get-dependencies`, `summarize`, and `cell-output`.

**No safe mutation.** Generic text edits on notebooks are inherently dangerous. Notebook-tools enforces revision preconditions on every mutation, requires confirmation tokens for deletions, provides structured diff summaries, and auto-generates cell IDs.

### Measured Results

Tested on a 93-cell data science notebook (924KB):

| Metric | Without tools | With tools | Improvement |
|--------|--------------|------------|-------------|
| Tokens to find a cell | ~185,000 | ~500 | 370x |
| Tokens to get an output | ~185,000 | ~500 | 370x |
| Tokens to understand structure | ~185,000 | ~3,000 | 62x |
| Notebook corruption risk | High (manual JSON surgery) | Zero (structured mutations) | Eliminated |
| Edit precision | File-level | Cell-level | Granular |
| Dependency tracing | Manual, error-prone | Automated, derived | Reliable |

## What It Does

### Read Operations (Cheap and Targeted)

| Command | What it does |
|---------|-------------|
| `list-cells` | Cell outline with summaries, status, section labels |
| `read-cells` | Read specific cells with budget controls |
| `search-cells` | Find cells by keyword in source or markdown |
| `cell-output` | Summarized output, not raw JSON |
| `get-dependencies` | Dependency graph between cells |
| `summarize` | Workflow overview, key variables, open issues |

### Mutation Operations (Safe and Notebook-Native)

| Command | What it does |
|---------|-------------|
| `edit-cell` | Replace, append, or prepend cell source |
| `insert-cell` | Add new cell at any position |
| `delete-cell` | Remove a cell (requires confirmation) |
| `move-cell` | Reposition a cell |
| `split-cell` | Split a cell at a line number |
| `merge-cells` | Merge adjacent cells |

### Live Operations (When Kernel is Available)

| Command | What it does |
|---------|-------------|
| `run-cells` | Execute specific cells or ranges |
| `kernel-state` | Inspect runtime environment |
| `list-variables` | Bounded variable inventory |
| `inspect-variable` | Type-aware variable previews |
| `inspect-dataframe` | Shape, dtypes, null counts, samples |
| `interrupt` | Interrupt running kernel |
| `restart-kernel` | Restart kernel session |
| `shutdown-kernel` | Shutdown kernel session |

## Quick Start

### Prerequisites

- Python 3.11+

### Installation

```bash
# Clone the repo
git clone https://github.com/Fariz36/notebook-tools.git
cd notebook-tools

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .

# Set the runtime directory
export NOTEBOOK_TOOLS_RUNTIME_DIR="$HOME/.local/state/notebook-tools"
```

### Verify Installation

```bash
notebook-tools list-cells --notebook examples/demo.ipynb --pretty
```

### Example Notebooks

The `examples/` directory contains notebooks for trying out the tools:

| Notebook | Purpose |
|----------|---------|
| `examples/demo.ipynb` | Clean data science workflow — imports, EDA, plot, model |
| `examples/error_demo.ipynb` | Intentionally broken — test error triage and debugging |

## Usage

### Basic Pattern

```bash
notebook-tools <command> --notebook /absolute/path/to/notebook.ipynb [options]
```

### Inspect Notebook Structure

```bash
notebook-tools list-cells --notebook examples/demo.ipynb --pretty
```

### Read One Cell

```bash
notebook-tools read-cells --notebook examples/demo.ipynb --index 2 --include-outputs --pretty
```

### Search for a Symbol

```bash
notebook-tools search-cells --notebook examples/demo.ipynb --query "df" --pretty
```

### Get Dependencies

```bash
notebook-tools get-dependencies --notebook examples/demo.ipynb --index 3 --pretty
```

### Inspect Stored Output

```bash
notebook-tools cell-output --notebook examples/demo.ipynb --index 1 --pretty
```

### Summarize a Notebook

```bash
notebook-tools summarize --notebook examples/demo.ipynb --pretty
```

### Edit a Cell

```bash
notebook-tools edit-cell --notebook examples/demo.ipynb --index 5 --edit-mode replace --content "new source" --pretty
```

### Insert a Markdown Cell

```bash
notebook-tools insert-cell --notebook examples/demo.ipynb --position 3 --cell-type markdown --content "## New Section" --pretty
```

### Run a Cell

```bash
notebook-tools run-cells --notebook examples/demo.ipynb --index 0 --pretty
```

### Inspect Runtime Variables

```bash
notebook-tools list-variables --notebook examples/demo.ipynb --start-if-missing --pretty
```

### View Available Skills

```bash
notebook-tools skills --pretty
```

## How To Set This Up For An LLM

Recommended LLM setup:

1. Expose each CLI command as a tool.
2. Make the tool wrapper return parsed JSON, not raw terminal text.
3. Keep the CLI machine-oriented.
4. Point the agent to `AGENTS.md` for operating policy, or use `notebook-tools skills` to load them programmatically.
5. Use the installed executable or a fixed venv executable path.
6. Prefer absolute notebook paths.
7. Set `NOTEBOOK_TOOLS_RUNTIME_DIR` if multiple clients should share the same runtime state location.

### Integrating Skills

Skills define higher-level workflows that orchestrate tools. There are three ways to integrate them:

#### Option 1: Cross-Agent Skills (Recommended)

This project ships with agent skills for multiple coding agents. Skills are auto-discovered from `.claude/skills/` (Claude Code), `.codex/skills/` (Codex CLI), and `.opencode/skills/` (OpenCode).

Available skills:

| Skill | Description |
|---|---|
| `notebook-orientation` | Explain what a notebook does without reading everything |
| `error-triage` | Diagnose and minimally fix failing cells |
| `eda-copilot` | Explore datasets and summarize dataframes |
| `visualization` | Improve or debug plots |
| `notebook-cleanup` | Make notebooks readable and shareable |
| `reproducibility-audit` | Detect hidden state and rerun risks |

#### Option 2: Programmatic

Use the `skills` command to load skill definitions as JSON:

```bash
# List all available skills
notebook-tools skills

# Get a specific skill
notebook-tools skills --skill "Error Triage"

# Get raw skills.md content
notebook-tools skills --raw
```

#### Option 3: File-Based

Point the LLM to `AGENTS.md` in the repo as system context or a reference document.

### Minimum Tool Wrapper Pattern

For an LLM agent, wrap commands like:

```bash
/absolute/path/to/venv/bin/notebook-tools <command> ...
```

The wrapper should:
- pass arguments predictably
- parse JSON stdout
- surface `ok`, `errors`, and `warnings`
- avoid free-form human formatting

### Recommended Agent Behavior

The LLM should:
- start with `list-cells`
- use `search-cells` and `get-dependencies` before broad reads
- use `cell-output` instead of reading raw output JSON
- use the smallest possible edit
- rerun the smallest possible slice
- report cells read, changed, and run

See:
- `AGENTS.md`
- `CLI_CONTRACT.md`

## Live-Kernel Requirements

Live commands require:
- `ipykernel`
- `jupyter_client`

These are declared in `pyproject.toml`.

Important:
- the interpreter running `notebook-tools` must be the same environment that has these packages installed
- in this repo, `venv/bin/python` is the safest choice for live commands

## File-Only Vs Live Mode

### File-Only Mode

Works on notebook files and stored outputs.

Good for:
- structure inspection
- static edits
- stored output review
- summarization
- dependency analysis

### Live Session Mode

Attaches to a kernel session.

Good for:
- execution
- runtime variable inspection
- dataframe inspection
- targeted validation after edits

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and how to add new commands or skills.

## License

MIT. See [LICENSE](LICENSE) for details.
