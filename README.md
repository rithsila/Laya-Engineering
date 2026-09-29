# Laya + JEV Hybrid Decision System

Fast local typed decisions on Apple Silicon Mac using **Laya-MLX** (System 1) combined with **JEV / TypeSafe AI** (System 2) and **Codex / ChatGPT**.

- For full test commands and expected outputs, see [TESTING.md](TESTING.md).
- For in-depth theory and prompt rules, see [GUIDELINES.md](GUIDELINES.md).

---

## The JEV Formula

> **"An LLM writes. Jev decides. Code acts."**

```
                     Incoming Ticket / Event
                                │
                                ▼
                   ┌─────────────────────────┐
                   │  Local Laya (ANE Chip)  │  ◄── 25 ms, $0 cost
                   └────────────┬────────────┘
                                │
                  Is Confidence High & Safe?
                     │                     │
                    YES                    NO (Confidence < 70% or flagged)
                     │                     │
                     ▼                     ▼
          ┌─────────────────────┐   ┌──────────────────────────┐
          │  Fast Local Python  │   │  JEV Cloud API (System 2)│ ◄── 1.2s
          │  Auto-Action        │   │  Deep Reasoning          │
          └─────────────────────┘   └──────────────────────────┘
```

---

## Quick Start (Choose 1 of 3 Ways)

### Option 1: Local Server in Background (Recommended)
Keeps model warm in Mac Neural Engine memory. Any script, Codex, or curl can call it in 25ms.

```bash
# Start background server
./start_server.sh

# Check status
./status_server.sh

# Test decision (25 ms response)
curl -s -X POST http://127.0.0.1:8080/decide -d '{"ticket":"Database error 500"}'

# Stop when done
./stop_server.sh
```

### Option 2: Interactive Terminal Mode (Best for Testing)
Keep one terminal tab open. Type messages and get instant 25ms answers.

```bash
.venv/bin/python hybrid.py -i
```

### Option 3: Run Once When Needed
Starts up, predicts one ticket, and exits. Takes ~20s total because of model load time.

```bash
.venv/bin/python hybrid.py --ticket "Can I get a refund for last month?"
```

---

## 10-Step Parity Features

- **Rank Wide, Read Narrow (Step 8)**:
  Scores a batch of 6 tickets at 11 ms each ($0.00) on Mac Neural Engine. Only escalates the top 2 items to Cloud/LLM:
  ```bash
  .venv/bin/python rank_wide.py
  ```

- **Run All Automated Tests**:
  ```bash
  .venv/bin/pytest laya-codex-demo/tests/test_basic.py
  ```

---

## Requirements

- **Mac**: Apple Silicon (M1, M2, M3, M4)
- **OS**: macOS 15 or newer
- **Python**: 3.11 to 3.13

---

## Project Structure

```
Laya-engineer-codex/
├── start_server.sh           # Start background server
├── stop_server.sh            # Stop background server
├── status_server.sh          # Check server status
├── TESTING.md                # Complete test suite guide
├── GUIDELINES.md             # In-depth guide & 10 steps
├── README.md                 # Project quickstart
├── rank_wide.py              # Step 8: Rank wide, read narrow demo
├── models/ane/               # Local Apple Neural Engine model files
├── laya-codex-demo/
│   ├── .env                  # TYPESAFE_API_KEY
│   ├── agent.py              # Laya MLX local wrapper
│   ├── jev_client.py         # JEV / TypeSafe Cloud client
│   ├── hybrid.py             # Hybrid router (Laya -> JEV Cloud)
│   ├── server.py             # Fast HTTP server (port 8080)
│   ├── codex_jev_loop.py     # 3-stage Codex loop
│   ├── rank_wide.py          # Priority queue batching
│   └── tests/
│       └── test_basic.py     # 5 unit & integration tests
```
