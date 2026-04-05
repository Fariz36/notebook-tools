---
name: notebook-cleanup
description: Make Jupyter notebooks easier to read and share. Identifies duplicated cells, improves structure, adds markdown documentation, and prepares notebooks for collaboration.
license: MIT
compatibility: opencode, claude-code, codex
metadata:
  audience: data-scientists
  workflow: maintenance
---

## What I do

I make Jupyter notebooks cleaner, more readable, and easier to share. I:

1. Analyze notebook structure for issues
2. Identify duplicated or poorly placed cells
3. Use targeted structural edits (moves, splits, merges, inserts)
4. Improve markdown documentation
5. Report all structural changes clearly

## When to use me

- "Clean this notebook"
- "Prepare this for sharing"
- "Make this notebook more readable"
- "Refactor this notebook"

## How I work

### Step 1: Analyze Structure

```bash
notebook-tools list-cells --notebook <path> --pretty
```

Look for:
- Duplicated code cells
- Long cells that should be split
- Adjacent cells that should be merged
- Missing markdown documentation
- Poor cell ordering

### Step 2: Identify Issues

Use search to find patterns:

```bash
notebook-tools search-cells --notebook <path> --query "import" --pretty
```

Check for reproducibility issues:

```bash
notebook-tools check-reproducibility --notebook <path> --pretty
```

### Step 3: Apply Structural Fixes

Move misplaced cells:

```bash
notebook-tools move-cell --notebook <path> --index <N> --position <M>
```

Split long cells:

```bash
notebook-tools split-cell --notebook <path> --index <N> --split-at <line>
```

Merge adjacent cells:

```bash
notebook-tools merge-cells --notebook <path> --index <N> --index <M>
```

Add documentation:

```bash
notebook-tools insert-cell --notebook <path> --position <N> --cell-type markdown --content "## Section Title\n\nDescription here."
```

### Step 4: Report

Report all structural changes:
- Cells moved and their new positions
- Cells split or merged
- Documentation added
- Remaining issues that need attention

## Rules

- Avoid unnecessary content rewrites
- Preserve user-authored content unless improving it is the task
- Report structural changes clearly
- Ask before deleting cells or making broad rewrites
- Flag reproducibility issues even if they are not fixed

## Confirmation Required

Ask before:
- Deleting cells
- Making broad notebook rewrites
- Running all cells after cleanup

## Dependencies

Requires `notebook-tools` CLI.
