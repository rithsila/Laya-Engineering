"""Hybrid Decision Pipeline: Local Laya (System 1) + JEV Cloud API (System 2)."""

import argparse
import os
import time
from typing import Any, Dict, Optional

from agent import decide, choice_question, score_question, noul_question, get_agent
from jev_client import decide_jev, get_jev_api_key

QUESTIONS = {
    "department": choice_question(
        instructions="Which department should handle this ticket?",
        criteria={
            "billing": "Invoices, credit cards, duplicate charges, refunds.",
            "technical": "Software bugs, server downtime, error codes, crashes.",
            "sales": "Upgrades, pricing plans, enterprise licenses, purchases.",
        },
    ),
    "urgency": score_question(
        instructions="How urgent is this ticket?",
        criteria=["low", "medium", "high"],
    ),
    "escalate": noul_question(
        instructions="Should this ticket immediately escalate to a human manager?",
    ),
}


def triage_hybrid(
    ticket_text: str,
    confidence_threshold: float = 0.70,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Triage ticket with fast local Laya; escalate to JEV Cloud if complex, long, or flagged."""
    t0 = time.perf_counter()
    reasons = []
    jev_key = get_jev_api_key(api_key)

    try:
        local_res = decide(ticket_text, QUESTIONS)
        local_ms = (time.perf_counter() - t0) * 1000

        dept = local_res["department"]
        urgency = local_res["urgency"]
        escalate = local_res["escalate"]
        confidence = local_res.answers["department"].get("confidence", 1.0)

        # Escalation triggers
        if escalate:
            reasons.append("Flagged for human/manager review")
        if confidence < confidence_threshold:
            reasons.append(f"Low confidence ({confidence:.1%} < {confidence_threshold:.0%})")

        # If no escalation needed -> Return local fast path
        if not reasons:
            return {
                "handled_by": "Laya (Local Neural Engine)",
                "latency_ms": round(local_ms, 2),
                "cost": "$0.00",
                "department": dept,
                "urgency": urgency,
                "escalate": escalate,
                "confidence": confidence,
                "escalated": False,
                "details": local_res.answers,
            }

    except ValueError as e:
        # Token limit exceeded on local ANE (96 tokens) -> Escalate to JEV Cloud
        if "supports at most" in str(e) or "tokens" in str(e):
            reasons.append("Ticket exceeds 96-token local ANE limit (Routed to Cloud)")
        else:
            raise e

    # Escalation needed -> Call JEV Cloud API
    escalation_reason = " & ".join(reasons)

    if not jev_key or jev_key == "your_api_key_here":
        return {
            "handled_by": "Laya (Local, JEV key missing)",
            "latency_ms": 0.0,
            "cost": "$0.00",
            "department": "Unknown",
            "urgency": 1.0,
            "escalate": True,
            "confidence": 0.0,
            "escalated": True,
            "escalation_reason": escalation_reason,
            "warning": "JEV API key not found in .env.",
            "details": {},
        }

    t_jev = time.perf_counter()
    jev_res = decide_jev(ticket_text, QUESTIONS, api_key=jev_key)
    jev_ms = (time.perf_counter() - t_jev) * 1000

    return {
        "handled_by": "JEV Cloud API (System 2 Escalation)",
        "latency_ms": round(jev_ms, 2),
        "cost": "JEV API credits",
        "department": jev_res["values"].get("department"),
        "urgency": jev_res["values"].get("urgency"),
        "escalate": jev_res["values"].get("escalate"),
        "confidence": jev_res["answers"].get("department", {}).get("confidence", 1.0),
        "escalated": True,
        "escalation_reason": escalation_reason,
        "details": jev_res["answers"],
    }


def print_result(ticket: str, res: Dict[str, Any]):
    print("-" * 65)
    print(f"Ticket      : {ticket[:80]}...")
    print(f"Handled By  : {res['handled_by']}")
    print(f"Latency     : {res['latency_ms']} ms")
    print(f"Department  : {str(res['department']).upper()} (Confidence: {res['confidence']:.2%})")
    print(f"Urgency     : {res['urgency']}")
    print(f"Escalated   : {res['escalated']}")
    if res.get("escalation_reason"):
        print(f"Reason      : {res['escalation_reason']}")
    print("-" * 65 + "\n")


def interactive_mode(api_key: Optional[str] = None):
    print("Hybrid Interactive Mode Active.")
    print("Model loaded in Apple Neural Engine. JEV API connected.")
    print("Type a ticket and press Enter (or type 'exit' to quit):\n")
    while True:
        try:
            line = input("Ticket > ").strip()
            if not line:
                continue
            if line.lower() in ("exit", "quit", "q"):
                print("Exiting.")
                break
            res = triage_hybrid(line, api_key=api_key)
            print_result(line, res)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


def main():
    parser = argparse.ArgumentParser(description="Hybrid Laya + JEV Ticket Triage")
    parser.add_argument("--ticket", type=str, help="Ticket text to triage")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive terminal mode")
    parser.add_argument("--key", type=str, help="JEV / TypeSafe API Key")
    parser.add_argument("--threshold", type=float, default=0.70, help="Confidence threshold (default 0.70)")
    args = parser.parse_args()

    print("\nWarmup: Loading local Neural Engine model...")
    get_agent()
    print("Neural Engine model ready.")

    if args.ticket:
        res = triage_hybrid(args.ticket, confidence_threshold=args.threshold, api_key=args.key)
        print_result(args.ticket, res)
    elif args.interactive:
        interactive_mode(api_key=args.key)
    else:
        test_tickets = [
            "Please send me last month's invoice for my records.",
            "CRITICAL ALERT: Production database cluster crashed with 500 error!",
        ]
        for t in test_tickets:
            res = triage_hybrid(t, confidence_threshold=args.threshold, api_key=args.key)
            print_result(t, res)


if __name__ == "__main__":
    main()
