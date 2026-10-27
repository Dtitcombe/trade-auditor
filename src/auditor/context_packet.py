"""The Context Packet — the Meterless pattern, recreated in Python.

Meterless publishes four engines as prompt-based specs + a packet
structure, no SDK: H-MEM (hierarchical memory, provenance, trust
ledger), World Model (event-sourced entity/context graph), Markovian
(long runs in bounded chunks), Scout Intent (a signed execution
contract; spec only) — "recreate the pattern in whatever language
you're building in" (github.com/Meterless/Meterless). This module is
that recreation for the Trade Auditor; see docs/meterless.md for the
full component-to-engine mapping. Planner / Executor / Evaluator are
roles working one packet in sequence, not a Meterless engine.

Every audit travels as ONE packet. The Planner assembles it; the
Executor reasons over it; the Evaluator verifies against it. Nothing
reaches a step except through the packet — that discipline is what
makes every claim in the verdict traceable to a cited journal field.

Packet shape (after Meterless's published Context Packet example):
    agent_id     who is acting
    task         the one question + the trade under audit
    world_state  the day's declared frame and the day's running state
    memory       the raw journal row + the day's other trades
    intent       what the agent must do — and must never do
    output       the verdict contract the steps must fill
"""

PACKET_VERSION = "1.0"


def build_packet(trade, frame, day_trades):
    """Assemble the context packet for one trade's audit.

    World Model pattern: the declared frame (risk cap, lockout) plus the
    day's running state (trades so far, P&L so far, lockout room left).
    H-MEM pattern: the raw journal row and the day's full history — the
    only evidence any step is allowed to cite.
    """
    idx = day_trades.index(trade)
    pnl_before = sum(t["pnl_usd"] for t in day_trades[:idx])
    return {
        "packet_version": PACKET_VERSION,
        "agent_id": "trade-auditor",
        "task": {
            "question": "Why did this trade pass or fail my system?",
            "trade_id": f"{trade['date']} {trade['time_et']} "
                        f"{trade['instrument']} {trade['model']}",
        },
        "world_state": {
            "frame": frame,
            "trades_today": len(day_trades),
            "pnl_before_usd": pnl_before,
            "lockout_room_usd": frame["daily_lockout_usd"] + pnl_before
            if pnl_before < 0 else frame["daily_lockout_usd"],
        },
        "memory": {
            "journal_row": trade,
            "day_history": day_trades,
        },
        "intent": {
            "answer": "Answer the task question only, per trade.",
            "cite": "Every factual claim cites the journal field it "
                    "rests on; an unverifiable claim voids the verdict.",
            "never": ["grade the P&L", "predict price",
                      "issue a trade signal"],
        },
        "output": {
            "format": ["verdict (PASS/FAIL)", "reasons (failed rules)",
                       "notes (cautions)", "fix (one, if failed)"],
            "grade": "process only — never the outcome",
        },
    }
