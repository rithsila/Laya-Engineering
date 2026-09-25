"""JEV Engineering: Codex/LLM Writes -> Laya Decides -> Code Acts."""

import time
from agent import decide, choice_question, score_question, noul_question, get_agent


def codex_draft_reply(ticket: str) -> str:
    """Codex (System 2) writes the complex email response."""
    return "Refund of $50 issued to original card."


def run_jev_engineering_loop(ticket: str):
    """The 3-stage JEV Engineering pattern."""
    print("=" * 65)
    print(f"1. INCOMING TICKET: \"{ticket}\"")
    print("=" * 65)

    # STAGE 1: Codex (LLM) WRITES
    print("\n[Stage 1: LLM Writes] Codex drafting response...")
    t0 = time.perf_counter()
    draft = codex_draft_reply(ticket)
    print(f"  Draft: \"{draft}\"")

    # STAGE 2: Laya / JEV DECIDES (Fast typed decisions in ~25 ms)
    print("\n[Stage 2: JEV/Laya Decides] Evaluating draft on Neural Engine...")
    eval_questions = {
        "is_safe": noul_question(
            instructions="Is this response professional and safe?",
        ),
        "tone": score_question(
            instructions="Rate helpfulness.",
            criteria=["poor", "good"],
        ),
        "next_action": choice_question(
            instructions="What action next?",
            criteria={
                "auto_send": "Send email now.",
                "review": "Hold for review.",
            },
        ),
    }

    t1 = time.perf_counter()
    state = f"Ticket: {ticket}\nDraft: {draft}"
    res = decide(state, eval_questions)
    jev_ms = (time.perf_counter() - t1) * 1000

    is_safe = res["is_safe"]
    tone = res["tone"]
    action = res["next_action"]
    confidence = res.answers["next_action"]["confidence"]

    print(f"  Decision Time : {jev_ms:.2f} ms ($0 cost)")
    print(f"  Is Safe       : {'YES' if is_safe else 'NO'}")
    print(f"  Tone Score    : {tone:.2f} / 1.00")
    print(f"  Next Action   : {action.upper()} (Confidence: {confidence:.1%})")

    # STAGE 3: CODE ACTS (Deterministic Python rule)
    print("\n[Stage 3: Code Acts] Executing deterministic control flow...")
    if is_safe and action == "auto_send":
        print("  -> ACTION TAKEN: Email sent to customer! (Zero human delay)")
    else:
        print("  -> ACTION TAKEN: Sent to human manager queue for review.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    print("\nWarmup: Loading Apple Neural Engine...")
    get_agent()
    print("Ready.\n")

    # Test Ticket
    run_jev_engineering_loop("Charged twice for invoice 1042. Please refund.")
