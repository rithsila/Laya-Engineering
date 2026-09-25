"""Benchmark test: Evaluate Laya + JEV cooperation and performance."""

import time
from hybrid import triage_hybrid
from agent import get_agent

TEST_CASES = [
    {
        "type": "Clear Billing",
        "ticket": "Please refund the duplicate charge on my credit card.",
    },
    {
        "type": "Clear Technical",
        "ticket": "I forgot my password and the reset link is not working.",
    },
    {
        "type": "Clear Sales",
        "ticket": "We want to purchase 50 enterprise seats for our team.",
    },
    {
        "type": "Ambiguous / Greeting",
        "ticket": "hi, are you there?",
    },
    {
        "type": "Angry / Manager Request",
        "ticket": "I will sue your company, let me speak to your manager right now!",
    },
]


def run_benchmark():
    print("\nWarmup: Loading Apple Neural Engine model...")
    get_agent()
    print("Model ready. Running Cooperation Benchmark (5 test cases)...\n")

    results = []
    laya_count = 0
    jev_count = 0
    laya_times = []
    jev_times = []

    print(f"{'Test Case':<25} | {'Handled By':<12} | {'Time':<10} | {'Dept':<10} | {'Escalated'}")
    print("-" * 75)

    for case in TEST_CASES:
        t_start = time.perf_counter()
        res = triage_hybrid(case["ticket"])
        t_total = (time.perf_counter() - t_start) * 1000

        is_jev = res["escalated"]
        handler = "JEV Cloud" if is_jev else "Laya Local"
        dept = str(res["department"]).upper()

        if is_jev:
            jev_count += 1
            jev_times.append(res["latency_ms"])
        else:
            laya_count += 1
            laya_times.append(res["latency_ms"])

        results.append(res)
        time_str = f"{res['latency_ms']:.1f} ms"
        print(f"{case['type']:<25} | {handler:<12} | {time_str:<10} | {dept:<10} | {str(is_jev)}")

    avg_laya = sum(laya_times) / len(laya_times) if laya_times else 0
    avg_jev = sum(jev_times) / len(jev_times) if jev_times else 0

    print("=" * 75)
    print("COOPERATION BENCHMARK REPORT")
    print(f"1. Routine Tickets (Laya)  : {laya_count}/{len(TEST_CASES)} handled locally (Avg: {avg_laya:.1f} ms, Cost: $0.00)")
    print(f"2. Hard Tickets (JEV Cloud): {jev_count}/{len(TEST_CASES)} escalated to Cloud (Avg: {avg_jev:.1f} ms)")
    print(f"3. Cloud Token Savings     : {laya_count/len(TEST_CASES):.0%} saved! Only {jev_count/len(TEST_CASES):.0%} needed expensive cloud API.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_benchmark()
