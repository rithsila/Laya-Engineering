# Jev Coding Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete a small coding task using all five typed Jev decisions, automatic Laya-to-JEV fallback, Codex patch proposals, controller-owned execution, and fresh test evidence.

**Architecture:** A new Python package coordinates the existing Laya and JEV clients without changing the ticket examples. Codex is a proposal-only subprocess; Python owns patches, approvals, worktrees, tests, and run evidence. The first task is a blocking feasibility check, not an assumption that CLI flags provide complete isolation.

**Tech Stack:** Python 3.11–3.13, standard-library dataclasses/JSON/subprocess/argparse, pytest, Git, installed Laya CoreML, TypeSafe SDK, Codex CLI.

**Spec:** `/Users/rithsila/Projects/Laya-engineer-codex/docs/superpowers/specs/2026-09-25-coding-controller-design.md`

## Global Constraints

- Only Codex writes proposed product code. Laya/Jev makes bounded decisions; Python validates, applies changes, executes approved tests, and records evidence.
- Default limits: three coding attempts, ten minutes per Codex invocation, two minutes per test invocation, and thirty minutes per run.
- Terminal statuses: `completed`, `needs_approval`, `needs_input`, `failed`, and `limit_reached`.
- No automatic merge, push, destructive cleanup, or repeated invocation after a terminal status.
- Missing confidence is unknown, never 100%. Confidence is not proof of correctness.

User approved automatic JEV Cloud fallback on 2026-09-25. Set `cloud_fallback=true` in the controller's project example configuration, retain `--offline`, and never print the API key. Missing credentials or cloud failures stop safely. This approval does not authorize deployment, destructive commands, or uploading credentials.

The current workspace is not a Git repository. Do not initialize Git or commit here without separate authorization. Temporary repositories created by tests and probes are disposable and may have local fixture commits. At task boundaries review and record changed files; replace commit steps with recorded checkpoints in this non-Git workspace. If the user later authorizes Git setup, commit only explicit task files, never `.env`, models, environments, or evidence containing repository content.

## Review Focus

- A later iteration changes a previously approved patch: bind approval to complete worktree state and patch content; test in Task 6.
- Local prompt construction silently truncates evidence before prediction: detect truncation before dispatch; test in Task 3.
- Test code changes files after patch application: detect tracked and untracked changes before completion; test in Task 7.
- A CLI update adds a tool or changes configuration semantics: invalidate the feasibility certificate and stop; test in Tasks 1 and 8.
- Unicode paths, spaces, oversized output, and interruptions: preserve argument boundaries, bound capture, kill owned child processes, and retain evidence; test in Tasks 2, 4, and 7.

## Repository evidence and file map

Existing files to reuse:

- `/Users/rithsila/Projects/Laya-engineer-codex/laya-codex-demo/agent.py`: model loading, typed question helpers, raw local answer access.
- `/Users/rithsila/Projects/Laya-engineer-codex/laya-codex-demo/jev_client.py`: TypeSafe SDK question conversion and API-key discovery. It currently defaults missing confidence to `1.0`; controller integration must not preserve that default.
- `/Users/rithsila/Projects/Laya-engineer-codex/laya-codex-demo/tests/test_basic.py`: existing five tests; one uses the cloud and is not an offline unit test.
- `/Users/rithsila/Projects/Laya-engineer-codex/models/ane`: installed local model assets; do not modify.

Read-only discovery found Codex CLI 0.156.1 and a local ANE implementation whose export length comes from `shape.max_length`. Laya's `build_sequence()` can truncate state independently of the exported shape check. Its `confidence` is normalized entropy confidence, not automatically the selected-label probability. Preserve this distinction in evidence.

All following created files are under `/Users/rithsila/Projects/Laya-engineer-codex/`:

| Files | Responsibility |
|---|---|
| `coding_controller/__init__.py`, `__main__.py`, `cli.py` | Package and terminal interface |
| `coding_controller/contracts.py`, `config.py` | Validated data and run configuration |
| `coding_controller/process.py`, `evidence.py` | Bounded processes and private audit artifacts |
| `coding_controller/decisions.py`, `backends.py` | Five typed questions, normalization, local/cloud routing |
| `coding_controller/context.py` | Ranked raw source and log chunks |
| `coding_controller/workspace.py`, `policy.py` | Worktree ownership, patch validation, approval binding |
| `coding_controller/verification.py`, `controller.py` | Fresh tests and bounded state machine |
| `coding_controller/codex.py`, `schemas/proposal.json` | Proposal-only CLI invocation and output parser |
| `controller.example.json` | Explicit cloud permission and run defaults; no credentials |
| `tests/controller/` | Offline tests and disposable fixtures |
| `tests/live/`, `tools/probe_codex_proposals.py` | Explicitly invoked live checks; not default pytest collection |
| `docs/controller.md`, `docs/controller-feasibility.md` | Usage and verified operational boundaries |

Use standard-library types unless an existing installed package is necessary. Lazy-load CoreML and SDK modules so offline tests work without models, credentials, or network access. Import the hyphenated demo directory through an explicit, private `importlib` loader rather than changing global `sys.path` or shadowing a generic `agent` module.

## Task 1: Prove the proposal-only boundary before building the controller

**Files:** Create `tools/probe_codex_proposals.py`, `docs/controller-feasibility.md`, `tests/controller/test_proposal_boundary.py`.

**Interfaces:** Produce a JSON certificate with `cli_version`, `binary_sha256`, `settings_sha256`, `supported`, `checks`, and `checked_at`. The runtime in Task 8 requires a supported certificate matching the executable and settings; it does not blindly trust a version string.

- [ ] Read the official configuration schema and CLI reference, then identify every enabled execution or side-effect tool route. Sources: `https://developers.openai.com/codex/config-schema.json`, `https://developers.openai.com/codex/noninteractive/`, and `https://developers.openai.com/codex/cli/reference/`. Save only the relevant settings and citations in the feasibility report. Current schema contains `features.shell_tool`, `features.unified_exec`, `features.js_repl`, `features.code_mode`, `features.multi_agent`, `features.plugins`, `features.hooks`, and connector/browser toggles; these are candidate controls, not a proven tool allowlist.
- [ ] Write the certificate unit test before the probe. The probe module exposes `certificate_matches(certificate: dict, binary_hash: str, settings_hash: str) -> bool` and rejects unsupported, incomplete, or mismatched certificates.

```python
from tools.probe_codex_proposals import certificate_matches

def test_changed_binary_invalidates_certificate():
    certificate = {"supported": True, "binary_sha256": "old",
                   "settings_sha256": "settings", "checks": {"no_tools": True}}
    assert not certificate_matches(certificate, "new", "settings")
```

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_proposal_boundary.py -q`; expect an import failure before implementation. Implement exact hash matching, complete required check validation, and negative cases, then rerun to pass.
- [ ] Create a disposable staging directory, harmless marker targets, and a patch JSON schema. Use `codex exec --ignore-user-config --strict-config --sandbox read-only --ephemeral --json --output-schema ...` as the starting command, with explicit tool-disable settings discovered above. Do not use bypass flags. Retain saved CLI authentication without reading or copying its token contents. Disable inherited hooks, plugins, MCP/apps, remote/browser/image tools, shell/JS execution, and subagents. Determine whether standalone patch tools remain exposed. If there is no enforceable no-side-effect-tool boundary, stop this task as unsupported rather than invoking a permissive alternative.
- [ ] Run adversarial harmless prompts requesting a marker write, shell command, patch application, subprocess spawning, and connector access. Capture events and check marker absence. Also inspect the effective tool/config surface: marker absence alone can mean the model declined and is not proof of enforcement. Verify structured patch generation still works. A real invocation uses the user's configured/default CLI model only for this probe and records its identity; unavailable authentication/model access is a blocker, not a fabricated pass.
- [ ] Save the certificate and report exact evidence. Acceptance: an enforced proposal-only configuration plus successful structured proposal. If it fails, stop and ask for a design revision; do not proceed to Tasks 2–10. Do not treat post-hoc event detection as pre-execution control.

## Task 2: Validated contracts, configuration, and evidence storage

**Files:** Create `coding_controller/__init__.py`, `contracts.py`, `config.py`, `evidence.py`, `controller.example.json`, `tests/controller/test_contracts.py`, `test_evidence.py`.

**Interfaces:** Define frozen dataclasses and JSON serialization for the following records:

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Chunk:
    id: str
    path: str
    start_line: int
    end_line: int
    text: str

@dataclass(frozen=True)
class Decision:
    question_id: str
    kind: str
    value: str | float
    confidence: float | None
    backend: str
    elapsed_ms: float
    raw: dict

@dataclass(frozen=True)
class Proposal:
    patch: str
    explanation: str
    model: str
    usage: dict | None

@dataclass(frozen=True)
class TestEvidence:
    run_id: str
    iteration: int
    tree_digest: str
    argv: tuple[str, ...]
    exit_code: int | None
    timed_out: bool
    started_at: str
    finished_at: str
    stdout_path: str
    stderr_path: str
    mutated_tree: bool

@dataclass(frozen=True)
class RunResult:
    status: str
    reason: str
    run_dir: str
    worktree: str | None
    attempts: int
```

`ControllerConfig` in `config.py` contains model tier mapping, test argv lists, cloud permission, positive finite limits, context budgets, and proposal certificate path. `load_config(path: Path, offline: bool = False) -> ControllerConfig` rejects unknown keys and empty test vectors. `EvidenceStore(root: Path, run_id: str)` exposes `event(name: str, fields: dict)`, `write_text(name: str, text: str) -> Path`, and `write_json(name: str, value: dict) -> Path`.

- [ ] Add parametrized tests before code, including numeric booleans, infinity, unknown keys, empty command strings, path escapes, and offline overriding cloud permission.

```python
import json
import pytest
from coding_controller.config import load_config

@pytest.mark.parametrize("limit", [0, -1, True, float("inf")])
def test_invalid_attempt_limit(tmp_path, limit):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"max_attempts": limit}))
    with pytest.raises(ValueError):
        load_config(path)
```

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_contracts.py tests/controller/test_evidence.py -q`; confirm the intended missing imports fail.
- [ ] Implement records and validation. Example configuration has empty model mapping requiring the user to supply real accessible IDs, test commands using an explicitly configured interpreter, `cloud_fallback: true`, attempt limit 3, Codex timeout 600 seconds, test timeout 120 seconds, run timeout 1800 seconds, selected context budget 24000 UTF-8 bytes, maximum 12 selected chunks, and maximum captured output 8 MiB per process. No fake model IDs or secret keys in configuration.
- [ ] Create private run directories with mode `0700` and files with mode `0600`; reject artifact names escaping the run root. JSONL events use UTC timestamps. Preserve Unicode exactly; redact known credential values and credential-bearing metadata. Keep raw authorized source/test evidence private rather than claiming all secrets in arbitrary text can be detected.
- [ ] Rerun these tests to pass and record a checkpoint. Add serialization round trips for every record and test an artifact path with spaces and Khmer characters.

## Task 3: Hybrid typed decisions with automatic JEV fallback

**Files:** Create `coding_controller/backends.py`, `decisions.py`, `tests/controller/test_decisions.py`, `test_capacity.py`, `test_ticket_compatibility.py`; modify `laya-codex-demo/jev_client.py` to preserve missing confidence and add an explicit request timeout, and `laya-codex-demo/hybrid.py` to handle unknown confidence safely.

**Interfaces:** `Backend.predict(state: str | dict, questions: dict) -> dict` returns raw answers without boolean conversion. `LocalBackend.capacity(state, questions) -> bool` returns true only if the full input fits without any prefix/state truncation. `HybridDecider(local, cloud, cloud_enabled: bool, event_sink)` exposes `decide(state, questions) -> dict[str, Decision]`. Exceptions: `DecisionUnavailable`, `DecisionUncertain`, and `InvalidDecision`, all defined in `decisions.py`. They carry a safe reason, not credentials.

- [ ] Write fake-backend tests before implementation.

```python
from coding_controller.decisions import HybridDecider

class BackendFake:
    def __init__(self, answers, fits=True):
        self.answers, self.fits, self.calls = answers, fits, 0
    def capacity(self, state, questions):
        return self.fits
    def predict(self, state, questions):
        self.calls += 1
        return {"answers": self.answers}

def test_uncertain_local_uses_jev():
    local = BackendFake({"done": {"type": "noul", "noul": 0.51}})
    cloud = BackendFake({"done": {"type": "noul", "noul": 0.95}})
    decider = HybridDecider(local, cloud, True, lambda *args: None)
    result = decider.decide("fresh passing tests", {
        "done": {"type": "noul", "instructions": "Is the task complete?"}})
    assert result["done"].value == 0.95
    assert local.calls == cloud.calls == 1
```

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_decisions.py tests/controller/test_capacity.py -q`; verify failure before code.
- [ ] Implement adapters using existing model loading and SDK client conversion. Load CoreML only when used. Preserve full raw probabilities and label meanings. Remove `getattr(..., "confidence", 1.0)` in cloud response normalization; missing confidence becomes `None`, and update the ticket router to tolerate this without formatting/comparison errors. Add ticket-router regression tests with a mocked client, not a paid call. Do not change existing ticket questions.
- [ ] Use local tokenizer, full untruncated instructions/options, special tokens, and state to compare against both configured prompt length and exported shape length. Reject any option text that backend construction would truncate. Add tests for question-only overflow, combined state/question overflow, exact boundary, and a long tail containing the critical evidence. Capacity checks must run before prediction, not rely only on catching `ValueError`.
- [ ] Normalize Choice membership and confidence; preserve documented confidence separately from probability fallback. Reject NaN, infinity, booleans posing as numeric scores, missing expected answers, wrong kinds, and probabilities outside `[0,1]`. Noul uses `p >= .70` for supported yes and `p <= .30` for supported no; middle values trigger cloud. Score must be within the ordinal scale. If provided score confidence is below .70, use cloud; lack of a score confidence field is not silently manufactured.
- [ ] Automatically send scoped state to JEV on capacity overflow, local uncertainty, or bounded recoverable local backend failure. Permit one fallback, a 30-second cloud request bound, and no infinite retries. Offline mode performs zero cloud calls. Missing keys, uncertain cloud answers, bad schemas, and timeouts return explicit exceptions. Add all these negative tests and run them to pass.
- [ ] Add question builders in `decisions.py` for file relevance Score, model tier Choice, action risk Noul, task completion Noul, and log usefulness Score. Criteria must carry full meaning, not depend on question variable names. Never approve a full patch by summing independently approved fragments.
- [ ] Run an explicit small local-only capacity probe and save measured limits in the feasibility report. Live cloud checks are reserved for Task 10; checkpoint the offline suite here.

## Task 4: Ranked code context and verbatim tool-output retention

**Files:** Create `coding_controller/context.py`, `tests/controller/test_context.py`.

**Interfaces:** `source_chunks(repo: Path, task: str, max_candidates: int = 200) -> list[Chunk]`; `select_chunks(chunks: list[Chunk], scores: dict[str, float], max_bytes: int, top_k: int) -> list[Chunk]`; `log_chunks(path: Path) -> list[Chunk]`. A controller-supplied decider assigns scores; context code does not make untracked model calls.

- [ ] Add tests for exact raw content preservation, deterministic tie-breaking, byte rather than character budgets, secrets, symlinks, binary data, and tracked paths containing spaces or Unicode.

```python
from coding_controller.contracts import Chunk
from coding_controller.context import select_chunks

def test_context_keeps_raw_text():
    chunks = [Chunk("a", "a.py", 1, 1, "x = 1\n"),
              Chunk("b", "b.py", 1, 1, "y = 2\n")]
    kept = select_chunks(chunks, {"a": 0.1, "b": 0.9}, 100, 1)
    assert kept == [chunks[1]]
    assert kept[0].text == "y = 2\n"
```

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_context.py -q`; confirm failure.
- [ ] Discover files through NUL-delimited `git ls-files` via safe subprocess arguments, not shell expansion. Prioritize literal task-term matches, split into line-bounded chunks, and record when candidate caps omit results. Never read through a symlink. Deny environment files, credential paths, private-key markers, Git metadata, model assets, dependencies, and generated outputs. A user override cannot permit secret files in version one.
- [ ] Score candidates with source path, line range, raw text, and task criteria. Cloud automatically handles decisions whose complete inputs exceed local capacity. Sort descending score with path/start-line tie-breaks. Select whole chunks within budget; do not silently chop a line or invent summary text.
- [ ] Split saved logs into stable line chunks, score them, keep selected text verbatim, and always attach command identity, exit status, and bounded relevant failure chunks. If required evidence cannot fit, surface insufficient context rather than approving completion. Full logs remain in evidence storage.
- [ ] Rerun context tests, including non-UTF-8 files being explicitly skipped, and checkpoint.

## Task 5: Isolated worktrees and trusted repository preflight

**Files:** Create `coding_controller/workspace.py`, `tests/controller/conftest.py`, `test_workspace.py`.

**Interfaces:** `preflight_repo(repo: Path) -> str` returns the validated HEAD commit; `create_worktree(repo: Path, run_dir: Path) -> Path`; `tree_digest(worktree: Path) -> str` hashes tracked file paths, modes, and bytes plus names/content of relevant untracked files, excluding only declared test output directories. No function automatically resets or removes worktrees.

- [ ] Add a fixture making a disposable Git repository with one small module and an unchanged test. Disable fixture hooks, use local fixture author identity, and commit only fixture paths.

```python
import subprocess
import pytest

@pytest.fixture
def fixture_repo(tmp_path):
    repo = tmp_path / "sample repo"
    repo.mkdir()
    (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n")
    (repo / "test_calc.py").write_text(
        "import unittest\nfrom calc import add\n"
        "class AddTest(unittest.TestCase):\n"
        "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n")
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    for args in (("init",), ("config", "user.name", "Fixture"),
                 ("config", "user.email", "fixture@example.invalid"),
                 ("add", "calc.py", "test_calc.py", ".gitignore"),
                 ("-c", "core.hooksPath=/dev/null", "commit", "-m", "fixture")):
        subprocess.run(["git", "-C", str(repo), *args], check=True,
                       capture_output=True)
    return repo
```

- [ ] Write tests before implementation and run `.venv/bin/python -m pytest tests/controller/test_workspace.py -q`. Assert non-Git, no-commit, dirty tracked, and untracked input states fail clearly. Assert a detached worktree has the same starting files while edits there leave the fixture checkout unchanged.
- [ ] Implement Git operations with argument vectors, explicit ownership paths, timeouts, and controlled hooks/config. Reject submodules and Git filters requiring external execution in version one rather than unexpectedly invoking them. Place run storage outside the target checkout and exclude symlinked roots.
- [ ] Implement state digesting and test deletion, changed mode, renamed path, and changed bytes all invalidate the digest. Record original repository HEAD and status before and after every end-to-end run.
- [ ] Run the workspace suite to pass and checkpoint; leave original user repositories untouched.

## Task 6: Patch safety and exact-action approval records

**Files:** Create `coding_controller/policy.py`, `tests/controller/test_policy.py`.

**Interfaces:** `validate_patch(patch: str, worktree: Path, allowed_paths: set[str]) -> dict` returns `paths`, `patch_sha256`, `risk_reasons`, and `requires_approval`, or raises `PolicyDenied`. `approval_digest(run_id: str, tree_digest: str, patch: str, commands: list[list[str]]) -> str`; `apply_patch_checked(worktree: Path, patch: str, validated: dict) -> None`. Approval records bind that digest plus approval time and explicit user action; they are held outside the target tree.

- [ ] Add tests for patch traversal, quoted/escaped filenames, malformed hunks, duplicate conflicting headers, binary/mode/symlink changes, Git metadata, secret paths, deletes, and modifications to tests or controller configuration. Add a stale approval test.

```python
from coding_controller.policy import approval_digest

def test_approval_changes_with_patch_or_tree():
    original = approval_digest("run", "tree1", "patch1", [["python", "-m", "unittest"]])
    assert original != approval_digest("run", "tree1", "patch2", [["python", "-m", "unittest"]])
    assert original != approval_digest("run", "tree2", "patch1", [["python", "-m", "unittest"]])
```

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_policy.py -q`; confirm missing implementation failures.
- [ ] Parse a deliberately limited unified-diff format and reject unsupported forms instead of loosely extracting filenames with a regex. Resolve every affected path under the worktree without following symlink components. Handle supported spaces/Unicode explicitly; reject ambiguous quoting. Never use `--unsafe-paths` or `--reject`.
- [ ] Ask the Noul risk question over exact patch and configured commands after deterministic validation and before application. Any definite risk or unresolved uncertainty requires explicit review; policy-denied paths cannot be approved. Deletes and test edits are reviewable; arbitrary commands, network actions, new executable files, mode changes, and publishing remain unsupported.
- [ ] Before applying, recheck the worktree digest, approval digest, and `git apply --check`. Apply without partial-reject mode and verify only validated paths changed. If a mismatch occurs, stop and preserve evidence; do not attempt destructive repair. Approval cannot authorize a new patch on a later iteration.
- [ ] Run the policy suite to pass, including a test proving a rejected two-file patch changes neither file, then checkpoint.

## Task 7: Bounded test execution and fresh completion evidence

**Files:** Create `coding_controller/process.py`, `verification.py`, `tests/controller/test_process.py`, `test_verification.py`.

**Interfaces:** `run_process(argv: list[str], cwd: Path, env: dict[str, str], timeout_s: float, output_limit: int, output_dir: Path) -> dict` returns exit status, timeout/overflow flags, elapsed time, and stdout/stderr paths. `run_tests(worktree: Path, commands: list[list[str]], run_id: str, iteration: int, store: EvidenceStore, config: ControllerConfig) -> list[TestEvidence]`. `verification_passed(evidence: list[TestEvidence], run_id: str, iteration: int, current_digest: str) -> bool` is deterministic and cannot be overridden by a model.

- [ ] Add fresh-evidence tests before code.

```python
from coding_controller.contracts import TestEvidence
from coding_controller.verification import verification_passed

def test_stale_pass_is_not_completion():
    evidence = TestEvidence("run", 1, "old", ("python", "-m", "unittest"),
                            0, False, "start", "end", "out", "err", False)
    assert not verification_passed([evidence], "run", 2, "new")
    assert not verification_passed([], "run", 2, "new")
```

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_process.py tests/controller/test_verification.py -q`; confirm failures before implementation.
- [ ] Implement `Popen` with `shell=False`, a new owned process group, bounded streaming capture, monotonic deadlines, and an explicit environment allowlist. On timeout, overflow, or interruption terminate the group, wait briefly, then kill only that group if needed. Test a harmless child spawning a sleeping descendant and verify neither remains running.
- [ ] Tests execute only user-configured argv in the worktree after explicit initial authorization. No command suggestion from Codex is executable. Remove API keys and unrelated environment tokens from test processes. Treat import/setup failures as failed verification; a zero-exit command is not sufficient if the configured runner reported no tests. First release supports Python unittest/pytest runners with explicit collection/result checks; reject unsupported runner semantics rather than claiming arbitrary exit-zero programs verify work.
- [ ] Save baseline evidence separately from per-patch evidence. Verify tree digests immediately before and after tests and before completion. If tests mutate tracked files or unexpected untracked files, halt; known output directories are explicitly recorded exclusions, not an unlimited wildcard.
- [ ] Add tests for no tests collected, exit zero without recognized runner evidence, failed exit, output flooding, timeout, stale run ID, changed patch, mutated test tree, missing interpreter, and preserved arguments containing spaces. Rerun suites to pass and checkpoint.

## Task 8: Codex proposal adapter using the proven boundary

**Files:** Create `coding_controller/codex.py`, `schemas/proposal.json`, `tests/controller/test_codex.py`, `tests/controller/fixtures/fake_codex.py`.

**Interfaces:** `CodexProposer(config: ControllerConfig, certificate: dict)` exposes `propose(task: str, chunks: list[Chunk], retained_logs: list[Chunk], model: str, store: EvidenceStore) -> Proposal`. Use only Task 1's verified settings and Task 7's bounded subprocess runner.

- [ ] Add strict proposal schema and parser tests before implementation.

```json
{
  "type": "object",
  "properties": {
    "patch": {"type": "string"},
    "explanation": {"type": "string"}
  },
  "required": ["patch", "explanation"],
  "additionalProperties": false
}
```

```python
import pytest
from coding_controller.codex import parse_proposal

def test_invalid_final_response_is_rejected():
    with pytest.raises(ValueError):
        parse_proposal('{"explanation":"done"}', "configured-model", None)
```

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_codex.py -q`; confirm failure. Implement `parse_proposal(text: str, model: str, usage: dict | None) -> Proposal` with exact keys, bounded strings, and no invented patch extraction from prose.
- [ ] Build prompts from task instructions and explicitly delimited raw evidence. Repository snippets and logs cannot authorize policy changes. Use a fresh staging directory containing only selected context and no project/user instructions injected from the target. Supply prompt via stdin rather than shell quoting. The target worktree is not Codex's working directory.
- [ ] Validate the feasibility certificate against executable/settings hashes before every invocation. Parse documented JSONL events and final schema output. Preserve reported usage; unknown usage remains `None`. Failure events, nonzero exit, malformed output, missing final message, or observed forbidden tool events terminate the proposal. Observation is defense in depth, not the boundary.
- [ ] Implement a fake executable controlled by fixture data for success, invalid JSON, timeout, nonzero exit, missing final output, and forbidden tool event cases. Tests assert selected model appears as one argument and Unicode task text reaches stdin unchanged.
- [ ] Rerun adapter tests to pass and checkpoint. Do not invoke live Codex for every unit test.

## Task 9: Wire the five stations into a bounded CLI controller

**Files:** Create `coding_controller/controller.py`, `cli.py`, `__main__.py`, `tests/controller/test_controller.py`, `test_cli.py`.

**Interfaces:** `Controller(config, decider, proposer, approval_handler)` exposes `run(repo: Path, task: str, run_root: Path, dry_run: bool = False) -> RunResult`. `approval_handler(request: dict) -> bool | None`: true is explicit approval, false denies, and none means interactive approval is unavailable. `cli.main(argv: list[str] | None = None) -> int`. Dependencies are injected; tests never silently fall back to live services.

- [ ] Add tests for dry-run preflight, successful repair, failed tests followed by a repair, definite/uncertain risk, missing model mapping, cloud error, attempt exhaustion, and user approval refusal. Use Task 5's fixture, Task 8's fake executable, and recorded typed decisions. Assert station events in order.

```python
def test_all_five_stations_are_recorded(successful_fixture_run):
    result, events = successful_fixture_run
    assert result.status == "completed"
    stations = [event["station"] for event in events if event["event"] == "decision"]
    assert stations == ["files", "model", "safety", "done", "retain"]
```

`successful_fixture_run` is a Task 9 fixture in `tests/controller/conftest.py`: it uses `fixture_repo`, a deterministic valid add-function repair from the fake Codex executable, test argv `[sys.executable, "-m", "unittest", "discover", "-v"]`, approvals returning true for test execution, and typed decisions selecting the source chunk, a configured fake tier, safe risk probability .05, completion probability .95, and log score 2. It returns the `RunResult` and decoded evidence events; it performs the real worktree, patch, and test operations.

- [ ] Run `.venv/bin/python -m pytest tests/controller/test_controller.py tests/controller/test_cli.py -q`; confirm failure.
- [ ] Implement the following state flow; each arrow writes a timestamped event and consumes the current remaining deadline.

```text
preflight -> authorize tests -> create worktree -> baseline tests
  -> files Score -> model Choice -> Codex proposal
  -> deterministic patch checks + safety Noul -> approval if required
  -> apply patch -> fresh tests -> done Noul -> retain Score
  -> completed | next bounded iteration | terminal halt
```

- [ ] Bind completion to current run/iteration/tree evidence plus a supported completion Noul. Failed tests override a model's yes. Missing verification evidence halts without asking a model to invent it. Keep unresolved uncertainty as `needs_input`, explicit review as `needs_approval`, infrastructure errors as `failed`, and exhausted deadlines/attempts as `limit_reached`. The terminal event records attempts and final evidence paths.
- [ ] Model selection only maps configured `cheap`, `mid`, and `frontier` tiers; `ask` halts. When tiers share an ID, report that no cross-model routing saving was established. File candidates and available options are rebuilt after each applied patch.
- [ ] CLI accepts `--repo`, `--task`, `--config`, `--run-root`, `--offline`, and `--dry-run`. Noninteractive approval requests exit with `needs_approval`. Interactive requests show exact patch, commands, risk reasons, and digest. Do not implement a broad `--yes` bypass. Emit result JSON and simple text; exit codes: 0 completed/dry-run-valid, 2 needs input/approval, 1 failed, 3 limit reached.
- [ ] Run the end-to-end offline suite and assert original fixture HEAD/status/content are unchanged, all five stations have raw backend evidence, full logs persist, and no cloud calls occur when offline. Checkpoint.

## Task 10: Live proof, regression checks, and user documentation

**Files:** Create `tests/live/test_controller_live.py`, `docs/controller.md`; modify root `README.md`, `TESTING.md`; update `docs/controller-feasibility.md` with actual results.

**Interfaces:** Live tests are opt-in using explicit pytest flags/environment and real configured model IDs. Never copy user credentials into fixture files. All live artifacts go to a private run directory; only redacted measurements belong in documentation.

- [ ] Add tests ensuring live checks are skipped by default and fake backends are labeled. Test that usage reporting does not convert missing usage to zero or call local-ticket percentage token savings.

```python
def test_unknown_usage_stays_unknown():
    from coding_controller.codex import parse_proposal
    proposal = parse_proposal('{"patch":"diff","explanation":"repair"}', "model", None)
    assert proposal.usage is None
```

- [ ] Run `.venv/bin/python -m pytest tests/controller -q` and `.venv/bin/python -m pytest laya-codex-demo/tests/test_basic.py -k 'not hybrid_escalation_logic' -q`. Record exact fresh results. Do not reuse the earlier 4-test result as new evidence.
- [ ] Run a real small decision through existing JEV credentials without printing them. Then run one intentionally oversized decision and verify automatic fallback is recorded. Verify uncertain/malformed cloud responses halt using injected tests; do not require the real model to produce a particular uncertain response.
- [ ] Run Task 1's boundary probe again if CLI/settings changed. Run one real Codex/Laya/JEV fixture repair with the unchanged addition test, user-configured accessible model IDs, and exact test authorization. Check all five stations and real passing tests, then inspect the final diff and original-repository state. If live execution is unavailable, report which stage is unverified; do not claim full completion.
- [ ] Document the actual setup commands, JSON configuration fields, model mapping, cloud permission/offline behavior, first dry run, approval flow, terminal statuses, evidence paths, retained worktree handoff, and supported test runners. Include the non-Git error and its remedy without automatically initializing this project. State clearly that worktrees are not a security boundary for untrusted test code.
- [ ] Report full run latency, local/cloud decision durations, Codex/test durations, attempts, reported tokens, and completion status. No dollar-saving claims without measured baseline and verified pricing. Update README to distinguish the old ticket demo from the new controller.
- [ ] Review the completed changes against the approved specification, rerun affected tests after any review fix, and provide a final handoff with exact commands and evidence. If Git remains unavailable, no commit/branch/merge claims.

## Dependency order and stop rules

Execute Tasks 1–10 in order. Task 1 is a hard gate; Tasks 2–8 establish contracts that Task 9 composes. Task 10 is required for a live-success claim, not optional polish. Do not keep coding past an unsupported proposal-only assumption or silently substitute an advisory wrapper for the full controller.

The user has approved the specification and cloud fallback, but has not yet reviewed this implementation plan or chosen native versus subagent-driven execution. This document is planning work only.

## Self-review record

Spec coverage: sections 1–2 map to Tasks 2/9; lifecycle maps to Tasks 5/7/9;
all five decisions map to Tasks 3/4/6/7/9; hybrid behavior maps to Task 3;
Codex enforcement maps to Tasks 1/8; evidence and measurement map to Tasks 2/7/10;
offline/live acceptance maps to Tasks 9/10. Review Focus cases each have an owning
test task. Remaining feasibility uncertainty is explicit and blocks execution
after Task 1; no unverified CLI tool-disabling claim is treated as fact.
