"""The auditor: Planner -> Executor -> Evaluator.

Built on Meterless's published engine patterns, recreated in Python,
as their docs direct (github.com/Meterless/Meterless: prompt-based
engine specs + a Context Packet structure, no SDK). Each audit travels
as one Context Packet (see context_packet.py); nothing reaches a step
except through it. Mapping: World Model -> day frame + running state;
H-MEM -> journal row + day history, every claim cited and verified
(provenance); Markovian -> one bounded audit unit per trade; Scout
Intent -> the one question + guardrails as the Planner's contract.
Planner / Executor / Evaluator are roles working one packet in
sequence — not a Meterless engine (swarm-orchestration is a future
engine, not a current one).

    Planner   (World Model + Scout Intent) — assembles the packet: the
              day's declared frame, the day's running state, the one
              question and its guardrails.
    Executor  (Markovian discipline) — evaluates each applicable rule
              against the packet's memory in one bounded unit, attaching
              cited field values as evidence.
    Evaluator (H-MEM) — verifies every citation against the raw
              journal row in the packet (provenance), grades the process
              (never the P&L), writes the one fix.
"""

import re

from . import context_packet, data_pipe
from .rules import RULES

MAKE_BACK_PHRASES = ["make the first loss back", "make it back", "win back",
                     "sized up"]


# ---------------------------------------------------------------- helpers

def _cite(field, value):
    return {"field": field, "value": value}


def _finding(rule, status, detail, citations):
    """status: 'pass' | 'fail' | 'note'. A single 'fail' fails the trade."""
    return {"rule": rule, "status": status, "detail": detail,
            "citations": citations}


def _note_phrase(trade, phrases):
    """Return the first phrase from `phrases` found in the journal notes
    (case-insensitive), or None. Note evidence is cited, never assumed."""
    notes = trade["notes"].lower()
    for p in phrases:
        if p.lower() in notes:
            return p
    return None


# ---------------------------------------------------------------- planner

def plan(packet):
    """Planner (World State + Intent): from the packet, return the list
    of rule keys that apply to this trade."""
    trade = packet["memory"]["journal_row"]
    day_trades = packet["memory"]["day_history"]
    applicable = ["risk_cap_usd", "models", "news", "ema800", "break_even"]
    if trade["model"] == "Breakout":
        applicable.append("grading_count")
    if trade["instrument"] == "GOLD" and trade["model"] == "Breakout":
        applicable.append("gold_breakout_gate")
    if len(day_trades) > 1 or _note_phrase(trade, ["added"]):
        applicable.append("sequence")
    return applicable


# ---------------------------------------------------------------- executor

def _eval_risk_cap(trade, frame, day):
    cap = frame["risk_cap_usd"]
    ok = trade["risk_usd"] <= cap
    return _finding(
        "risk_cap_usd", "pass" if ok else "fail",
        f"Risk ${trade['risk_usd']:.0f} vs the ${cap:.0f} per-trade cap.",
        [_cite("risk_usd", trade["risk_usd"])])


def _eval_model_named(trade, frame, day):
    named = trade["model"] in RULES["models"]
    return _finding(
        "models", "pass" if named else "fail",
        f"Model named before entry: {trade['model']}."
        if named else "No model named — a baseless trade.",
        [_cite("model", trade["model"])])


def _eval_news(trade, frame, day):
    news = trade["news"]
    if news == "red":
        return _finding(
            "news", "fail",
            "Red-folder news — never traded, whatever the setup looks like.",
            [_cite("news", "red")])
    if news == "orange":
        return _finding(
            "news", "note",
            "Orange folder: traded at normal size, as ruled; extra care "
            "applies around PMI releases.",
            [_cite("news", "orange")])
    return _finding("news", "pass", "No news conflict.",
                    [_cite("news", trade["news"])])


def _eval_ema800(trade, frame, day):
    state = trade["ema800"]
    if state == "with":
        return _finding("ema800", "pass",
                        "800 with the trade — the tide is at its back.",
                        [_cite("ema800", "with")])
    if state == "middle":
        return _finding(
            "ema800", "note",
            "800 flat / in the middle: non-trending caution day — targets "
            "shrink to the nearest liquidity, S&D degrades, size light.",
            [_cite("ema800", "middle")])
    # against
    if trade["model"] == "Breakout":
        return _finding(
            "ema800", "fail",
            "800 against a breakout: an average in the way before the "
            "trade even starts.",
            [_cite("ema800", "against")])
    return _finding(
        "ema800", "note",
        "800 against the trade — downgrade; the anchor is not at its back.",
        [_cite("ema800", "against")])


def _eval_gold_gate(trade, frame, day):
    if trade["htf"] != "yes":
        return _finding(
            "gold_breakout_gate", "fail",
            "Gold breakout without HTF alignment — the gate is explicit: "
            "13 crosses 50 in direction WITH HTF, or it is not a gold "
            "breakout. This is the leak pattern.",
            [_cite("htf", trade["htf"])])
    phrase = _note_phrase(trade, ["cross"])
    if phrase:
        return _finding(
            "gold_breakout_gate", "pass",
            "Gate satisfied: HTF aligned and the 13/50 cross in direction "
            "is documented in the journal.",
            [_cite("htf", "yes"), _cite("notes", phrase)])
    return _finding(
        "gold_breakout_gate", "note",
        "HTF aligned, but no 13/50 cross documented in the journal — "
        "the gate cannot be verified from the entry.",
        [_cite("htf", "yes")])


def _eval_grading_count(trade, frame, day):
    m = re.search(r"(\d)\s*of\s*4", trade["notes"])
    if not m:
        return _finding(
            "grading_count", "note",
            "EMA alignment count not documented in the journal.",
            [])
    n = int(m.group(1))
    need = RULES["grading_count"]["best_breakout_min_aligned"]
    if n >= need:
        return _finding(
            "grading_count", "pass",
            f"Grading count {n} of 4 averages in direction — a quality "
            f"breakout shape.",
            [_cite("notes", m.group(0))])
    return _finding(
        "grading_count", "fail",
        f"Grading count only {n} of 4 averages in direction — below the "
        f"{need}-of-4 quality bar for a breakout.",
        [_cite("notes", m.group(0))])


def _eval_sequence(trade, frame, day):
    """Day-aware: `day` is the day's trades in time order."""
    idx = day.index(trade)
    notes_hit = _note_phrase(trade, ["added"])
    if notes_hit and _note_phrase(trade, ["half size"]):
        return _finding(
            "sequence", "pass",
            "Added to a winner at half size only — the sequence rule, "
            "followed exactly.",
            [_cite("notes", "half size")])
    if idx == 0:
        return _finding("sequence", "note",
                        "First trade of the day — no sequence context.", [])
    prior = day[:idx]
    pnl_before = sum(t["pnl_usd"] for t in prior)
    findings = []
    if pnl_before < 0:
        room = frame["daily_lockout_usd"] + pnl_before  # pnl_before is negative
        # STRICT ROOM RULE, ruled by the trader at the Sat Oct 24 weekly
        # check ("I shouldn't be over leveraging at all"): a second
        # trade that risks more than the day's remaining lockout room
        # FAILS, cut size or not. The only exception is changing the
        # declared ceiling itself. (Test-set trade #10 is the case:
        # $160 risked with $110 room left.)
        if trade["risk_usd"] > room:
            findings.append(_finding(
                "sequence", "fail",
                f"Risked ${trade['risk_usd']:.0f} with only ${room:.0f} of "
                f"lockout room left after ${-pnl_before:.0f} of losses — "
                f"the second trade never risks more than the day has "
                f"left.",
                [_cite("risk_usd", trade["risk_usd"])]))
        prev = prior[-1]
        if prev["result"] == "loss" and trade["risk_usd"] > prev["risk_usd"]:
            findings.append(_finding(
                "sequence", "fail",
                "Sized UP after a loss — the rule is same size or cut, "
                "never more.",
                [_cite("risk_usd", trade["risk_usd"])]))
        phrase = _note_phrase(trade, MAKE_BACK_PHRASES)
        if phrase:
            findings.append(_finding(
                "sequence", "fail",
                "Make-back sizing: the journal itself says the size was "
                "set to win back the earlier loss. Sizing comes from the "
                "setup, never from the last trade.",
                [_cite("notes", phrase)]))
    if findings:
        return findings[0] if len(findings) == 1 else {
            "rule": "sequence", "status": "fail",
            "detail": " ".join(f["detail"] for f in findings),
            "citations": [c for f in findings for c in f["citations"]]}
    return _finding("sequence", "note",
                    "Sequence within the rules for this day.", [])


def _eval_break_even(trade, frame, day):
    phrase = _note_phrase(trade, ["BE at 1R"])
    if phrase:
        return _finding("break_even", "pass",
                        "Stop moved to break-even at 1R — the routine step.",
                        [_cite("notes", phrase)])
    phrase = _note_phrase(trade, ["BE early"])
    if phrase:
        trigger = _note_phrase(trade, RULES["break_even"]["early_triggers"])
        detail = "Early break-even, justified"
        if trigger:
            detail += f" by a named trigger ({trigger})"
        detail += " — the defensive rule working as written."
        cites = [_cite("notes", phrase)]
        if trigger:
            cites.append(_cite("notes", trigger))
        return _finding("break_even", "pass", detail, cites)
    if trade["result"] == "loss":
        return _finding(
            "break_even", "note",
            "Stopped out; no break-even evidence in the journal — the "
            "trade is failed or passed on its other rules.", [])
    return _finding("break_even", "note",
                    "No break-even evidence in the journal.", [])


_EVALUATORS = {
    "risk_cap_usd": _eval_risk_cap,
    "models": _eval_model_named,
    "news": _eval_news,
    "ema800": _eval_ema800,
    "gold_breakout_gate": _eval_gold_gate,
    "grading_count": _eval_grading_count,
    "sequence": _eval_sequence,
    "break_even": _eval_break_even,
}


def execute(packet, applicable):
    """Executor (Reasoning): evaluate each applicable rule against the
    packet's memory; return findings with citations."""
    trade = packet["memory"]["journal_row"]
    frame = packet["world_state"]["frame"]
    day_trades = packet["memory"]["day_history"]
    return [_EVALUATORS[key](trade, frame, day_trades) for key in applicable]


# ---------------------------------------------------------------- evaluator

FIX_BY_RULE = {
    "gold_breakout_gate": "No gold breakout without HTF alignment — "
                          "gold's home model is S&D.",
    "news": "Red folder = never traded, whatever the setup looks like.",
    "sequence": "After a loss, trade #2 risks same-or-cut and never more "
                "than the day's remaining lockout room.",
    "ema800": "The 800 against you is an average in the way — downgrade "
              "the setup or pass on it.",
    "grading_count": "Breakouts need at least 3 of 4 averages in your "
                     "direction. Fewer is not a trade.",
    "risk_cap_usd": "Size to the $250 cap before entry, not after.",
    "models": "Name the model before entry — or there is no trade.",
}


def _verify_citation(trade, citation):
    field, value = citation["field"], citation["value"]
    if field not in trade:
        return False
    actual = trade[field]
    if isinstance(actual, (int, float)) and isinstance(value, (int, float)):
        return float(actual) == float(value)
    if field == "notes":
        return str(value).lower() in str(actual).lower()
    return str(actual) == str(value)


def evaluate(packet, findings):
    """Evaluator (Memory): verify citations against the packet's raw
    journal row, grade process, write the one fix.
    An unverified citation VOIDS the verdict — the agent does not get to
    claim what the journal doesn't support."""
    trade = packet["memory"]["journal_row"]
    for f in findings:
        for c in f["citations"]:
            if not _verify_citation(trade, c):
                return {"date": trade["date"], "time_et": trade["time_et"],
                        "instrument": trade["instrument"],
                        "model": trade["model"], "dir": trade["dir"],
                        "verdict": "VOID",
                        "trader_grade": trade["grade"],
                        "reasons": [f"Citation failed verification: "
                                    f"{c['field']} = {c['value']!r}"],
                        "notes": [], "fix": "Fix the citation, not the trade."}
    fails = [f for f in findings if f["status"] == "fail"]
    notes = [f["detail"] for f in findings if f["status"] == "note"]
    verdict = "FAIL" if fails else "PASS"
    fix = FIX_BY_RULE.get(fails[0]["rule"]) if fails else None
    return {"date": trade["date"], "time_et": trade["time_et"],
            "instrument": trade["instrument"], "model": trade["model"],
            "dir": trade["dir"], "verdict": verdict,
            "trader_grade": trade["grade"],
            "reasons": [f["detail"] for f in fails],
            "notes": notes, "fix": fix,
            "context": {"packet_version": packet["packet_version"],
                        "trades_today": packet["world_state"]["trades_today"],
                        "lockout_room_usd":
                            packet["world_state"]["lockout_room_usd"]}}


# ---------------------------------------------------------------- driver

def audit_trade(trade, frame, day_trades):
    packet = context_packet.build_packet(trade, frame, day_trades)
    steps = plan(packet)
    findings = execute(packet, steps)
    return evaluate(packet, findings)


def audit_csv(csv_path):
    trades = data_pipe.load_trades(csv_path)
    days = {}
    for t in trades:
        days.setdefault(t["date"], []).append(t)
    for day in days.values():
        day.sort(key=lambda t: t["time_et"])
    return [audit_trade(t, data_pipe.load_day_frame(t["date"]),
                        days[t["date"]]) for t in trades]
