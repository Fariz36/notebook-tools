---
name: eda-copilot
description: Explore datasets in Jupyter notebooks by inspecting dataframes, summarizing schemas, checking data quality, and proposing EDA cells. Use when asked to analyze data or add exploratory analysis.
license: MIT
compatibility: opencode, claude-code, codex
metadata:
  audience: data-scientists
  workflow: analysis
---

## What I do

I help explore and understand datasets loaded in Jupyter notebooks. I:

1. Find data-loading cells and loaded variables
2. Inspect dataframe schemas, shapes, and quality
3. Summarize distributions, nulls, and key patterns
4. Propose or insert compact EDA cells if requested

## When to use me

- "Analyze this dataframe"
- "Add EDA"
- "What does this dataset look like?"
- "Explore the data in this notebook"

## How I work

### Step 1: Find the Data

If in live mode, list variables:

```bash
notebook-tools list-variables --notebook <path> --start-if-missing --pretty
```

Or search for data-loading patterns:

```bash
notebook-tools search-cells --notebook <path> --query "read_csv" --pretty
```

### Step 2: Inspect the Dataframe

```bash
notebook-tools inspect-dataframe --notebook <path> --variable-name <name> --pretty
```

This returns shape, columns, dtypes, null counts, and sample rows.

### Step 3: Read Loading Context (if needed)

```bash
notebook-tools read-cells --notebook <path> --index <N> --summary-mode compact --pretty
```

### Step 4: Propose EDA

Based on the dataframe inspection, propose:
- Schema summary
- Null/missing value analysis
- Numeric distributions
- Categorical value counts
- Recommended visualizations

If the user wants EDA cells inserted, use:

```bash
notebook-tools insert-cell --notebook <path> --position <N> --cell-type code --content "<eda-code>"
```

## Rules

- Always inspect schema before proposing analysis
- Prefer bounded summaries over full dataframe dumps
- Only read data-loading cells if the source is relevant to the question
- In file-only mode, recommend live inspection for accurate analysis
- Propose EDA cells but ask for confirmation before inserting

## Confirmation Required

Ask before inserting new cells into the notebook.

## Dependencies

Requires `notebook-tools` CLI. Live inspection requires `ipykernel`, `jupyter_client`, and `pandas`.
