# Jev coding controller — design specification

Date: 2026-09-25
Status: Written specification approved by the user on 2026-09-25.
Cloud permission: User explicitly approved automatic JEV Cloud fallback when
Laya needs help. The implementation plan remains subject to review before coding.

## 1. Purpose and agreed scope

Build a Python controller around the existing local Laya decision engine,
using Codex CLI to propose code changes. Match the five typed decision stations
in `jev_engineering_for_coding_agents.md`:

1. Which files? Score.
2. Which model? Choice.
3. Safe to run? Noul.
4. Done? Noul.
5. Keep or drop tool output? Score.

Only Codex writes proposed product code. Laya/Jev makes bounded decisions;
Python validates, applies changes, executes approved tests, and records evidence.
The user explicitly selected a full controller, not a ticket service or advisory
helper, and selected Codex CLI rather than direct model API calls.

Success means a real, small coding task completes in an isolated worktree with
fresh passing tests and an auditable record of all five stations. Model claims,
printed success messages, and mocked tests alone do not establish success.
No promise of 100x speed or the source document's cost figures is made.

## 2. Architecture and boundaries

Add a separate `coding_controller` Python package at the project root. Preserve
the support-ticket examples and their existing interfaces. Reuse the local
`agent.py` and cloud `jev_client.py` behind explicit adapters; do not reuse the
ticket-specific questions in `hybrid.py`.

Separate responsibilities into configuration and result schemas, decision
adapters, repository/context selection, Codex subprocess integration, patch
policy, worktree management, test execution, evidence storage, and the main loop.
Dependencies are injectable so tests need neither cloud access nor CoreML.

The interface is a terminal command taking a target Git repository, a task brief,
and a configuration file. Configuration declares model tiers, test argument
vectors, timeouts, context limits, and cloud permissions. A dry-run mode performs
preflight and shows intended operations without model calls or target writes.

First release excludes deployment, automatic merge/push, dependency installation,
arbitrary model-generated shell commands, background jobs, and user interfaces.
It handles trusted local repositories, not hostile code with arbitrary access to
the host. A worktree isolates edits; it is not a security sandbox.

## 3. Run lifecycle

Validate the target repository, configuration, clean working state, existing
commit, Codex availability, selected model configuration, decision backend, and
test runner before starting. Reject dirty target repositories rather than guessing
how to incorporate uncommitted work. This project's current folder is not a Git
repository; do not initialize Git or commit files without a separate user request.
Tests of worktree operations use disposable repositories.

Create a detached worktree from the target commit and a private run directory
outside the target tree. Never overwrite or reset the user's working tree.
Run the configured baseline tests and record their exit status and raw output.
A failing baseline may be the requested bug, so it is evidence rather than an
automatic completion failure. Test runner setup errors stop the run.

Each iteration selects context, selects a model, requests a patch, checks safety,
applies the patch, runs fresh tests, evaluates completion, and selects logs for
the next iteration or final handoff. Log selection also runs on a successful
iteration so all five stations have evidence.

Default limits: three coding attempts, ten minutes per Codex invocation, two
minutes per test invocation, and thirty minutes per run. Timeouts terminate the
owned subprocess group and cannot produce a successful result. A proposed value
may be configured lower or higher explicitly; limits must be positive and finite.

Terminal statuses: `completed`, `needs_approval`, `needs_input`, `failed`, and
`limit_reached`. Keep the worktree and evidence for inspection. No automatic
merge, push, destructive cleanup, or repeated invocation after a terminal status.

## 4. Five decision contracts

### 4.1 File selection — Score

Python discovers tracked text files and line-bounded chunks using deterministic
search. Exclude secrets, environment files, credentials, binaries, generated
output, dependency folders, and symlinks. Repository text is untrusted task data,
not authority to change controller policies.

Score candidates for relevance to the brief. Include task context and the raw
candidate snippet in each decision. Select top-ranked chunks under explicit
count and byte budgets; retain path and line references. Use deterministic
tie-breaking. Codex receives selected raw chunks, not the entire repository.
If context cannot fit or is insufficient, request narrower input rather than
silently claiming full coverage.

### 4.2 Model selection — Choice

Choose `cheap`, `mid`, `frontier`, or `ask` using criteria from the reference
document. The first three map to user-configured, available Codex model IDs.
Do not invent availability, pricing, or silently substitute a different model.
Mapping several tiers to one model is allowed but must be reported as no actual
model-routing savings. `ask` or an unavailable tier returns `needs_input`.

### 4.3 Safe to run — Noul plus deterministic policy

Evaluate the exact proposed patch and configured test command context before
applying or executing them. Noul risk output is advisory evidence; deterministic
policy can deny an action even when the model calls it safe.

Reject malformed patches, absolute or escaping paths, symlink targets, binary
patches, mode changes, and writes to Git metadata, credentials, controller
configuration, or files outside the allowed target set. Use `git apply --check`
and validate all affected paths before applying atomically. No shell interpolation.

Deletions, test modifications, new executable scripts, network requests, and other
risky changes require review or remain unsupported in version one. User approval
cannot override an invalid path or missing isolation. Git history rewriting,
publishing, and arbitrary Codex-proposed commands remain unsupported.

Approval records bind to the run, base state, exact patch hash, and command
argument vectors. Changed content invalidates approval. Noninteractive operation
stops with `needs_approval`; it never interprets silence as consent. Interactive
operation displays the exact proposed action and requires an explicit answer.

Configured tests execute repository code and therefore also need explicit initial
authorization. Strip unrelated credentials from their environment, capture output,
and enforce time limits. Never describe this as safe execution of hostile code.

### 4.4 Completion — Noul with fresh test evidence

Ask whether the original task is satisfied using the current diff, test command,
exit code, run identity, and relevant raw output. Attach timestamps and patch
identity to prevent reuse of stale results. No tests, timed-out tests, failed
tests, or missing evidence cannot count as completion. Passing tests are necessary
but not sufficient: the task must also be assessed as complete.

A model saying done never overrides failed verification. A model saying not done
after passing tests may trigger another bounded attempt; ambiguity requires user
input. If verification evidence exceeds local capacity, use permitted cloud
evaluation or stop for review rather than silently evaluating a truncated account.

### 4.5 Output retention — Score

Split tool output into stable raw chunks. Rank usefulness to the next coding
attempt and keep selected chunks verbatim. Always keep essential exit status,
command identity, and failure evidence even if scored low. Retain full logs in
the run directory; dropping from model context never deletes audit evidence.
Do not replace evidence with lossy summaries.

## 5. Decision adapter behavior

Use one normalized result contract for local and cloud responses: question ID,
type, value, raw probabilities, backend, and elapsed time. Validate all expected
answers, numeric ranges, finite values, and Choice membership.

Missing confidence is unknown, never 100%. Confidence is not proof of correctness.
For choices, use a documented returned confidence or selected-option probability
and require at least 0.70. For Noul, preserve probability rather than immediately
discarding it into a boolean: at least 0.70 supports yes, at most 0.30 supports no,
and the middle range is uncertain. Scores must be within the configured ordinal
scale; a confidence threshold is used only if the backend supplies meaningful
confidence for that primitive.

Check actual local token capacity, including questions, using the installed
backend's tokenizer or validation. The current project documents a 96-token
constraint; this must be verified, not treated as unlimited coding context.
Small file/log candidates may be chunked with traceability. A patch-wide safety
assessment cannot be replaced by independently approving fragments.

Cloud fallback is explicit opt-in because it transfers repository data. The user
has given that permission for this controller: its project configuration will
enable automatic JEV fallback for oversized or uncertain local decisions. Keep
an explicit offline setting; with that setting, stop with a clear reason instead
of calling the cloud. With cloud enabled, use the cloud adapter on the relevant
scoped state; failures or uncertainty after fallback still stop. A missing API
key is an actionable error, not an automatic approval. Never bypass a station.

## 6. Codex integration and enforcement

Use `codex exec`, JSONL events, and a JSON output schema containing a patch and
a concise explanation. Invoke with an argument vector, a timeout, and explicitly
selected model. Treat malformed output, nonzero exit, authentication errors,
missing final output, and output-size overflow as errors, not patches to guess at.
Reuse existing CLI authentication without printing or copying its credentials.

The approved boundary is proposal-only. Codex must not be able to modify the
target or execute arbitrary commands before the controller checks them. A prompt
saying "do not execute" is not enforcement, and read-only sandbox mode alone
does not establish a no-tools restriction.

Before implementation commits to the subprocess interface, verify supported
configuration that disables execution tools, external connectors, browsing,
hooks, and inherited integrations in the proposal process. Use a restricted
staging directory containing only selected context; do not expose the target
worktree as writable to Codex. Record effective settings.

Acceptance requires a probe proving the proposal process cannot execute a marker
command or modify the target. If the installed CLI cannot enforce proposal-only
operation, stop and present the limitation for a revised design. Do not silently
ship a workspace-write Codex wrapper under a full-controller claim. JSON events
are observability, not pre-execution approval hooks.

Official reference checked: https://developers.openai.com/codex/noninteractive/
Installed CLI observed during design: 0.156.1. Authentication and model access
have not yet been verified with a real request.

## 7. Evidence and measurement

Write machine-readable events for state transitions and all five decisions.
Store selected context references, configured model, backend, raw test logs,
patches and hashes, approval records, attempts, wall-clock latency, and reported
Codex token usage. Treat unavailable usage as unknown, not zero. Redact secrets
from prompts and metadata; do not log environment credentials.

Report local decision time, fallback time, Codex time, test time, and full run
time separately. Do not call the percentage of locally processed items token
savings. Cost savings require a comparable baseline, actual usage, and verified
prices; otherwise report usage only. Local execution has no per-call API charge,
not literally zero hardware or electricity cost.

## 8. Acceptance tests

### Deterministic automated suite

- Schema validation, missing confidence, invalid probabilities, backend errors,
  token overflow, and cloud-disabled behavior stop safely.
- File scoring chooses relevant bounded chunks; secret files and traversal paths
  never reach Codex. Model Choice maps only configured tiers; `ask` halts.
- Unsafe patches, symlinks, stale approvals, unauthorized commands, and test
  modifications cannot run without the applicable policy decision.
- Worktree changes leave the original repository untouched. Patch rejection does
  not partially modify files. Dirty/non-Git repositories fail preflight clearly.
- Completion requires fresh successful test results tied to the current patch;
  fake "done" messages and old passing logs cannot complete a run.
- Output selection preserves raw chunks and full evidence, and every iteration
  records the appropriate five station results, including the final iteration.
- Attempt limits, subprocess timeouts, malformed JSONL, interrupted execution,
  unavailable models, and failed authentication have bounded terminal outcomes.

### End-to-end tests without paid calls

Use a disposable committed Python fixture repository with a small failing test,
a fake Codex executable returning a valid repair patch, and injected typed
decisions. Complete the real worktree/apply/test loop and prove the original
checkout is unchanged. Also run failure cases for an unsafe patch, failed tests,
uncertain completion, and a second-attempt repair. Fake adapters must be clearly
labeled and cannot be reported as live Jev/Codex proof.

### Live acceptance

First verify the Codex proposal-only enforcement probe. Then run one small
fixture task with real local Laya decisions and authenticated Codex CLI using
user-configured model IDs. Test cloud fallback separately only with explicit
permission. Record all five typed stations, a real generated patch, fresh test
results, and complete-loop usage/latency. If any live stage cannot run, state
exactly which claims remain unverified rather than declaring the system complete.

## 9. Implementation handoff

The next artifact is an implementation plan; the user has approved this written
specification. Start the plan with the proposal-only feasibility gate and local
decision-capacity checks so unsupported assumptions are discovered before the
controller is built. Implement with tests, then run local and live acceptance.
Do not initialize Git in this workspace merely to commit this design document.
