"""Entry point: audit the frozen test set.

    python run_audit.py [path/to/trades.csv]

Night 1: loads the pipe and lists the trades it will audit.
Night 2: full Planner -> Executor -> Evaluator verdicts.
"""

import sys

sys.path.insert(0, "src")

from auditor import agent  # noqa: E402


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/trades_sample.csv"
    results = agent.audit_csv(csv_path)
    print(f"Audited {len(results)} trades from {csv_path}\n")
    for i, r in enumerate(results, 1):
        print(f"#{i}  {r['date']} {r['time_et']}  {r['instrument']} "
              f"{r['model']} {r['dir']}  ->  {r['verdict']}")
        for reason in r["reasons"]:
            print(f"      FAIL: {reason}")
        for note in r["notes"]:
            print(f"      note: {note}")
        if r["fix"]:
            print(f"      FIX: {r['fix']}")
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    print(f"\nScore: {passed} PASS / {len(results) - passed} FAIL")


if __name__ == "__main__":
    main()
