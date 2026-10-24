"""Two-mode data pipe.

The agent NEVER reads journal files directly in production mode: every lookup
goes through Zetaris, the data harness — one governed SQL endpoint over the
journal (CSV) and the trader's notes, joined at query time.

Until the Zetaris instance is provisioned (organisers: access still TBC on
Oct 22), LOCAL mode implements the IDENTICAL contract against the CSV on
disk. Swapping modes = implementing `query_zetaris` when the endpoint lands;
no caller changes.

Contract: every function returns a list of dicts with the journal's per-trade
log fields: date, time_et, instrument, model, grade, dir, htf, ema800, news,
risk_usd, result, pnl_usd, notes.
"""

import csv
import os

MODE = os.environ.get("AUDITOR_DATA_MODE", "local")  # "local" | "zetaris"


def _load_local(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["risk_usd"] = float(r["risk_usd"])
        r["pnl_usd"] = float(r["pnl_usd"])
    return rows


def query_zetaris(sql):
    """TODO (Zetaris swap-in): run `sql` against the Zetaris endpoint over the
    federated journal + notes views and return rows in the contract shape.
    Connection details arrive with instance provisioning."""
    raise NotImplementedError("Zetaris instance not yet provisioned")


def load_trades(csv_path=None):
    if MODE == "zetaris":
        return query_zetaris("SELECT * FROM journal.trades ORDER BY date, time_et")
    return _load_local(csv_path)


def load_day_frame(date):
    """The day's declared frame: risk cap, lockout, news calendar.
    Zetaris mode joins this from the notes source; local mode returns the
    ruled defaults from rules.py."""
    from .rules import RULES
    return {
        "date": date,
        "risk_cap_usd": RULES["risk_cap_usd"],
        "daily_lockout_usd": RULES["daily_lockout_default_usd"],
    }
