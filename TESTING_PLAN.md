# Testing Plan

## 1. Purpose
This document defines how to evaluate whether `notebook-tools` materially improves LLM agent performance on `.ipynb` tasks compared with a baseline agent that does not have notebook-native tools.

The main question is:

Can an LLM complete notebook editing and debugging tasks more accurately, more safely, and with lower token usage when it uses notebook-native tools instead of treating a notebook like a generic text or JSON file?

## 2. Primary Evaluation Question
Compare two agent configurations on the same notebook tasks:

1. Tool-enabled agent
- can use `notebook-tools`
- operates on notebook cells, outputs, and live runtime state

2. Baseline agent
- cannot use `notebook-tools`
- can only operate using generic file reads/edits and optionally generic Python or shell commands

The comparison should measure whether the tool-enabled agent is better at:
- locating the right notebook context
- making smaller edits
- preserving notebook validity
- using less context
- solving notebook-native tasks that depend on cells, outputs, and runtime state

## 3. Evaluation Categories
### 3.1 File-Only Editing Tasks
These tasks should not require a live kernel.

Examples:
- insert a markdown explanation before a modeling cell
- split a long code cell into two smaller cells
- move a setup cell earlier in the notebook
- merge two adjacent markdown cells
- summarize notebook structure
- retrieve outputs stored in a specific cell
- identify likely dependencies for a plotting cell

### 3.2 Live Execution Tasks
These tasks require a live kernel.

Examples:
- run a target cell and summarize the error
- inspect runtime variables after executing a setup cell
- inspect a dataframe in memory
- fix a failing cell and rerun only the necessary slice
- verify kernel working directory and Python version

### 3.3 Reproducibility and Workflow Tasks
These tasks measure notebook-native reasoning quality.

Examples:
- identify cells that depend on hidden state
- explain why a later cell depends on an earlier definition
- summarize stored notebook issues such as stale or failing outputs
- prepare a notebook for top-to-bottom execution

## 4. Benchmark Task Set
Build a benchmark set of notebooks with clear task prompts.

Recommended benchmark size for a first pass:
- 10 small notebooks
- 10 medium notebooks
- 5 larger notebooks

Each notebook should include a mix of:
- markdown and code cells
- stored outputs
- at least some multi-cell dependencies
- a few notebooks with runtime errors
- a few notebooks with hidden-state or ordering problems

Each notebook should have 3-8 prompts so the benchmark covers:
- read-only tasks
- structural edit tasks
- debugging tasks
- live inspection tasks

## 5. Test Matrix
For each prompt, run both configurations:

1. Tool-enabled agent
2. Baseline agent

Keep these fixed across runs:
- same model
- same temperature
- same max turn budget
- same notebook and prompt
- same success rubric

If possible, run each task multiple times to reduce run-to-run variance.

## 6. Success Metrics
### 6.1 Task Completion
Measure:
- task solved correctly
- task partially solved
- task failed

### 6.2 Edit Quality
Measure:
- notebook still valid JSON and valid notebook structure
- correct cell targeted
- edit minimality
- no unintended changes outside task scope

### 6.3 Execution Quality
For live tasks, measure:
- command success rate
- fix verified by rerun
- whether the agent reran the minimal useful slice instead of excessive execution

### 6.4 Token Efficiency
Measure:
- total prompt + tool-response tokens consumed per task
- number of notebook cells fully read
- number of cells touched unnecessarily
- ratio of targeted reads to broad reads

### 6.5 Safety and Transparency
Measure:
- whether destructive actions required confirmation
- whether the agent clearly reported cells read, changed, and run
- whether the agent distinguished observed vs inferred facts

## 7. Recommended Rubric
Score each task from 0 to 3.

0:
- incorrect or failed

1:
- partially correct but wrong scope, wrong edit, or missing validation

2:
- correct outcome with some inefficiency or excess context use

3:
- correct, minimal, well-scoped, and clearly reported

For each task also record:
- tokens used
- cells read
- cells changed
- cells run
- whether confirmation policy was respected

## 8. Suggested Task Families
### 8.1 Output Retrieval
Prompt examples:
- "What error does cell 5 produce?"
- "Summarize the output of the training cell."

Expected advantage of tools:
- `cell-output` should avoid reading the full notebook or raw JSON outputs

### 8.2 Dependency Reasoning
Prompt examples:
- "What does this plot depend on?"
- "Where is `df` defined before this cell?"

Expected advantage of tools:
- `get-dependencies` should reduce broad notebook reading

### 8.3 Structural Editing
Prompt examples:
- "Move the imports to the top."
- "Split this long data-cleaning cell into two cells."

Expected advantage of tools:
- structural edits remain notebook-native and avoid manual JSON surgery

### 8.4 Debugging
Prompt examples:
- "Fix the failing import."
- "Why is this cell failing?"

Expected advantage of tools:
- output summaries and targeted reruns reduce unnecessary exploration

### 8.5 Runtime Inspection
Prompt examples:
- "What variables exist after setup runs?"
- "Inspect the dataframe called `df_train`."

Expected advantage of tools:
- runtime inspection should avoid ad hoc probe code written into the notebook

## 9. What To Measure In The Comparison
The most important comparison is not just raw success rate.

Also compare:
- read amplification
- edit amplification
- execution amplification
- notebook corruption risk
- need for manual rescue after the run

Recommended derived metrics:
- average cells read per successful task
- average number of commands per successful task
- average edits outside target cells
- percentage of tasks completed without full-notebook reads

## 10. Human Review Checks
For a smaller subset of benchmark runs, have a human reviewer score:
- whether the right cells were targeted
- whether the explanation matched notebook reality
- whether the edit was the smallest reasonable change
- whether the result would be trusted in real notebook work

## 11. Failure Analysis
When a run fails, classify the failure:
- wrong cell targeting
- wrong dependency reasoning
- excessive context reads
- notebook JSON corruption
- runtime misuse
- stale-session confusion
- poor explanation despite correct action

This matters because the product goal is not only to solve tasks, but to solve them in a notebook-native way.

## 12. Recommended First Evaluation Protocol
Start with a simple protocol:

1. Choose 10 notebook tasks.
2. Run the same model with tools enabled.
3. Run the same model without tools.
4. Score each run on correctness, minimality, tokens, and trust.
5. Review the deltas.

If the tool-enabled agent is not clearly better on:
- dependency tasks
- output tasks
- structural notebook edits
- runtime inspection tasks

then the tool layer is not yet delivering enough notebook-native value.

## 13. What "Good" Looks Like
This tool layer is successful if the tool-enabled agent consistently:
- reads fewer cells
- emits fewer raw notebook dumps
- makes more localized edits
- breaks notebooks less often
- solves more notebook-native tasks correctly
- provides more trustworthy reports of what it changed and ran

## 14. Recommendation
The strongest test is an agentic A/B test:

- same LLM
- same prompts
- same notebooks
- with tools vs without tools

That is the clearest way to show whether `notebook-tools` is actually useful for LLM-first notebook operation rather than just being another CLI.
