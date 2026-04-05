---
name: notebook-orientation
description: Explain what a Jupyter notebook does by inspecting structure, summarizing workflow, and reading only key cells. Use when asked to walk through, summarize, or understand a notebook.
license: MIT
compatibility: opencode
metadata:
  audience: data-scientists
  workflow: inspection
---

## What I do

I help you understand a Jupyter notebook without reading every cell. I use `notebook-tools` to:

1. List the notebook structure with `list-cells`
2. Summarize the workflow with `summarize`
3. Read only the key cells that define the notebook's purpose
4. Report sections, data flow, major outputs, and unknowns

## When to use me

- "What does this notebook do?"
- "Walk me through this notebook"
- "Explain the structure of this notebook"
- "What are the main sections here?"

## How I work

### Step 1: Structure

```bash
notebook-tools list-cells --notebook <path> --pretty
```

This gives cell types, execution counts, and short summaries without pulling full content.

### Step 2: Workflow Summary

```bash
notebook-tools summarize --notebook <path> --pretty
```

This returns a high-level workflow summary with major sections and key outputs.

### Step 3: Targeted Reads

Only read cells that are essential to answer the question. Use:

```bash
notebook-tools read-cells --notebook <path> --index <N> --summary-mode compact --pretty
```

Or search for specific content:

```bash
notebook-tools search-cells --notebook <path> --query "<term>" --pretty
```

### Step 4: Report

Report:
- Notebook mode: `file_only` or `live_session`
- Major sections identified
- Data flow and key variables
- Major outputs
- Unknowns or risks

## Rules

- Never read the entire notebook by default
- Always start with `list-cells` before deeper reads
- Use `search-cells` to find specific content before broad reads
- Report what was observed vs inferred
- In file-only mode, explicitly state that runtime validation is unavailable

## Dependencies

Requires `notebook-tools` CLI installed. All commands need `--notebook <absolute-path>`.
