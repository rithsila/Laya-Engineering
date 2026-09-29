# JEV Engineering Guidelines

How to build fast AI agent systems using **Codex (LLM)** + **Jev / Laya (Decision Engine)** + **Python Code**.

---

## 1. The Core Split: Write, Decide, Act

| Step | Who Does It | Model | Latency | Cost |
|---|---|---|---|---|
| **Writes** | Generates text, code, email drafts, summaries | **Codex / ChatGPT** | ~1.5 - 3.0s | API Tokens |
| **Decides** | Picks choices, scores urgency, checks yes/no flags | **Laya (Local) / Jev** | 25 - 40 ms | $0.00 / Free |
| **Acts** | Runs `if/else`, saves files, sends emails, calls tools | **Python Code** | < 1 ms | Free |

---

## 2. The 7 Golden Rules of Jev Engineering

1. **Send Evidence, Not Summaries**:
   - *Good*: Send the raw ticket, full error trace, or user message.
   - *Bad*: Do not compress or summarize the message first.

2. **Write Questions in Full**:
   - Put all criteria and definitions inside `instructions` and `criteria`.
   - The model only reads instructions, not variable names.

3. **Rebuild Options at Every Step**:
   - Dynamically build the options list based on current state (e.g. current UI buttons or available tools).

4. **Fan-Out Everything in One Call**:
   - Ask Choice, Score, and Noul questions together in a single dictionary.
   - All questions run in parallel with the exact same ~25 ms response time.

5. **Act Only on Confident Answers**:
   - Check the confidence score.
   - If confidence $\ge 70\%$: Execute fast local code.
   - If confidence $< 70\%$ or flagged: Escalate to Codex or JEV Cloud API.

6. **Check Results with Deterministic Code**:
   - Do not trust a text model saying "done".
   - Use Python assertions to check database status, HTTP response, or file creation.

7. **Count Cost per Finished Task**:
   - Measure total task success rate and overall token spend, not individual API calls.

---

## 3. How to Prompt Codex for JEV Engineering

When you ask Codex or ChatGPT to build an AI feature, use this prompt formula:

```text
"I am using Jev Engineering.
1. Use Codex (LLM) only to write complex text or plan steps.
2. Define typed Laya/Jev questions (Choice, Score, Noul) for all decision branches.
3. Use Python if/else to execute actions based on the decision output.
4. If Laya confidence is under 70%, escalate to JEV Cloud."
```

---

## 4. Production Code Template

```python
from agent import decide, choice_question, score_question, noul_question
from jev_client import decide_jev

def run_agent_workflow(ticket: str):
    # Step 1: Define parallel typed questions
    questions = {
        "dept": choice_question(
            "Which department?",
            {"billing": "Billing", "tech": "Technical", "sales": "Sales"}
        ),
        "urgency": score_question("Rate urgency", ["low", "medium", "high"]),
        "escalate": noul_question("Needs manager review?")
    }

    # Step 2: Run fast local reflex (25 ms on Mac Neural Engine)
    res = decide(ticket, questions)

    # Step 3: Check confidence & escalate if needed
    if res["escalate"] or res.answers["dept"]["confidence"] < 0.70:
        # Hard / Unsure: Escalate to JEV Cloud (System 2)
        final = decide_jev(ticket, questions)
        handler = "JEV Cloud API"
    else:
        # Easy / Sure: Keep local result ($0 cost)
        final = res
        handler = "Local Laya"

    # Step 4: Code Acts deterministically
    dept = final["dept"] if isinstance(final, dict) else final["values"]["dept"]
    print(f"[{handler}] Routed to {dept}")
```
