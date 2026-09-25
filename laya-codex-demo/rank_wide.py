"""JEV Step 8: Rank Wide, Read Narrow.

1. Rank Wide: Fast local Laya ($0, 25ms) scores a batch of incoming tickets.
2. Queue & Filter: Deterministic Python sorts into priority queue.
3. Read Narrow: Only top high-urgency items consume expensive Codex/Cloud tokens.
"""

import time
import os
import sys

# Ensure current folder is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import decide, choice_question, score_question, noul_question
from hybrid import triage_hybrid

QUESTIONS = {
    "urgency": score_question("Rate urgency of this customer issue", ["low", "medium", "high"]),
    "escalate": noul_question("Does this require immediate human manager attention?"),
}

TICKETS = [
    {"id": "TCK-101", "text": "Can I update the billing email on our monthly invoice?"},
    {"id": "TCK-102", "text": "Newsletter unsubscribe link didn't work for my teammate."},
    {"id": "TCK-103", "text": "EMERGENCY: Production payment gateway down, all checkouts failing with 500!"},
    {"id": "TCK-104", "text": "Where can I find the API documentation for webhook signatures?"},
    {"id": "TCK-105", "text": "We are getting legal counsel involved if our data is not exported today."},
    {"id": "TCK-106", "text": "Feature request: Can you add dark mode to the dashboard settings?"},
]


def rank_wide(tickets):
    """Stage 1: Fast local scoring of all tickets on Apple Neural Engine."""
    print("=" * 68)
    print("STAGE 1: RANK WIDE (Local Laya on Apple Neural Engine - $0.00)")
    print("=" * 68)
    ranked = []

    for item in tickets:
        t0 = time.perf_counter()
        res = decide(item["text"], QUESTIONS)
        ms = (time.perf_counter() - t0) * 1000

        item_scored = {
            "id": item["id"],
            "text": item["text"],
            "urgency": round(res["urgency"], 3),
            "escalate": res["escalate"],
            "ms": round(ms, 1),
        }
        ranked.append(item_scored)
        print(f"[{item['id']}] Urgency: {item_scored['urgency']:<5} | Escalate: {str(item_scored['escalate']):<5} | {ms:.1f}ms | {item['text'][:45]}...")

    # Stage 2: Sort by urgency descending
    ranked.sort(key=lambda x: (x["escalate"], x["urgency"]), reverse=True)
    return ranked


def read_narrow(ranked_tickets, top_k=2):
    """Stage 2: Spend LLM / Cloud compute only on top-k priority items."""
    print("\n" + "=" * 68)
    print(f"STAGE 2: READ NARROW (Send only top {top_k} items to Cloud / Codex)")
    print("=" * 68)

    top_items = ranked_tickets[:top_k]
    routine_items = ranked_tickets[top_k:]

    for item in top_items:
        print(f"\n>> ESCALATING HIGH-PRIORITY [{item['id']}] to Cloud / Codex:")
        print(f"   Text: \"{item['text']}\"")
        res = triage_hybrid(item["text"])
        print(f"   Handled by: {res['handled_by']} ({res['latency_ms']} ms)")
        print(f"   Decision  : Dept={res['department']}, Urgency={res['urgency']}, Escalate={res['escalate']}")

    print("\n" + "=" * 68)
    print(f"STAGE 3: CODE ACTS (Auto-resolve remaining {len(routine_items)} routine tickets)")
    print("=" * 68)
    for item in routine_items:
        print(f"   [Auto-Queued] {item['id']}: Routed to standard queue (Urgency: {item['urgency']}) - $0 cost")


def main():
    print(f"Incoming batch of {len(TICKETS)} tickets received.")
    t_start = time.perf_counter()
    ranked = rank_wide(TICKETS)
    read_narrow(ranked, top_k=2)
    total_s = time.perf_counter() - t_start
    print(f"\nDone! Batch processed in {total_s:.2f}s total.")
    print("Tokens saved: 66% (4 of 6 tickets never touched an expensive LLM).")


if __name__ == "__main__":
    main()
