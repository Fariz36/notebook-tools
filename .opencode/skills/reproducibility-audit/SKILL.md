---
name: reproducibility-audit
description: Audit Jupyter notebooks for hidden state, stale outputs, execution order issues, and non-determinism. Produces a report with findings, confidence labels, and suggested fixes.
license: MIT
compatibility: opencode
metadata:
  audience: data-scientists
  workflow: quality
---

## What I do

I audit Jupyter notebooks for reproducibility issues. I:

1. Run reproducibility diagnostics
2. Inspect flagged cells and their dependencies
3. Identify hidden state risks and stale outputs
4. Detect execution order problems
5. Report findings with confidence labels and suggested fixes

## When to use me

- "Make this reproducible"
- "Why does rerunning change results?"
- "Audit this notebook for hidden state"
- "Check if this notebook runs top-to-bottom"

## How I work

### Step 1: Run Reproducibility Check

```bash
notebook-tools check-reproducibility --notebook <path> --pretty
```

This flags:
- Out-of-order execution
- Stale outputs
- Hidden state dependencies
- Non-determinism risks

### Step 2: Inspect Flagged Cells

For each flagged cell:

```bash
notebook-tools read-cells --notebook <path> --index <N> --pretty
```

### Step 3: Check Dependencies

```bash
notebook-tools get-dependencies --notebook <path> --index <N> --mode full --pretty
```

### Step 4: Optional Live Validation

If the user approves, validate with a restart-and-run:

```bash
notebook-tools restart-kernel --notebook <path> --confirmation-token <token>
notebook-tools run-cells --notebook <path> --all --pretty
```

### Step 5: Report

Report:
- Hidden state risks
- Stale outputs
- Execution order issues
- Determinism concerns
- Suggested fixes
- Confidence label per finding (`observed`, `derived`, `heuristic`, `unverified`)

## Rules

- Always run the static check before suggesting live validation
- Label each finding with a confidence level
- Ask permission before restart-and-run validation
- In file-only mode, clearly state what cannot be verified without execution
- Prioritize fixes that make the notebook runnable top-to-bottom

## Confirmation Required

Ask before:
- Restarting the kernel
- Running all cells for validation
- Making structural changes to fix reproducibility

## Dependencies

Requires `notebook-tools` CLI. Live validation requires `ipykernel` and `jupyter_client`.
