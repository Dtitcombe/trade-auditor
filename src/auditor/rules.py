"""The trader's system, as ruled in advance (Oct 17, 2026 sit-down).

The auditor grades PROCESS against these rules only. It never grades P&L,
never predicts price, and never issues trade signals. Rules are data here,
not opinions: change the ruling, change the file, the audit follows.
"""

RULES = {
    "risk_cap_usd": 250,          # no single trade risks more than this
    "daily_lockout_default_usd": 350,  # declared week to week; -350 day = done
    "models": ["S&D", "Breakout", "Fib"],  # a trade with no model named = baseless
    "doyle_live_exception": True,  # trades taken live with the mentor are declared at review, never drift
    "gold_breakout_gate": {
        # Gold breakouts ONLY when the 13 EMA crosses the 50 EMA in the
        # direction of the trade WITH higher-timeframe alignment.
        "requires": ["ema_cross_in_direction", "htf_aligned"],
    },
    "grading_count": {
        # Doyle grading (Oct 16 webinar): count the averages.
        "best_breakout_min_aligned": 3,   # >=3 of 4 EMAs in your direction
        "top_grade": "zero averages in the way",
        "ema800_in_middle": "downgrade: non-trending caution day",
    },
    "ema800": {
        # One job only: HTF anchor/veto, read on the 5-minute (= 200 on 15m).
        "states": ["with", "against", "middle"],
    },
    "news": {
        "red": "never traded",
        "orange": "normal size; extra care around PMI releases",
    },
    "sequence": {
        "add_to_winner": "half size only",
        "second_trade_after_loss": "same size or cut, never more; never more than the day's remaining lockout room; always optional",
    },
    "break_even": {
        "routine": "stop to break-even at 1R",
        "early_triggers": [
            "long consolidation",
            "red-folder news too close",
            "price breaks the 13 & 50 against the trade on the 1-minute",
            "zone against the trade / liquidity grab against the position at a swing",
        ],
    },
    "psych": {
        "make_back_exit": "never set an exit target to win back a previous loss",
    },
}
