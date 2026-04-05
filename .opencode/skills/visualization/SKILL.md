---
name: visualization
description: Improve or debug plots in Jupyter notebooks. Finds plotting cells, critiques visualizations, applies minimal fixes, and reruns only the affected cells.
license: MIT
compatibility: opencode
metadata:
  audience: data-scientists
  workflow: visualization
---

## What I do

I help create, improve, and debug visualizations in Jupyter notebooks. I:

1. Find plotting cells via search
2. Read the plotting code and upstream data prep
3. Critique the visualization
4. Apply minimal fixes
5. Rerun only the target plot cells

## When to use me

- "Make a better chart"
- "Why is this plot wrong?"
- "Improve this visualization"
- "Add a plot showing X vs Y"

## How I work

### Step 1: Find the Plotting Cell

```bash
notebook-tools search-cells --notebook <path> --query "plt" --pretty
```

Also search for common plotting libraries:

```bash
notebook-tools search-cells --notebook <path> --query "seaborn" --pretty
notebook-tools search-cells --notebook <path> --query "plotly" --pretty
```

### Step 2: Read the Plotting Cell and Context

```bash
notebook-tools read-cells --notebook <path> --index <N> --pretty
```

Read immediate upstream data prep cells if needed:

```bash
notebook-tools get-dependencies --notebook <path> --index <N> --mode upstream --pretty
```

### Step 3: Inspect Plot Output (if available)

```bash
notebook-tools cell-output --notebook <path> --index <N> --pretty
```

### Step 4: Critique and Fix

Common issues to check:
- Unreadable labels or legends
- Overplotting
- Misleading scales or axes
- Missing titles or annotations
- Incorrect chart type for the data

Apply the minimal fix:

```bash
notebook-tools edit-cell --notebook <path> --index <N> --edit-mode replace --content "<fixed-code>"
```

### Step 5: Validate

```bash
notebook-tools run-cells --notebook <path> --index <N> --pretty
```

## Rules

- Only read the plotting cell and its immediate upstream dependencies
- Critique the visualization before proposing changes
- Apply the smallest fix that addresses the issue
- In file-only mode, describe expected output changes since live validation is unavailable

## Confirmation Required

Ask before inserting new visualization cells or restructuring existing ones.

## Dependencies

Requires `notebook-tools` CLI. Live validation requires `ipykernel` and `jupyter_client`.
