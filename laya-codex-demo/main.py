"""Support ticket triage demo using Laya-MLX typed decisions."""

import argparse
import time
from agent import decide, get_agent, choice_question, score_question, noul_question

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

SAMPLE_TICKETS = [
    {
        "title": "Duplicate Charge",
        "text": "I got billed twice for my subscription this month. Please refund the duplicate $50 payment.",
    },
    {
        "title": "Production Server Crash",
        "text": "CRITICAL: The production database is completely down. All client APIs are returning HTTP 500.",
    },
    {
        "title": "Enterprise Plan Quote",
        "text": "Hello, our team has 80 developers and we want to purchase the annual enterprise tier. Can you share pricing?",
    },
]


def triage_ticket(ticket_text: str):
    """Run typed decisions on a ticket."""
    start_time = time.perf_counter()
    res = decide(ticket_text, QUESTIONS)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    dept = res["department"]
    urgency = res["urgency"]
    escalate = res["escalate"]
    
    dept_prob = res["answers"]["department"]["probabilities"].get(dept, 0.0)
    urg_prob = res["answers"]["urgency"]["probabilities"]
    esc_prob = res["answers"]["escalate"]["noul"]

    print("=" * 60)
    print(f"Ticket: {ticket_text}")
    print("-" * 60)
    print(f"Decision Time : {elapsed_ms:.2f} ms (Apple Silicon MLX)")
    print(f"Department    : {dept.upper()} (prob: {dept_prob:.2%})")
    print(f"Urgency Score : {urgency:.2f} / 2.00 (probs: low={urg_prob.get('0',0):.2f}, med={urg_prob.get('1',0):.2f}, high={urg_prob.get('2',0):.2f})")
    print(f"Escalate      : {'YES' if escalate else 'NO'} (escalation prob: {esc_prob:.2%})")
    print(f"Tokens Used   : {res['usage'].get('input_tokens', 0)} in, 0 out (Zero token drift)")
    print("=" * 60 + "\n")


def interactive_loop():
    """Keep model loaded in memory so every decision takes only ~20-30 ms."""
    print("Interactive Mode Active! Model stays loaded in MLX.")
    print("Type your ticket and press Enter (or type 'exit' to quit):\n")
    while True:
        try:
            line = input("Ticket > ").strip()
            if not line:
                continue
            if line.lower() in ("exit", "quit", "q"):
                print("Exiting.")
                break
            triage_ticket(line)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


def main():
    parser = argparse.ArgumentParser(description="Laya MLX Ticket Triage Demo")
    parser.add_argument("--ticket", type=str, help="Custom ticket text to evaluate")
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Keep model in memory for instant decisions"
    )
    args = parser.parse_args()

    print("\nWarmup / Loading Laya MLX Agent into Apple Silicon MLX...")
    t0 = time.perf_counter()
    get_agent()
    load_ms = (time.perf_counter() - t0) * 1000
    print(f"Model loaded into MLX in {load_ms:.0f} ms.\n")

    if args.ticket:
        triage_ticket(args.ticket)
    elif args.interactive:
        interactive_loop()
    else:
        for sample in SAMPLE_TICKETS:
            print(f"--- Running Demo: {sample['title']} ---")
            triage_ticket(sample["text"])
        interactive_loop()


if __name__ == "__main__":
    main()
