# Notebook Agent Skills

## Purpose

This document defines how an LLM agent should use `notebook-tools` to operate on `.ipynb` notebooks safely, accurately, and token-efficiently.

The main rule is simple:

> **Read as little as possible, change as little as possible, run as little as necessary.**

## Core Behavior

The agent should:
- reason in terms of cells, outputs, runtime state, and dependencies
- prefer summaries and search results before full cell reads
- distinguish file state from kernel state
- keep edits minimal and localized
- rerun only the smallest valid execution slice
- state what is observed, inferred, and unverified

The agent should **not**:
- read the entire notebook by default
- dump large outputs or tables when a summary is enough
- claim runtime facts in file-only mode
- restart the kernel or delete cells without confirmation
- apply broad notebook rewrites unless explicitly requested

## Default Workflow

For most requests, follow this sequence:

1. Run `list-cells` to understand structure
2. Use `search-cells` or `get-dependencies` to narrow scope
3. Run `read-cells` only on the relevant cells
4. Inspect outputs or runtime state only if needed
5. Apply the smallest correct edit
6. Run the smallest useful verification step
7. Report cells read, cells changed, cells run, and remaining uncertainty

## Mode Awareness

### Live Session Mode

In live mode, the agent may:
- run cells
- inspect variables
- inspect dataframes
- validate fixes against runtime results

### File-Only Mode

In file-only mode, the agent may:
- inspect notebook structure and source
- edit cells
- infer likely dependencies heuristically
- identify likely stale outputs from metadata

In file-only mode, the agent must explicitly say when runtime validation is unavailable.

## Read Policy

Prefer this order:

1. `list-cells`
2. `search-cells`
3. `get-dependencies`
4. `read-cells`
5. `cell-output`
6. runtime inspection commands

Rules:
- do not read outputs unless the task depends on execution results
- do not read broad cell ranges if search or dependencies can narrow the target
- use `compact` or `standard` summaries before `full`
- if a cell is very long, read the target cell first and only read neighboring cells if required

## Edit Policy

- edit only target cells unless restructuring is clearly required
- preserve cell ordering unless reordering is part of the request
- preserve user-authored markdown unless improving documentation is the task
- use revision preconditions for edits whenever available

Before editing, know:
- which cell is being changed
- why that cell is the right place to change
- what minimal change is sufficient

## Execution Policy

Prefer:

1. rerun one cell
2. rerun the target cell plus immediate dependencies if needed
3. rerun affected downstream cells only when validation requires it
4. `run all` only when the user requests it or reproducibility validation requires it

Avoid expensive execution by default. If a fix may depend on hidden state, say so explicitly and recommend a stronger validation step.

## Runtime Inspection Policy

- start with `list-variables`
- inspect only variables relevant to the task
- prefer `inspect-dataframe` over generic inspection for pandas objects
- request bounded samples and summaries, not full object dumps

Inspect runtime state only when it improves the answer materially.

## Confirmation Policy

**Must ask for confirmation before:**
- deleting cells
- restarting the kernel
- running all cells in a long notebook
- installing packages
- making broad or destructive notebook rewrites

**May proceed without confirmation for:**
- targeted reads
- narrow code edits that directly satisfy the request
- rerunning a small set of cells needed to verify a fix, unless the user asked for no execution

## Reporting Policy

Responses should be concise and explicit. Report:
- notebook mode: `live_session` or `file_only`
- cells read
- cells changed
- cells run
- whether outputs were summarized or truncated
- what was directly observed
- what was inferred heuristically
- any remaining risks or unverified assumptions

## Heuristic Labels

Use these labels consistently:

| Label | Meaning |
|---|---|
| `observed` | directly seen in source, output, or runtime state |
| `derived` | computed from execution history or structured metadata |
| `heuristic` | inferred from static analysis or patterns |
| `unverified` | plausible but not confirmed |

---

## Skill Workflows

### Notebook Orientation

**Goal:** Explain what the notebook does without reading everything.

**Triggers:** "What does this notebook do?", "Walk me through this notebook"

**Flow:**
1. `list-cells`
2. `summarize` (workflow mode)
3. `read-cells` for only the key cells
4. Report sections, data flow, major outputs, and unknowns

**Expected output:** Concise summary with cell map, key dependencies, risks or missing context.

---

### Error Triage

**Goal:** Diagnose and minimally fix a failing notebook cell.

**Triggers:** "Fix this error", "Why is this cell failing?"

**Flow:**
1. `read-cells` for the failing cell
2. `cell-output` for traceback summary
3. `get-dependencies` for upstream context
4. Optionally inspect runtime state if live mode helps
5. `edit-cell` with the minimal fix
6. `run-cells` on the smallest valid slice
7. Report root cause, fix, and validation scope

**Expected output:** Root cause, proposed minimal fix, exact cells read/edited/run, rerun recommendation.

---

### EDA Copilot

**Goal:** Inspect and summarize a dataset or dataframe.

**Triggers:** "Analyze this dataframe", "Add EDA"

**Flow:**
1. `list-variables`
2. `inspect-dataframe`
3. Optionally `read-cells` for data-loading cells
4. Propose or insert compact EDA cells if requested

**Expected output:** Schema summary, quality checks, recommended visualizations, inserted analysis cells if approved.

---

### Visualization Assistant

**Goal:** Improve or debug a plot.

**Triggers:** "Make a better chart", "Why is this plot wrong?"

**Flow:**
1. Find plotting cells via `search-cells`
2. Read the plotting cell and immediate upstream data prep cells
3. Inspect plot output summary if available
4. Minimally edit plot code
5. Rerun target plot cells only

**Expected output:** Chart critique, improved plotting code, interpretation guidance.

---

### Notebook Cleanup

**Goal:** Make the notebook easier to read and share.

**Triggers:** "Clean this notebook", "Prepare this for sharing"

**Flow:**
1. `list-cells`
2. Identify duplicated or poorly placed cells
3. Use targeted edits, inserts, moves, splits, or merges
4. Avoid unnecessary content rewrites
5. Report structural changes clearly

**Expected output:** Reordered cells when justified, reduced duplication, improved markdown, clearer sectioning, reproducibility warnings.

---

### Reproducibility Auditor

**Goal:** Identify hidden state and rerun risks.

**Triggers:** "Make this reproducible", "Why does rerunning change results?"

**Flow:**
1. `check-reproducibility`
2. Inspect flagged cells with `read-cells`
3. Inspect dependencies for risky cells
4. Optionally ask permission for restart-and-run validation
5. Report findings with confidence labels

**Expected output:** Reproducibility report, suggested fixes, optional restart-and-run verification.

---

## Final Principle

The tool layer exists to let the LLM act like a careful notebook operator, not a raw file editor.

When uncertain, prefer narrower reads, narrower edits, and clearer reporting.
