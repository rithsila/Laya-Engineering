# Jev Engineering for Coding Agents

**Subtitle:** Five Typed Decisions Around Every Loop, and What They Take Off the Frontier Model  
**Author:** zodchi · @zodchiii · t.me/zodchixquant  
**Date:** September 2026  
**Note:** 2026 Working Note on Jev Engineering Practice. Independent working note, not affiliated with TypeSafe.

---

## 1. The Coding Loop Diagram

```
                 [Task: brief + repo]
                          |
                          v
               < Which files? (SCORE) >
                          |
                          v
              [ Read top chunks only ]
                          |
                          v
               < Which model? (CHOICE) >
                          |
                          v
               [ WRITE CODE - LLM ]
                          |
                          v
               < Safe to run? (NOUL) > ---> [ Irreversible? Ask You Approve ]
                          |
                          v
               [ Run in a worktree ]
                          |
                          v
              [ Tests: fresh evidence ]
                          |
                          v
                   < Done? (NOUL) > -------> [ Halt: Ask You ]
                          |
                          v
             < Keep or drop? (SCORE) >
                          |
                          +---> (Loops back to next step)
```

> **Figure 1 Note:** Only one station writes code. Five other stations are small choices:
> 1. Which files to read?
> 2. Which model to use?
> 3. Safe to run?
> 4. Is the job done?
> 5. Keep or drop tool output?
>
> Diamonds are typed calls. Two can exit to ask a human.

---

## 2. Main Content

### I. Most Turns Contain a Decision

Coding agents spend most turns making simple choices, not writing code:
- Which grep results to read.
- Whether a test failed because the code is wrong or the test is old.
- If a bash command is safe to run.
- If the task is finished.

Big frontier models usually answer these questions inside huge 120k token contexts. That is very slow and expensive for a choice with only 2 to 4 options.

#### Example Decision API Call

```python
r = client.system_one(state=step, questions={
    "tier": Choice(
        instructions="Which model should do this step?",
        criteria={
            "cheap": "Mechanical edit, local, low risk.",
            "mid": "Bounded change across a few files.",
            "frontier": "Design change or unknown code.",
            "ask": "Brief unclear; a person decides.",
        },
    ),
    "destructive": Noul(
        instructions="Does this delete or overwrite data?",
    )
})
```

---

### II. Five Questions on the Loop

1. **Which files? (Score):** Ranks search results so the model reads only top parts instead of 40 grep lines.
2. **Which model? (Choice):** Sends simple edits to cheap models, and hard design changes to frontier models.
3. **Safe to run? (Noul):** Checks security risks (delete files, use network, rewrite git). Stops for human approval if irreversible.
4. **Done? (Noul):** Checks real test results instead of trusting agent self-reports.
5. **Keep or drop? (Score):** Scores tool output so only useful logs stay verbatim in context without lossy summaries.

---

### III. What Asking the Frontier Costs

Frontier models re-read the full 120,000 token context for every small question. Small models and Jev only read a small scoped state.

#### Table 1: Cost Comparison (September 2026 Rates)

| Asked of | Each Decision | Per Session | Per Month |
| :--- | :--- | :--- | :--- |
| **Frontier (cached)** | $0.130 | $1.95 | $1,716 |
| **Frontier (cold prefix)** | $1.210 | $18.15 | $15,972 |
| **Cheap LLM** | $0.0017 | $0.025 | $22 |
| **Jev** | $0.0001 | $0.0013 | $1 |

