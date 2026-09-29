# Laya + JEV Hybrid Decision System

Fast local typed decisions on Apple Silicon Mac using **Laya-MLX** (System 1) combined with **JEV / TypeSafe AI** (System 2) and **Codex / ChatGPT**.

For the in-depth architectural guide and prompting rules, see [GUIDELINES.md](GUIDELINES.md).

---

## The JEV Engineering Formula

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

- **Codex / LLM (Writes)**: Generates text, drafts emails, writes code, summarizes.
- **Laya / Jev (Decides)**: Picks choices, scores urgency, checks yes/no flags in **25 ms** with calibrated probabilities ($0 cost).
- **Code (Acts)**: Runs deterministic `if/else` logic without brittle JSON parsing.

---

## Requirements

- **Computer**: Apple Silicon Mac (M1, M2, M3, M4)
- **OS**: macOS 15 or newer
- **Python**: Python 3.11 to 3.13

---

## 1. Quick Setup

```bash
# 1. Create and activate virtual environment
uv venv .venv
source .venv/bin/activate

# 2. Install dependencies
uv pip install -r laya-codex-demo/requirements.txt

# 3. Download the Apple Neural Engine model (download once, runs 100% offline)
python3 -c "from huggingface_hub import snapshot_download; snapshot_download('aac6fef/laya-multilingual-mlx', local_dir='models/mlx')"

# 4. Add your JEV API key
echo "TYPESAFE_API_KEY=your_key_here" > laya-codex-demo/.env
```

---

## 2. Running Modes

### A. Run Cooperation Benchmark (5 realistic scenarios)
```bash
.venv/bin/python test_benchmark.py
```

### B. Interactive Hybrid Mode (Test custom tickets live)
```bash
.venv/bin/python hybrid.py -i
```

### C. Run the Codex + JEV Engineering Loop
```bash
.venv/bin/python codex_jev_loop.py
```

### D. Local Background HTTP Server (~25 ms API)
```bash
.venv/bin/python laya-codex-demo/server.py
# In another terminal:
curl -s -X POST http://127.0.0.1:8080/decide -d '{"ticket":"Database connection timed out"}'
```

---

## 3. Project Structure

```
Laya-engineer-codex/
├── GUIDELINES.md             # In-depth Jev Engineering guide & 7 rules
├── README.md                 # Project quickstart and overview
├── models/mlx/               # Local Apple Neural Engine model files (375 MB)
├── laya-codex-demo/
│   ├── .env                  # JEV / TypeSafe API key
│   ├── agent.py              # Laya MLX local wrapper (Choice, Score, Noul)
│   ├── jev_client.py         # JEV / TypeSafe Cloud API client
│   ├── hybrid.py             # Hybrid router (Laya reflex -> JEV cloud)
│   ├── main.py               # Ticket triage demo with interactive mode
│   ├── codex_jev_loop.py     # 3-stage Codex writes -> Laya decides -> Code acts
│   ├── test_benchmark.py     # 5-scenario performance test
│   └── tests/
│       └── test_basic.py     # Unit and integration test suite
```

---

## 4. References & Research

- [What is Jev Engineering? (Made with Jev)](https://madewithjev.com/what-is-jev-engineering)
- [Jev Engineering 101 (Craft Better Software)](https://craftbettersoftware.com/p/jev-engineering-101)
- [Laya MLX GitHub Repository](https://github.com/mizorewww/laya-mlx)
- [TypeSafe AI Console](https://console.typesafe.ai)
