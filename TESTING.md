# Testing Guide for JEV Engineering

Run these tests on your Apple Silicon Mac to verify all 10 steps of JEV Engineering.

---

## Quick Test Cheatsheet

| Test | What It Verifies | Command | Time |
|---|---|---|---|
| **1. Unit & Integration** | Primitives, Schemas, Local ANE, Hybrid logic | `rtk .venv/bin/pytest laya-codex-demo/tests/test_basic.py` | ~21s |
| **2. Codex + JEV Loop** | "LLM writes $\rightarrow$ Jev decides $\rightarrow$ Code acts" | `rtk .venv/bin/python codex_jev_loop.py` | ~22s |
| **3. Rank Wide, Read Narrow** | Scores 6 tickets in 11ms each, escalates top 2 | `rtk .venv/bin/python rank_wide.py` | ~24s |
| **4. Hybrid Benchmark** | 5 realistic tickets: Local ($0, 25ms) vs Cloud | `rtk .venv/bin/python test_benchmark.py` | ~25s |
| **5. Background Server** | Fast HTTP API for Codex & external apps | `rtk ./start_server.sh` | ~15s |

---

## Test 1: Unit & Integration Suite

Verifies question helpers, response parsing, local ANE inference, hybrid escalation, and rank-wide priority sorting.

```bash
rtk .venv/bin/pytest laya-codex-demo/tests/test_basic.py
```

**Expected Result:**
```text
===== 5 passed in 21.63s =====
```

---

## Test 2: Full Codex + JEV 3-Step Loop

Demonstrates the core JEV formula:
1. **LLM writes**: Codex drafts an email or code change.
2. **Jev decides**: Local Laya evaluates safety, sentiment, and action flags in parallel.
3. **Code acts**: Deterministic Python sends or blocks without hallucination.

```bash
rtk .venv/bin/python codex_jev_loop.py
```

**Expected Result:**
- Output shows: Stage 1 Draft $\rightarrow$ Stage 2 Laya decision (25 ms) $\rightarrow$ Stage 3 Code execution.

---

## Test 3: Rank Wide, Read Narrow (Step 8)

Demonstrates batching 6 tickets:
- Local Laya scores all 6 tickets on Apple Neural Engine at **11 ms per ticket ($0.00)**.
- Only the 2 critical tickets consume expensive Cloud/LLM tokens.
- Routine tickets are auto-queued by Python.

```bash
rtk .venv/bin/python rank_wide.py
```

**Expected Result:**
```text
[TCK-103] Urgency: 1.182 | Escalate: True  | 11.6ms | EMERGENCY: Production payment gateway down...
Tokens saved: 66% (4 of 6 tickets never touched an expensive LLM).
```

---

## Test 4: Hybrid Benchmark (5 Scenarios)

Compares local Apple Neural Engine against JEV Cloud escalation across 5 realistic support tickets.

```bash
rtk .venv/bin/python test_benchmark.py
```

**Expected Result:**
- Routine tickets: Handled by **Local Neural Engine** (~25 ms, $0.00).
- Complex / Critical tickets: Handled by **JEV Cloud API** (~1.2s).

---

## Test 5: Background HTTP Server

Keeps the model loaded in Apple Silicon memory for instant 25 ms HTTP calls.

```bash
# 1. Start server
rtk ./start_server.sh

# 2. Check status
rtk ./status_server.sh

# 3. Test request (instant 25-35 ms response)
rtk curl -s -X POST http://127.0.0.1:8080/decide -d '{"ticket":"Payment failed with error 402"}'

# 4. Stop server when done
rtk ./stop_server.sh
```
